"""Hàm kiểm tra dữ liệu đầu vào dùng chung cho các schema."""
import ipaddress
import re
from typing import Annotated, Optional

from pydantic import AfterValidator

USERNAME_RE = re.compile(r"^[A-Za-z0-9_.]{3,50}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
PHONE_RE = re.compile(r"^(\+84|0)\d{9,10}$")

PASSWORD_MIN = 6
PASSWORD_MAX = 64


def clean_optional(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    return value or None


def validate_username(value: str) -> str:
    value = value.strip()
    if not USERNAME_RE.match(value):
        raise ValueError("Tên đăng nhập 3-50 ký tự, chỉ gồm chữ, số, dấu '_' hoặc '.'")
    return value


def validate_full_name(value: str) -> str:
    value = " ".join(value.split())
    if len(value) < 2 or len(value) > 100:
        raise ValueError("Họ tên phải từ 2 đến 100 ký tự")
    return value


def validate_email(value: Optional[str]) -> Optional[str]:
    value = clean_optional(value)
    if value is not None and (len(value) > 100 or not EMAIL_RE.match(value)):
        raise ValueError("Email không hợp lệ")
    return value


def validate_phone(value: Optional[str]) -> Optional[str]:
    value = clean_optional(value)
    if value is not None:
        value = value.replace(" ", "").replace(".", "")
        if not PHONE_RE.match(value):
            raise ValueError("Số điện thoại không hợp lệ (VD: 0912345678)")
    return value


def validate_password(value: str) -> str:
    if len(value) < PASSWORD_MIN or len(value) > PASSWORD_MAX:
        raise ValueError(f"Mật khẩu phải từ {PASSWORD_MIN} đến {PASSWORD_MAX} ký tự")
    if value.strip() != value:
        raise ValueError("Mật khẩu không được bắt đầu hoặc kết thúc bằng khoảng trắng")
    return value


def validate_optional_password(value: Optional[str]) -> Optional[str]:
    if value is None or value == "":
        return None
    return validate_password(value)


def validate_host(value: str) -> str:
    value = value.strip()
    if value in ("localhost", "0.0.0.0"):
        return value
    try:
        ipaddress.IPv4Address(value)
    except ValueError as exc:
        raise ValueError("Địa chỉ IP không hợp lệ (VD: 192.168.1.10 hoặc 0.0.0.0)") from exc
    return value


# --- Kiểu dữ liệu tái sử dụng (Annotated) cho các schema ---
Username = Annotated[str, AfterValidator(validate_username)]
FullName = Annotated[str, AfterValidator(validate_full_name)]
OptEmail = Annotated[Optional[str], AfterValidator(validate_email)]
OptPhone = Annotated[Optional[str], AfterValidator(validate_phone)]
Password = Annotated[str, AfterValidator(validate_password)]
OptPassword = Annotated[Optional[str], AfterValidator(validate_optional_password)]
Host = Annotated[str, AfterValidator(validate_host)]
