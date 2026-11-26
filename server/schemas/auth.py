"""Schema cho module 1.1 - Xác thực và phiên đăng nhập."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role_code: str
    role_name: str
    is_active: bool
    must_change_password: bool
    last_login_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=64)
    force: bool = Field(default=False, description="True = đăng xuất phiên cũ đang hoạt động")
    client_info: Optional[str] = Field(default=None, max_length=255)


class SocketInfo(BaseModel):
    host: str
    port: int
    running: bool
    heartbeat_interval: int
    heartbeat_timeout: int


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    session_id: str
    server_time: datetime
    user: UserOut
    socket: SocketInfo


class SessionInfo(BaseModel):
    session_id: str
    ip_address: Optional[str] = None
    created_at: datetime
    last_activity_at: datetime
    expires_at: datetime
    socket_online: bool
    user: UserOut

