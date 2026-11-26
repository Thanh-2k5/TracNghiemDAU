"""Bắt tay xác thực dùng chung cho TCP và WebSocket."""
import asyncio
import time

from server.core.config import settings
from server.core.exceptions import AppError
from server.services import session_service
from server.socket_server.connection import ClientConnection
from server.socket_server.connection_manager import socket_manager
from server.socket_server.protocol import PacketType, make_packet


async def authenticate_connection(conn: ClientConnection, packet: dict) -> bool:
    if packet.get("type") != PacketType.AUTH:
        await conn.send(make_packet(PacketType.AUTH_FAIL, {
            "message": "Gói tin đầu tiên phải là 'auth'", "code": "AUTH_REQUIRED"}))
        return False

    token = (packet.get("data") or {}).get("token")
    try:
        info = await asyncio.to_thread(session_service.verify_socket_token, token, conn.id)
    except AppError as exc:
        await conn.send(make_packet(PacketType.AUTH_FAIL, {"message": exc.message, "code": exc.code}))
        return False

    conn.authenticated = True
    conn.session_id = info["session_id"]
    conn.user_id = info["user_id"]
    conn.username = info["username"]
    conn.full_name = info["full_name"]
    conn.role_code = info["role_code"]
    conn.mark_heartbeat()

    await conn.send(make_packet(PacketType.AUTH_OK, {
        "connection_id": conn.id,
        "server_time": time.time(),
        "heartbeat_interval": settings.HEARTBEAT_INTERVAL,
        "heartbeat_timeout": settings.HEARTBEAT_TIMEOUT,
        "user": {k: info[k] for k in ("user_id", "username", "full_name", "role_code")},
    }, packet.get("id")))
    await socket_manager.bind_session(conn)
    return True

