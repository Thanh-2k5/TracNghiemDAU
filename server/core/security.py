"""Băm mật khẩu (bcrypt) và tạo / giải mã JWT access token."""
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from server.core.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: int, role: str, session_id: str) -> tuple[str, datetime]:
    """Trả về (token, thời điểm hết hạn - giờ địa phương, naive)."""
    now_utc = datetime.now(timezone.utc)
    expire_utc = now_utc + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "role": role,
        "sid": session_id,
        "iat": int(now_utc.timestamp()),
        "exp": int(expire_utc.timestamp()),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    expires_local = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return token, expires_local


def decode_access_token(token: str) -> dict[str, Any]:
    """Giải mã token. Ném jwt.ExpiredSignatureError / jwt.PyJWTError nếu không hợp lệ."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

