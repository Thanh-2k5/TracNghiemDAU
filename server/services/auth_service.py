"""Dịch vụ xác thực (1.1.1 Đăng nhập, 1.1.2 Đăng xuất) - tái sử dụng cho cả 7 tác nhân."""
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from server.core.exceptions import ConflictError, ForbiddenError, UnauthorizedError
from server.core.security import create_access_token, hash_password, verify_password
from server.models import User, UserSession
from server.schemas.auth import LoginRequest
from server.services import session_service

# Hash giả để thời gian phản hồi khi sai username ~ khi sai mật khẩu (chống dò tài khoản)
_DUMMY_HASH = hash_password("dummy-password-for-timing")


def login(db: Session, req: LoginRequest, ip: Optional[str]) -> tuple[UserSession, str, datetime]:
    username = req.username.strip()
    user = db.scalar(select(User).where(User.username == username))
    if user is None:
        verify_password(req.password, _DUMMY_HASH)
        raise UnauthorizedError("Tên đăng nhập hoặc mật khẩu không chính xác", "INVALID_CREDENTIALS")
    if not verify_password(req.password, user.password_hash):
        raise UnauthorizedError("Tên đăng nhập hoặc mật khẩu không chính xác", "INVALID_CREDENTIALS")
    if not user.is_active:
        raise ForbiddenError("Tài khoản đã bị khóa. Vui lòng liên hệ quản trị viên.", "ACCOUNT_LOCKED")

    # 1.1.3 - Kiểm tra trùng phiên đăng nhập song song
    existing = session_service.find_alive_session(db, user.id)
    revoked_ids: list[str] = []
    if existing is not None:
        if not req.force:
            db.commit()  # lưu lại các phiên 'chết' vừa được dọn
            raise ConflictError(
                "Tài khoản đang được đăng nhập trên một thiết bị khác "
                f"(IP: {existing.ip_address or 'không rõ'}, từ {existing.created_at:%H:%M %d/%m/%Y}).",
                "SESSION_CONFLICT",
                extra={
                    "ip_address": existing.ip_address,
                    "client_info": existing.client_info,
                    "created_at": existing.created_at.isoformat(),
                },
            )
        revoked_ids = session_service.revoke_user_sessions(
            db, user.id, "Tài khoản đã được đăng nhập từ thiết bị khác"
        )

    session = session_service.create_session(db, user, ip, req.client_info)
    token, expires_at = create_access_token(user.id, user.role_code, session.id)
    user.last_login_at = datetime.now()
    db.commit()

    if revoked_ids:
        session_service.notify_force_logout(
            revoked_ids,
            "Tài khoản của bạn vừa được đăng nhập từ thiết bị khác. Phiên làm việc này đã bị đóng.",
        )
    return session, token, expires_at


def logout(db: Session, session: UserSession) -> None:
    """1.1.2 - Hủy phiên, thu hồi token và ngắt kết nối Socket an toàn."""
    session_service.revoke(db, session, "Người dùng đăng xuất")
    db.commit()
    session_service.close_socket_sessions([session.id])

