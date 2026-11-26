"""Schema cho module 1.4 - Quản trị mạng (Admin)."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from server.schemas.validators import Host


class NetworkConfig(BaseModel):
    socket_host: Host
    socket_port: int = Field(ge=1024, le=65535)
    api_host: Host
    api_port: int = Field(ge=1024, le=65535)


class NetworkConfigResponse(NetworkConfig):
    message: Optional[str] = None
    restart_required: bool = False


class ServerStatus(BaseModel):
    running: bool
    host: Optional[str] = None
    port: Optional[int] = None
    started_at: Optional[datetime] = None
    uptime_seconds: int = 0
    connection_count: int = 0
    authenticated_count: int = 0
    server_time: datetime
    message: Optional[str] = None


class ConnectionOut(BaseModel):
    connection_id: str
    transport: str
    address: str
    user_id: Optional[int] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    role_code: Optional[str] = None
    authenticated: bool
    connected_at: datetime
    last_heartbeat_at: datetime
    seconds_since_heartbeat: float
    latency_ms: Optional[float] = None
    bytes_in: int
    bytes_out: int
    packets_in: int
    packets_out: int
    rate_in_bps: float
    rate_out_bps: float


class ConnectionsResponse(BaseModel):
    status: ServerStatus
    total_bytes_in: int
    total_bytes_out: int
    total_rate_in_bps: float
    total_rate_out_bps: float
    connections: list[ConnectionOut]
