"""Real-time Socket Server (TCP) - nhận kết nối từ Desktop Client.

Server chạy chung event loop với FastAPI (khởi động trong lifespan) nên Admin có thể
Khởi động / Dừng / Đổi IP-Port (module 1.4) mà không cần tắt REST API.
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional

from server.core.config import settings
from server.socket_server.connection import TCPClientConnection
from server.socket_server.connection_manager import socket_manager
from server.socket_server.handshake import authenticate_connection
from server.socket_server.protocol import PacketType, ProtocolError, decode_packet, make_packet

logger = logging.getLogger("socket_server")


class TCPSocketServer:
    def __init__(self) -> None:
        self._server: Optional[asyncio.base_events.Server] = None
        self.host: Optional[str] = None
        self.port: Optional[int] = None
        self.started_at: Optional[datetime] = None
        self._lock = asyncio.Lock()

    @property
    def is_running(self) -> bool:
        return self._server is not None and self._server.is_serving()

    async def start(self, host: str, port: int) -> None:
        async with self._lock:
            if self.is_running:
                return
            self._server = await asyncio.start_server(
                self._handle_client, host, port, limit=settings.SOCKET_MAX_PACKET_SIZE
            )
            self.host, self.port, self.started_at = host, port, datetime.now()
            logger.info("Socket Server đang lắng nghe tại %s:%s", host, port)

    async def stop(self, message: str = "Máy chủ Socket đã dừng hoạt động") -> None:
        async with self._lock:
            if self._server is None:
                return
            server, self._server = self._server, None
            server.close()  # ngừng nhận kết nối mới
            await socket_manager.close_all(
                make_packet(PacketType.SERVER_SHUTDOWN, {"message": message}), transport="TCP"
            )
            try:
                await asyncio.wait_for(server.wait_closed(), timeout=5)
            except asyncio.TimeoutError:
                logger.warning("Hết thời gian chờ đóng các kết nối TCP")
            self.started_at = None
            logger.info("Socket Server đã dừng")

    def status(self) -> dict:
        return {
            "running": self.is_running,
            "host": self.host if self.is_running else None,
            "port": self.port if self.is_running else None,
            "started_at": self.started_at if self.is_running else None,
            "uptime_seconds": socket_manager.uptime_since(self.started_at) if self.is_running else 0,
        }

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = writer.get_extra_info("peername")
        address = f"{peer[0]}:{peer[1]}" if peer else "unknown"
        conn = TCPClientConnection(writer, address)
        socket_manager.add(conn)
        try:
            # --- Bắt tay xác thực: gói đầu tiên phải là 'auth' ---
            line = await asyncio.wait_for(reader.readline(), timeout=settings.SOCKET_AUTH_TIMEOUT)
            if not line:
                return
            conn.mark_received(len(line))
            try:
                packet = decode_packet(line)
            except ProtocolError as exc:
                await conn.send(make_packet(PacketType.AUTH_FAIL, {"message": str(exc), "code": "BAD_PACKET"}))
                return
            if not await authenticate_connection(conn, packet):
                return

            # --- Vòng lặp nhận gói tin ---
            while not conn.closed:
                line = await reader.readline()
                if not line:
                    break
                conn.mark_received(len(line))
                if not line.strip():
                    continue
                try:
                    packet = decode_packet(line)
                except ProtocolError as exc:
                    await conn.send(make_packet(PacketType.ERROR, {"message": str(exc), "code": "BAD_PACKET"}))
                    continue
                await socket_manager.dispatch(conn, packet)
        except asyncio.TimeoutError:
            await conn.send(make_packet(PacketType.AUTH_FAIL, {
                "message": "Hết thời gian chờ xác thực", "code": "AUTH_TIMEOUT"}))
        except ValueError:  # vượt quá giới hạn kích thước gói tin
            await conn.send(make_packet(PacketType.ERROR, {
                "message": "Gói tin vượt quá kích thước cho phép", "code": "PACKET_TOO_LARGE"}))
        except (ConnectionError, asyncio.IncompleteReadError, OSError):
            pass
        except asyncio.CancelledError:
            raise
        finally:
            await socket_manager.remove(conn)


tcp_server = TCPSocketServer()

