"""Dịch vụ người dùng: 1.2 Thông tin cá nhân (dùng chung) và 1.3 Quản lý tài khoản (Admin)."""
from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from server.core.config import settings
from server.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from server.core.security import hash_password, verify_password
from server.models import Role, User
from server.schemas.account import AccountCreate, AccountUpdate
from server.schemas.profile import ChangePasswordRequest, ProfileUpdate
from server.services import session_service


# ============================ Tiện ích ============================
def get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("Không tìm thấy tài khoản")
    return user


def get_role_by_code(db: Session, code: str) -> Role:
    role = db.scalar(select(Role).where(Role.code == code))
    if role is None:
        raise BadRequestError(f"Vai trò không tồn tại: {code}")
    return role


def _ensure_email_unique(db: Session, email: Optional[str], exclude_user_id: Optional[int] = None) -> None:
    if not email:
        return
    stmt = select(User.id).where(func.lower(User.email) == email.lower())
    if exclude_user_id:
        stmt = stmt.where(User.id != exclude_user_id)
    if db.scalar(stmt) is not None:
        raise ConflictError("Email đã được sử dụng bởi tài khoản khác", "EMAIL_EXISTS")


# ==================== 1.2 Thông tin cá nhân ====================
def update_profile(db: Session, user: User, data: ProfileUpdate) -> User:
    """1.2.1 - Cập nhật họ tên, email, số điện thoại."""
    _ensure_email_unique(db, data.email, user.id)
    user.full_name = data.full_name
    user.email = data.email
    user.phone = data.phone
    db.commit()
    db.refresh(user)
    return user


def change_password(db: Session, user: User, data: ChangePasswordRequest) -> None:
    """1.2.2 - Đổi mật khẩu (xác thực mật khẩu cũ)."""
    if not verify_password(data.old_password, user.password_hash):
        raise BadRequestError("Mật khẩu cũ không chính xác", "WRONG_PASSWORD")
    user.password_hash = hash_password(data.new_password)
    user.must_change_password = False
    db.commit()


# ==================== 1.3 Quản lý tài khoản ====================
def list_roles(db: Session) -> list[Role]:
    return list(db.scalars(select(Role).order_by(Role.id)))


def list_accounts(
    db: Session,
    keyword: Optional[str] = None,
    role_code: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[User], int]:
    stmt = select(User).join(User.role)
    if keyword:
        like = f"%{keyword.strip()}%"
        stmt = stmt.where(or_(User.username.ilike(like), User.full_name.ilike(like),
                              User.email.ilike(like), User.phone.ilike(like)))
    if role_code:
        stmt = stmt.where(Role.code == role_code)
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)

    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    page = max(page, 1)
    page_size = min(max(page_size, 1), 200)
    items = db.scalars(stmt.order_by(User.id).offset((page - 1) * page_size).limit(page_size)).unique()
    return list(items), total


def create_account(db: Session, data: AccountCreate) -> User:
    """1.3.1 - Thêm mới tài khoản (mật khẩu trống => mật khẩu mặc định, bắt buộc đổi khi đăng nhập)."""
    if db.scalar(select(User.id).where(User.username == data.username)) is not None:
        raise ConflictError(f"Tên đăng nhập '{data.username}' đã tồn tại", "USERNAME_EXISTS")
    _ensure_email_unique(db, data.email)
    role = get_role_by_code(db, data.role_code.value)
    use_default = data.password is None
    user = User(
        username=data.username,
        password_hash=hash_password(settings.DEFAULT_PASSWORD if use_default else data.password),
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
        role_id=role.id,
        is_active=data.is_active,
        must_change_password=use_default,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_account(db: Session, user_id: int, data: AccountUpdate) -> User:
    """1.3.1 - Sửa thông tin tài khoản."""
    user = get_user(db, user_id)
    _ensure_email_unique(db, data.email, user.id)
    user.full_name = data.full_name
    user.email = data.email
    user.phone = data.phone
    db.commit()
    db.refresh(user)
    return user


def set_account_status(db: Session, actor: User, user_id: int, is_active: bool) -> User:
    """1.3.1 - Khóa / mở khóa tài khoản. Khóa => thu hồi mọi phiên và ngắt Socket ngay."""
    user = get_user(db, user_id)
    if user.id == actor.id and not is_active:
        raise ForbiddenError("Không thể tự khóa tài khoản đang đăng nhập")
    user.is_active = is_active
    revoked: list[str] = []
    if not is_active:
        revoked = session_service.revoke_user_sessions(db, user.id, "Tài khoản bị khóa bởi quản trị viên")
    db.commit()
    db.refresh(user)
    session_service.notify_force_logout(revoked, "Tài khoản của bạn đã bị khóa bởi quản trị viên.")
    return user


def reset_password(db: Session, actor: User, user_id: int) -> tuple[User, str]:
    """1.3.2 - Đặt lại mật khẩu mặc định và yêu cầu đổi mật khẩu ở lần đăng nhập tiếp theo."""
    user = get_user(db, user_id)
    if user.id == actor.id:
        raise ForbiddenError("Hãy dùng chức năng 'Đổi mật khẩu' cho tài khoản của chính bạn")
    user.password_hash = hash_password(settings.DEFAULT_PASSWORD)
    user.must_change_password = True
    revoked = session_service.revoke_user_sessions(db, user.id, "Mật khẩu đã được đặt lại bởi quản trị viên")
    db.commit()
    db.refresh(user)
    session_service.notify_force_logout(revoked, "Mật khẩu của bạn đã được quản trị viên đặt lại. Vui lòng đăng nhập lại.")
    return user, settings.DEFAULT_PASSWORD


def assign_role(db: Session, actor: User, user_id: int, role_code: str) -> User:
    """1.3.3 - Gán vai trò (1 trong 7 nhóm tác nhân). Phiên hiện tại của tài khoản bị đóng để nạp quyền mới."""
    user = get_user(db, user_id)
    if user.id == actor.id:
        raise ForbiddenError("Không thể tự thay đổi vai trò của chính mình")
    role = get_role_by_code(db, role_code)
    if user.role_id == role.id:
        return user
    user.role_id = role.id
    revoked = session_service.revoke_user_sessions(db, user.id, "Vai trò tài khoản đã thay đổi")
    db.commit()
    db.refresh(user)
    session_service.notify_force_logout(
        revoked, f"Vai trò tài khoản đã được đổi thành '{role.name}'. Vui lòng đăng nhập lại.")
    return user

