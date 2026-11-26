"""Router WebSocket - kênh real-time thay thế TCP (dùng cùng giao thức gói tin JSON)."""
import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from server.core.config import settings
from server.socket_server.connection import WebSocketClientConnection
from server.socket_server.connection_manager import socket_manager
from server.socket_server.handshake import authenticate_connection
from server.socket_server.protocol import PacketType, ProtocolError, decode_packet, make_packet

router = APIRouter(tags=["Real-time WebSocket"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    client = websocket.client
    conn = WebSocketClientConnection(websocket, f"{client.host}:{client.port}" if client else "unknown")
    socket_manager.add(conn)
    try:
        text = await asyncio.wait_for(websocket.receive_text(), timeout=settings.SOCKET_AUTH_TIMEOUT)
        conn.mark_received(len(text.encode("utf-8")))
        try:
            packet = decode_packet(text)
        except ProtocolError as exc:
            await conn.send(make_packet(PacketType.AUTH_FAIL, {"message": str(exc), "code": "BAD_PACKET"}))
            return
        if not await authenticate_connection(conn, packet):
            return
        while not conn.closed:
            text = await websocket.receive_text()
            conn.mark_received(len(text.encode("utf-8")))
            try:
                packet = decode_packet(text)
            except ProtocolError as exc:
                await conn.send(make_packet(PacketType.ERROR, {"message": str(exc), "code": "BAD_PACKET"}))
                continue
            await socket_manager.dispatch(conn, packet)
    except asyncio.TimeoutError:
        await conn.send(make_packet(PacketType.AUTH_FAIL, {"message": "Hết thời gian chờ xác thực",
                                                           "code": "AUTH_TIMEOUT"}))
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        await socket_manager.remove(conn)

