"""Schema cho module 1.2 - Thông tin cá nhân."""
from pydantic import BaseModel, model_validator

from server.schemas.validators import FullName, OptEmail, OptPhone, Password


class ProfileUpdate(BaseModel):
    full_name: FullName
    email: OptEmail = None
    phone: OptPhone = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: Password
    confirm_password: str

    @model_validator(mode="after")
    def check_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Xác nhận mật khẩu mới không khớp")
        if self.new_password == self.old_password:
            raise ValueError("Mật khẩu mới phải khác mật khẩu cũ")
        return self
