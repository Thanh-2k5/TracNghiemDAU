"""Lõi quản lý kết nối Real-time dùng chung toàn hệ thống.

- Lưu danh sách kết nối TCP / WebSocket đang mở, ánh xạ phiên đăng nhập <-> kết nối.
- Xử lý Heartbeat, phát hiện mất kết nối (timeout), tính băng thông thời gian thực.
- Định tuyến gói tin tới handler do các module khác đăng ký (register_handler).
- Cung cấp API an toàn đa luồng (force_logout_sessions...) để tầng REST gọi sang.
"""
import asyncio
import inspect
import logging
import time
from datetime import datetime
from typing import Any, Awaitable, Callable, Optional, Union

from server.core.config import settings
from server.socket_server.connection import ClientConnection
from server.socket_server.protocol import PacketType, make_packet

logger = logging.getLogger("socket_server")

Handler = Callable[[ClientConnection, dict], Union[Awaitable[None], None]]
Listener = Callable[[ClientConnection], Union[Awaitable[None], None]]

MONITOR_INTERVAL = 2.0          # giây - chu kỳ tính băng thông & kiểm tra heartbeat
DB_TOUCH_INTERVAL = 30.0        # giây - chu kỳ cập nhật last_activity của phiên vào DB


class ConnectionManager:
    def __init__(self) -> None:
        self.connections: dict[str, ClientConnection] = {}
        self._session_index: dict[str, str] = {}
        self._handlers: dict[str, Handler] = {}
        self._listeners: dict[str, list[Listener]] = {"connect": [], "disconnect": []}
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.activity_callback: Optional[Callable[[str], None]] = None
        self._monitor_task: Optional[asyncio.Task] = None

    # ================= Đăng ký mở rộng cho các module khác =================
    def register_handler(self, ptype: str, handler: Optional[Handler] = None):
        """Đăng ký xử lý cho 1 loại gói tin. Dùng trực tiếp hoặc làm decorator."""
        def decorator(fn: Handler) -> Handler:
            self._handlers[ptype] = fn
            return fn
        return decorator(handler) if handler else decorator

    def add_listener(self, event: str, listener: Listener) -> None:
        """event = 'connect' (sau khi xác thực) | 'disconnect'."""
        self._listeners.setdefault(event, []).append(listener)

    async def _emit(self, event: str, conn: ClientConnection) -> None:
        for listener in self._listeners.get(event, []):
            try:
                result = listener(conn)
                if inspect.isawaitable(result):
                    await result
            except Exception:  # noqa: BLE001 - listener lỗi không được làm sập server
                logger.exception("Listener '%s' lỗi", event)

    # ================= Vòng đời kết nối =================
    def add(self, conn: ClientConnection) -> None:
        self.connections[conn.id] = conn
        logger.info("[%s] Kết nối mới %s từ %s", conn.transport, conn.id, conn.address)

    async def bind_session(self, conn: ClientConnection) -> None:
        """Gắn kết nối với phiên đăng nhập; đóng kết nối cũ nếu cùng phiên."""
        if not conn.session_id:
            return
        old_id = self._session_index.get(conn.session_id)
        if old_id and old_id != conn.id and old_id in self.connections:
            old = self.connections[old_id]
            await self.close_connection(
                old, make_packet(PacketType.KICKED, {"reason": "Phiên làm việc đã kết nối lại từ vị trí khác"})
            )
        self._session_index[conn.session_id] = conn.id
        await self._emit("connect", conn)

    async def remove(self, conn: ClientConnection) -> None:
        if self.connections.pop(conn.id, None) is None:
            await conn.close()
            return
        if conn.session_id and self._session_index.get(conn.session_id) == conn.id:
            self._session_index.pop(conn.session_id, None)
        await conn.close()
        logger.info("[%s] Đóng kết nối %s (%s)", conn.transport, conn.id, conn.username or conn.address)
        if conn.authenticated:
            await self._emit("disconnect", conn)

    async def close_connection(self, conn: ClientConnection, packet: Optional[dict] = None) -> None:
        if packet is not None:
            await conn.send(packet)
        await conn.close()

    # ================= Định tuyến gói tin =================
    async def dispatch(self, conn: ClientConnection, packet: dict) -> None:
        ptype = packet["type"]
        data = packet.get("data") or {}

        if ptype == PacketType.HEARTBEAT:
            await self._handle_heartbeat(conn, data)
            return
        if ptype == PacketType.LOGOUT:
            await self.close_connection(conn, make_packet(PacketType.NOTIFY, {"message": "Đã đóng kết nối"}))
            return

        handler = self._handlers.get(ptype)
        if handler is None:
            await conn.send(make_packet(PacketType.ERROR, {"message": f"Loại gói tin không hỗ trợ: {ptype}"},
                                        packet.get("id")))
            return
        try:
            result = handler(conn, packet)
            if inspect.isawaitable(result):
                await result
        except Exception as exc:  # noqa: BLE001
            logger.exception("Handler '%s' lỗi", ptype)
            await conn.send(make_packet(PacketType.ERROR, {"message": f"Lỗi xử lý gói tin: {exc}"}, packet.get("id")))

    async def _handle_heartbeat(self, conn: ClientConnection, data: dict) -> None:
        conn.mark_heartbeat(data.get("latency_ms"))
        await conn.send(make_packet(PacketType.HEARTBEAT_ACK, {
            "client_ts": data.get("client_ts"),
            "server_time": time.time(),
        }))
        now = time.monotonic()
        if conn.session_id and self.activity_callback and now - conn.last_db_touch >= DB_TOUCH_INTERVAL:
            conn.last_db_touch = now
            try:
                await asyncio.to_thread(self.activity_callback, conn.session_id)
            except Exception:  # noqa: BLE001
                logger.exception("Không cập nhật được hoạt động phiên %s", conn.session_id)

    # ================= Truy vấn =================
    def is_session_online(self, session_id: str) -> bool:
        conn_id = self._session_index.get(session_id)
        return bool(conn_id and conn_id in self.connections)

    def get_user_connections(self, user_id: int) -> list[ClientConnection]:
        return [c for c in list(self.connections.values()) if c.user_id == user_id]

    def snapshot(self) -> list[dict]:
        return [c.to_dict() for c in sorted(list(self.connections.values()), key=lambda c: c.connected_at)]

    def totals(self) -> dict[str, Any]:
        conns = list(self.connections.values())
        return {
            "connection_count": len(conns),
            "authenticated_count": sum(1 for c in conns if c.authenticated),
            "total_bytes_in": sum(c.bytes_in for c in conns),
            "total_bytes_out": sum(c.bytes_out for c in conns),
            "total_rate_in_bps": round(sum(c.rate_in for c in conns), 1),
            "total_rate_out_bps": round(sum(c.rate_out for c in conns), 1),
        }

    # ================= Gửi gói tin =================
    async def send_to_session(self, session_id: str, packet: dict) -> bool:
        conn_id = self._session_index.get(session_id)
        conn = self.connections.get(conn_id) if conn_id else None
        return await conn.send(packet) if conn else False

    async def send_to_user(self, user_id: int, packet: dict) -> int:
        sent = 0
        for conn in self.get_user_connections(user_id):
            sent += int(await conn.send(packet))
        return sent

    async def broadcast(self, packet: dict, role_code: Optional[str] = None) -> int:
        sent = 0
        for conn in list(self.connections.values()):
            if conn.authenticated and (role_code is None or conn.role_code == role_code):
                sent += int(await conn.send(packet))
        return sent

    async def kick(self, connection_id: str, reason: str) -> bool:
        conn = self.connections.get(connection_id)
        if not conn:
            return False
        await self.close_connection(conn, make_packet(PacketType.KICKED, {"reason": reason}))
        return True

    async def close_all(self, packet: Optional[dict] = None, transport: Optional[str] = None) -> None:
        targets = [c for c in list(self.connections.values()) if transport is None or c.transport == transport]
        await asyncio.gather(*(self.close_connection(c, packet) for c in targets), return_exceptions=True)

    # ================= API an toàn đa luồng cho tầng REST =================
    def run_threadsafe(self, coro: Awaitable) -> None:
        if self.loop is None or self.loop.is_closed():
            if inspect.iscoroutine(coro):
                coro.close()
            return
        try:
            running = asyncio.get_running_loop()
        except RuntimeError:
            running = None
        if running is self.loop:
            self.loop.create_task(coro)  # type: ignore[arg-type]
        else:
            asyncio.run_coroutine_threadsafe(coro, self.loop)  # type: ignore[arg-type]

    def force_logout_sessions(self, session_ids: list[str], reason: str) -> None:
        """Gửi force_logout rồi ngắt kết nối của các phiên (VD: bị đăng nhập nơi khác, bị khóa)."""
        if session_ids:
            self.run_threadsafe(self._close_sessions(session_ids, PacketType.FORCE_LOGOUT, reason))

    def close_sessions(self, session_ids: list[str]) -> None:
        """Đóng êm kết nối của các phiên (VD: người dùng chủ động đăng xuất)."""
        if session_ids:
            self.run_threadsafe(self._close_sessions(session_ids, PacketType.NOTIFY, "Đăng xuất thành công"))

    async def _close_sessions(self, session_ids: list[str], ptype: str, reason: str) -> None:
        for sid in session_ids:
            conn_id = self._session_index.get(sid)
            conn = self.connections.get(conn_id) if conn_id else None
            if conn:
                await self.close_connection(conn, make_packet(ptype, {"reason": reason, "message": reason}))

    # ================= Giám sát Heartbeat & băng thông =================
    def start_monitor(self) -> None:
        self.loop = asyncio.get_running_loop()
        if self._monitor_task is None or self._monitor_task.done():
            self._monitor_task = self.loop.create_task(self._monitor_loop())

    async def stop_monitor(self) -> None:
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

    async def _monitor_loop(self) -> None:
        while True:
            await asyncio.sleep(MONITOR_INTERVAL)
            now = time.monotonic()
            for conn in list(self.connections.values()):
                conn.update_rate(now)
                if conn.authenticated and now - conn.last_heartbeat > settings.HEARTBEAT_TIMEOUT:
                    logger.warning("Mất heartbeat: %s (%s) - ngắt kết nối", conn.id, conn.username)
                    await self.close_connection(conn, make_packet(PacketType.ERROR, {
                        "message": "Mất tín hiệu Heartbeat - kết nối bị đóng", "code": "HEARTBEAT_TIMEOUT"}))

    def uptime_since(self, started_at: Optional[datetime]) -> int:
        return int((datetime.now() - started_at).total_seconds()) if started_at else 0


socket_manager = ConnectionManager()

