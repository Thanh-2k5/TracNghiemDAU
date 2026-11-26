"""Schema cho module 1.3 - Quản lý tài khoản (Admin)."""
from typing import Optional

from pydantic import BaseModel, ConfigDict

from server.core.constants import RoleCode
from server.schemas.auth import UserOut
from server.schemas.validators import FullName, OptEmail, OptPassword, OptPhone, Username


class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: Optional[str] = None


class AccountCreate(BaseModel):
    username: Username
    password: OptPassword = None  # Để trống => dùng mật khẩu mặc định
    full_name: FullName
    email: OptEmail = None
    phone: OptPhone = None
    role_code: RoleCode
    is_active: bool = True


class AccountUpdate(BaseModel):
    full_name: FullName
    email: OptEmail = None
    phone: OptPhone = None


class AccountStatusUpdate(BaseModel):
    is_active: bool


class RoleAssign(BaseModel):
    role_code: RoleCode


class AccountListResponse(BaseModel):
    items: list[UserOut]
    total: int
    page: int
    page_size: int


class ResetPasswordResponse(BaseModel):
    message: str
    default_password: str
