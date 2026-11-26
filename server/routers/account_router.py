"""Router 1.3 - Quản lý tài khoản (Admin)."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from server.controllers import account_controller
from server.core.constants import RoleCode
from server.core.deps import CurrentUser, require_admin
from server.database.db import get_db
from server.schemas.account import (AccountCreate, AccountListResponse, AccountStatusUpdate, AccountUpdate,
                                    ResetPasswordResponse, RoleAssign, RoleOut)
from server.schemas.auth import UserOut

router = APIRouter(prefix="/api/admin", tags=["1.3 Quản lý tài khoản (Admin)"])


@router.get("/roles", response_model=list[RoleOut], summary="Danh sách 7 vai trò")
def list_roles(_: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    return account_controller.list_roles(db)


@router.get("/accounts", response_model=AccountListResponse, summary="Danh sách / tìm kiếm tài khoản")
def list_accounts(
    keyword: Optional[str] = Query(None, max_length=100),
    role_code: Optional[RoleCode] = None,
    is_active: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    _: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return account_controller.list_accounts(db, keyword, role_code.value if role_code else None,
                                            is_active, page, page_size)


@router.get("/accounts/{user_id}", response_model=UserOut, summary="Chi tiết tài khoản")
def get_account(user_id: int, _: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    return account_controller.get_account(db, user_id)


@router.post("/accounts", response_model=UserOut, status_code=201, summary="1.3.1 Thêm tài khoản")
def create_account(data: AccountCreate, _: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    return account_controller.create_account(db, data)


@router.put("/accounts/{user_id}", response_model=UserOut, summary="1.3.1 Sửa tài khoản")
def update_account(user_id: int, data: AccountUpdate, _: CurrentUser = Depends(require_admin),
                   db: Session = Depends(get_db)):
    return account_controller.update_account(db, user_id, data)


@router.patch("/accounts/{user_id}/status", response_model=UserOut, summary="1.3.1 Khóa / mở khóa tài khoản")
def set_status(user_id: int, data: AccountStatusUpdate, current: CurrentUser = Depends(require_admin),
               db: Session = Depends(get_db)):
    return account_controller.set_status(db, current, user_id, data.is_active)


@router.post("/accounts/{user_id}/reset-password", response_model=ResetPasswordResponse,
             summary="1.3.2 Đặt lại mật khẩu mặc định")
def reset_password(user_id: int, current: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    return account_controller.reset_password(db, current, user_id)


@router.put("/accounts/{user_id}/role", response_model=UserOut, summary="1.3.3 Gán vai trò")
def assign_role(user_id: int, data: RoleAssign, current: CurrentUser = Depends(require_admin),
                db: Session = Depends(get_db)):
    return account_controller.assign_role(db, current, user_id, data.role_code.value)

