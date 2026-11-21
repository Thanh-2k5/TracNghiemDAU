import json
import os
import socket
import threading
from typing import Callable, Optional
from PySide6.QtCore import QObject, Signal


class SocketClient(QObject):
    """Client kết nối Real-time Socket (TCP/JSON) tích hợp Qt Signal cho PySide6."""

    message_received = Signal(dict)
    connection_changed = Signal(bool)

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None):
        super().__init__()
        self.host = host or os.getenv("SOCKET_HOST", "127.0.0.1")
        self.port = port or int(os.getenv("SOCKET_PORT", "9000"))
        self._sock: Optional[socket.socket] = None
        self._running = False

    def connect_server(self) -> bool:
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.connect((self.host, self.port))
            self._running = True
            self.connection_changed.emit(True)
            threading.Thread(target=self._listen_loop, daemon=True).start()
            return True
        except OSError:
            self.connection_changed.emit(False)
            return False

    def send_json(self, payload: dict):
        if self._sock and self._running:
            raw = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
            self._sock.sendall(raw)

    def _listen_loop(self):
        buffer = ""
        while self._running and self._sock:
            try:
                chunk = self._sock.recv(4096)
                if not chunk:
                    break
                buffer += chunk.decode("utf-8")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.strip():
                        self.message_received.emit(json.loads(line))
            except (OSError, json.JSONDecodeError):
                break
        self._running = False
        self.connection_changed.emit(False)

    def disconnect_server(self):
        self._running = False
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None

