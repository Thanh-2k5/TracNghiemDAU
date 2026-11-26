"""Controller quản lý tài khoản (1.3) - Admin."""
from typing import Optional

from sqlalchemy.orm import Session

from server.core.deps import CurrentUser
from server.schemas.account import (AccountCreate, AccountListResponse, AccountUpdate, ResetPasswordResponse,
                                    RoleOut)
from server.schemas.auth import UserOut
from server.services import user_service


def list_roles(db: Session) -> list[RoleOut]:
    return [RoleOut.model_validate(r) for r in user_service.list_roles(db)]


def list_accounts(db: Session, keyword: Optional[str], role_code: Optional[str], is_active: Optional[bool],
                  page: int, page_size: int) -> AccountListResponse:
    items, total = user_service.list_accounts(db, keyword, role_code, is_active, page, page_size)
    return AccountListResponse(items=[UserOut.model_validate(u) for u in items], total=total,
                               page=page, page_size=page_size)


def get_account(db: Session, user_id: int) -> UserOut:
    return UserOut.model_validate(user_service.get_user(db, user_id))


def create_account(db: Session, data: AccountCreate) -> UserOut:
    return UserOut.model_validate(user_service.create_account(db, data))


def update_account(db: Session, user_id: int, data: AccountUpdate) -> UserOut:
    return UserOut.model_validate(user_service.update_account(db, user_id, data))


def set_status(db: Session, current: CurrentUser, user_id: int, is_active: bool) -> UserOut:
    return UserOut.model_validate(user_service.set_account_status(db, current.user, user_id, is_active))


def reset_password(db: Session, current: CurrentUser, user_id: int) -> ResetPasswordResponse:
    user, default_password = user_service.reset_password(db, current.user, user_id)
    return ResetPasswordResponse(
        message=f"Đã đặt lại mật khẩu cho tài khoản '{user.username}'",
        default_password=default_password,
    )


def assign_role(db: Session, current: CurrentUser, user_id: int, role_code: str) -> UserOut:
    return UserOut.model_validate(user_service.assign_role(db, current.user, user_id, role_code))

