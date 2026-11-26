"""Controller quản trị mạng (1.4) - Admin."""
from sqlalchemy.orm import Session

from server.schemas.network import ConnectionsResponse, NetworkConfig, NetworkConfigResponse, ServerStatus
from server.schemas.common import MessageResponse
from server.services import network_service


def get_config(db: Session) -> NetworkConfigResponse:
    return NetworkConfigResponse(**network_service.get_config(db))


def save_config(db: Session, cfg: NetworkConfig) -> NetworkConfigResponse:
    return NetworkConfigResponse(**network_service.save_config(db, cfg))


def status() -> ServerStatus:
    return ServerStatus(**network_service.get_status())


async def start(db: Session) -> ServerStatus:
    await network_service.start_server(db)
    return ServerStatus(**network_service.get_status("Socket Server đã khởi động"))


async def stop() -> ServerStatus:
    await network_service.stop_server()
    return ServerStatus(**network_service.get_status("Socket Server đã dừng"))


async def restart(db: Session) -> ServerStatus:
    await network_service.restart_server(db)
    return ServerStatus(**network_service.get_status("Socket Server đã khởi động lại"))


def connections() -> ConnectionsResponse:
    return ConnectionsResponse(**network_service.get_connections())


async def kick(connection_id: str) -> MessageResponse:
    await network_service.kick_connection(connection_id)
    return MessageResponse(message="Đã ngắt kết nối")

