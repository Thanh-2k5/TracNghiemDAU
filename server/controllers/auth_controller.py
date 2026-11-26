"""Controller xác thực (1.1) - điều phối request -> service -> schema phản hồi."""
from datetime import datetime

from fastapi import Request
from sqlalchemy.orm import Session

from server.core.deps import CurrentUser
from server.schemas.auth import LoginRequest, LoginResponse, SessionInfo, SocketInfo, UserOut
from server.schemas.common import MessageResponse
from server.services import auth_service, network_service, session_service
from server.socket_server.connection_manager import socket_manager


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def login(db: Session, req: LoginRequest, request: Request) -> LoginResponse:
    session, token, expires_at = auth_service.login(db, req, _client_ip(request))
    return LoginResponse(
        access_token=token,
        expires_at=expires_at,
        session_id=session.id,
        server_time=datetime.now(),
        user=UserOut.model_validate(session.user),
        socket=SocketInfo(**network_service.get_socket_info(db)),
    )


def logout(db: Session, current: CurrentUser) -> MessageResponse:
    auth_service.logout(db, current.session)
    return MessageResponse(message="Đăng xuất thành công")


def session_info(current: CurrentUser) -> SessionInfo:
    s = current.session
    return SessionInfo(
        session_id=s.id,
        ip_address=s.ip_address,
        created_at=s.created_at,
        last_activity_at=s.last_activity_at,
        expires_at=s.expires_at,
        socket_online=socket_manager.is_session_online(s.id),
        user=UserOut.model_validate(current.user),
    )


def heartbeat(db: Session, current: CurrentUser) -> dict:
    """Heartbeat dự phòng qua REST khi kênh Socket tạm thời không khả dụng."""
    session_service.touch(db, current.session, force=True)
    return {"message": "ok", "server_time": datetime.now()}

