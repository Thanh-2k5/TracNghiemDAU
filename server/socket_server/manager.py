import json
from typing import Dict
from fastapi import WebSocket


class ConnectionManager:
    """Quản lý kết nối Real-time Socket (WebSocket / TCP) cho các phòng thi."""

    def __init__(self):
        # Lưu danh sách kết nối theo client_id (VD: mã sinh viên hoặc mã giám thị)
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        self.active_connections.pop(client_id, None)

    async def send_json(self, client_id: str, data: dict):
        websocket = self.active_connections.get(client_id)
        if websocket:
            await websocket.send_text(json.dumps(data, ensure_ascii=False))

    async def broadcast_json(self, data: dict):
        message = json.dumps(data, ensure_ascii=False)
        for connection in self.active_connections.values():
            await connection.send_text(message)


socket_manager = ConnectionManager()

