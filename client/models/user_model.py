"""Model dữ liệu và trạng thái phiên làm việc phía Desktop Client (MVC Model)."""
from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from PySide6.QtCore import QObject, Signal

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")
CLIENT_CONFIG_PATH = BASE_DIR / ".client_config.json"


@dataclass
class UserProfile:
    id: int
    username: str
    full_name: str
    email: Optional[str]
    phone: Optional[str]
    role_code: str
    role_name: str
    is_active: bool
    must_change_password: bool = False
    last_login_at: Optional[str] = None
    created_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UserProfile":
        return cls(
            id=int(data["id"]),
            username=str(data["username"]),
            full_name=str(data["full_name"]),
            email=data.get("email"),
            phone=data.get("phone"),
            role_code=str(data["role_code"]),
            role_name=str(data.get("role_name") or data["role_code"]),
            is_active=bool(data.get("is_active", True)),
            must_change_password=bool(data.get("must_change_password", False)),
            last_login_at=data.get("last_login_at"),
            created_at=data.get("created_at"),
        )


class ClientEndpointConfig:
    """Lưu/đọc cấu hình địa chỉ REST API Server trên máy trạm Client."""

    @staticmethod
    def load() -> tuple[str, int]:
        default_host = os.getenv("API_HOST", "127.0.0.1")
        if default_host == "0.0.0.0":
            default_host = "127.0.0.1"
        default_port = int(os.getenv("API_PORT", "8000"))
        if CLIENT_CONFIG_PATH.is_file():
            try:
                raw = json.loads(CLIENT_CONFIG_PATH.read_text(encoding="utf-8"))
                host = str(raw.get("api_host") or default_host).strip()
                port = int(raw.get("api_port") or default_port)
                return host, port
            except (OSError, ValueError, TypeError):
                pass
        return default_host, default_port

    @staticmethod
    def save(api_host: str, api_port: int) -> None:
        payload = {"api_host": api_host.strip(), "api_port": int(api_port)}
        CLIENT_CONFIG_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


class SessionState(QObject):
    """Lưu trữ trạng thái phiên đăng nhập & kết nối Socket dùng chung cho cả 7 phân hệ."""

    user_changed = Signal(object)              # UserProfile | None
    socket_state_changed = Signal(bool, object)  # (online: bool, latency_ms: float | None)

    def __init__(self) -> None:
        super().__init__()
        self.access_token: Optional[str] = None
        self.session_id: Optional[str] = None
        self.user: Optional[UserProfile] = None
        self.socket_online: bool = False
        self.latency_ms: Optional[float] = None

    @property
    def is_authenticated(self) -> bool:
        return bool(self.access_token and self.user)

    def set_login(self, token: str, session_id: str, user: UserProfile) -> None:
        self.access_token = token
        self.session_id = session_id
        self.user = user
        self.user_changed.emit(user)

    def update_user(self, user: UserProfile) -> None:
        self.user = user
        self.user_changed.emit(user)

    def set_socket_state(self, online: bool, latency_ms: Optional[float] = None) -> None:
        self.socket_online = online
        self.latency_ms = latency_ms if online else None
        self.socket_state_changed.emit(self.socket_online, self.latency_ms)

    def clear(self) -> None:
        self.access_token = None
        self.session_id = None
        self.user = None
        self.socket_online = False
        self.latency_ms = None
        self.user_changed.emit(None)
        self.socket_state_changed.emit(False, None)


session_state = SessionState()

