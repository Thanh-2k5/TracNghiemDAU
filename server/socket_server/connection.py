"""Đối tượng kết nối Socket (TCP / WebSocket) + thống kê băng thông của từng kết nối."""
import asyncio
import time
import uuid
from datetime import datetime
from typing import Optional

from fastapi import WebSocket

from server.socket_server.protocol import encode_packet


class ClientConnection:
    transport = "BASE"

    def __init__(self, address: str):
        self.id: str = uuid.uuid4().hex[:12]
        self.address = address
        self.connected_at = datetime.now()
        self.last_heartbeat = time.monotonic()
        self.last_heartbeat_at = datetime.now()
        self.latency_ms: Optional[float] = None
        self.last_db_touch = 0.0

        # Thông tin xác thực (sau khi auth_ok)
        self.authenticated = False
        self.user_id: Optional[int] = None
        self.username: Optional[str] = None
        self.full_name: Optional[str] = None
        self.role_code: Optional[str] = None
        self.session_id: Optional[str] = None

        # Thống kê băng thông
        self.bytes_in = 0
        self.bytes_out = 0
        self.packets_in = 0
        self.packets_out = 0
        self.rate_in = 0.0
        self.rate_out = 0.0
        self._snap_in = 0
        self._snap_out = 0
        self._snap_time = time.monotonic()

        self.closed = False
        self._send_lock = asyncio.Lock()

    # ---------------- Thống kê ----------------
    def mark_received(self, nbytes: int) -> None:
        self.bytes_in += nbytes
        self.packets_in += 1

    def mark_heartbeat(self, latency_ms: Optional[float] = None) -> None:
        self.last_heartbeat = time.monotonic()
        self.last_heartbeat_at = datetime.now()
        if latency_ms is not None:
            self.latency_ms = round(float(latency_ms), 1)

    def update_rate(self, now: float) -> None:
        elapsed = now - self._snap_time
        if elapsed <= 0:
            return
        self.rate_in = (self.bytes_in - self._snap_in) / elapsed
        self.rate_out = (self.bytes_out - self._snap_out) / elapsed
        self._snap_in, self._snap_out, self._snap_time = self.bytes_in, self.bytes_out, now

    def seconds_since_heartbeat(self) -> float:
        return round(time.monotonic() - self.last_heartbeat, 1)

    def to_dict(self) -> dict:
        return {
            "connection_id": self.id,
            "transport": self.transport,
            "address": self.address,
            "user_id": self.user_id,
            "username": self.username,
            "full_name": self.full_name,
            "role_code": self.role_code,
            "authenticated": self.authenticated,
            "connected_at": self.connected_at,
            "last_heartbeat_at": self.last_heartbeat_at,
            "seconds_since_heartbeat": self.seconds_since_heartbeat(),
            "latency_ms": self.latency_ms,
            "bytes_in": self.bytes_in,
            "bytes_out": self.bytes_out,
            "packets_in": self.packets_in,
            "packets_out": self.packets_out,
            "rate_in_bps": round(self.rate_in, 1),
            "rate_out_bps": round(self.rate_out, 1),
        }

    # ---------------- Gửi / đóng ----------------
    async def send(self, packet: dict) -> bool:
        if self.closed:
            return False
        data = encode_packet(packet)
        try:
            async with self._send_lock:
                await self._write(data)
        except (ConnectionError, OSError, RuntimeError):
            await self.close()
            return False
        self.bytes_out += len(data)
        self.packets_out += 1
        return True

    async def _write(self, data: bytes) -> None:  # pragma: no cover - abstract
        raise NotImplementedError

    async def close(self) -> None:  # pragma: no cover - abstract
        raise NotImplementedError


class TCPClientConnection(ClientConnection):
    transport = "TCP"

    def __init__(self, writer: asyncio.StreamWriter, address: str):
        super().__init__(address)
        self.writer = writer

    async def _write(self, data: bytes) -> None:
        self.writer.write(data)
        await self.writer.drain()

    async def close(self) -> None:
        if self.closed:
            return
        self.closed = True
        try:
            self.writer.close()
            await asyncio.wait_for(self.writer.wait_closed(), timeout=3)
        except (ConnectionError, OSError, asyncio.TimeoutError):
            pass


class WebSocketClientConnection(ClientConnection):
    transport = "WS"

    def __init__(self, websocket: WebSocket, address: str):
        super().__init__(address)
        self.websocket = websocket

    async def _write(self, data: bytes) -> None:
        await self.websocket.send_text(data.decode("utf-8").rstrip("\n"))

    async def close(self) -> None:
        if self.closed:
            return
        self.closed = True
        try:
            await self.websocket.close()
        except (RuntimeError, ConnectionError, OSError):
            pass

