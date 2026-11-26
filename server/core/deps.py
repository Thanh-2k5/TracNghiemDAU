"""Dependency FastAPI: lấy người dùng hiện tại từ Bearer token & kiểm tra phân quyền."""
from dataclasses import dataclass
from typing import Optional

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from server.core.constants import RoleCode
from server.core.exceptions import ForbiddenError
from server.database.db import get_db
from server.models import User, UserSession
from server.services import session_service

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    user: User
    session: UserSession


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> CurrentUser:
    token = credentials.credentials if credentials else None
    session = session_service.validate_token(db, token)
    session_service.touch(db, session)
    return CurrentUser(user=session.user, session=session)


def require_roles(*roles: RoleCode):
    allowed = {r.value for r in roles}

    def checker(current: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current.user.role_code not in allowed:
            raise ForbiddenError("Bạn không có quyền thực hiện chức năng này")
        return current

    return checker


require_admin = require_roles(RoleCode.ADMIN)

