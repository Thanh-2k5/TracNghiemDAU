"""Dịch vụ quản lý phiên đăng nhập (1.1.2, 1.1.3) - dùng chung cho cả 7 tác nhân."""
from datetime import datetime, timedelta
from typing import Optional

import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from server.core.config import settings
from server.core.exceptions import UnauthorizedError
from server.core.security import decode_access_token
from server.database.db import session_scope
from server.models import User, UserSession
from server.socket_server.connection_manager import socket_manager

TOUCH_THROTTLE_SECONDS = 15


def is_session_alive(session: UserSession) -> bool:
    """Phiên còn 'sống' nếu đang giữ kết nối socket hoặc vừa có hoạt động gần đây."""
    if socket_manager.is_session_online(session.id):
        return True
    idle = (datetime.now() - session.last_activity_at).total_seconds()
    return idle < settings.SESSION_ALIVE_SECONDS


def get_valid_sessions(db: Session, user_id: int) -> list[UserSession]:
    stmt = select(UserSession).where(
        UserSession.user_id == user_id,
        UserSession.revoked_at.is_(None),
        UserSession.expires_at > datetime.now(),
    )
    return list(db.scalars(stmt))


def find_alive_session(db: Session, user_id: int) -> Optional[UserSession]:
    """1.1.3 - Tìm phiên song song còn hoạt động; tự đóng các phiên 'chết' (mất kết nối lâu)."""
    alive: Optional[UserSession] = None
    for session in get_valid_sessions(db, user_id):
        if is_session_alive(session):
            alive = alive or session
        else:
            revoke(db, session, "Phiên tự động kết thúc do không còn hoạt động")
    return alive


def create_session(db: Session, user: User, ip: Optional[str], client_info: Optional[str]) -> UserSession:
    now = datetime.now()
    session = UserSession(
        user_id=user.id,
        ip_address=ip,
        client_info=(client_info or "")[:255] or None,
        created_at=now,
        last_activity_at=now,
        expires_at=now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    db.add(session)
    db.flush()
    return session


def revoke(db: Session, session: UserSession, reason: str) -> None:
    if session.revoked_at is None:
        session.revoked_at = datetime.now()
        session.revoke_reason = reason[:255]
        session.socket_connection_id = None
        db.add(session)


def revoke_user_sessions(db: Session, user_id: int, reason: str, exclude_id: Optional[str] = None) -> list[str]:
    revoked: list[str] = []
    for session in get_valid_sessions(db, user_id):
        if session.id != exclude_id:
            revoke(db, session, reason)
            revoked.append(session.id)
    return revoked


def validate_token(db: Session, token: Optional[str]) -> UserSession:
    """Kiểm tra token + phiên trong DB. Dùng chung cho REST (deps) và Socket (handshake)."""
    if not token:
        raise UnauthorizedError("Bạn chưa đăng nhập", "UNAUTHENTICATED")
    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedError("Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại", "TOKEN_EXPIRED") from exc
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Token xác thực không hợp lệ", "INVALID_TOKEN") from exc

    session = db.get(UserSession, payload.get("sid"))
    if session is None:
        raise UnauthorizedError("Phiên đăng nhập không tồn tại", "SESSION_REVOKED")
    if session.revoked_at is not None:
        reason = session.revoke_reason or "Phiên đã bị đóng"
        raise UnauthorizedError(f"Phiên đăng nhập đã kết thúc: {reason}", "SESSION_REVOKED")
    if session.expires_at <= datetime.now():
        raise UnauthorizedError("Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại", "TOKEN_EXPIRED")
    if session.user is None:
        raise UnauthorizedError("Tài khoản không còn tồn tại", "SESSION_REVOKED")
    if not session.user.is_active:
        raise UnauthorizedError("Tài khoản đã bị khóa", "ACCOUNT_LOCKED")
    return session


def touch(db: Session, session: UserSession, force: bool = False) -> None:
    now = datetime.now()
    if force or (now - session.last_activity_at).total_seconds() >= TOUCH_THROTTLE_SECONDS:
        session.last_activity_at = now
        db.add(session)
        db.commit()


def touch_session_by_id(session_id: str) -> None:
    """Gọi từ Socket Server (heartbeat) - chạy trong thread riêng."""
    with session_scope() as db:
        session = db.get(UserSession, session_id)
        if session and session.revoked_at is None:
            session.last_activity_at = datetime.now()


def verify_socket_token(token: Optional[str], connection_id: str) -> dict:
    """Xác thực gói 'auth' của Socket; gắn connection_id vào phiên."""
    with session_scope() as db:
        session = validate_token(db, token)
        session.socket_connection_id = connection_id
        session.last_activity_at = datetime.now()
        user = session.user
        return {
            "session_id": session.id,
            "user_id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "role_code": user.role_code,
        }


def notify_force_logout(session_ids: list[str], reason: str) -> None:
    socket_manager.force_logout_sessions(session_ids, reason)


def close_socket_sessions(session_ids: list[str]) -> None:
    socket_manager.close_sessions(session_ids)
