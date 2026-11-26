"""Router 1.2 - Thông tin cá nhân (dùng chung cho 7 tác nhân)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from server.controllers import profile_controller
from server.core.deps import CurrentUser, get_current_user
from server.database.db import get_db
from server.schemas.auth import UserOut
from server.schemas.common import MessageResponse
from server.schemas.profile import ChangePasswordRequest, ProfileUpdate

router = APIRouter(prefix="/api/profile", tags=["1.2 Thông tin cá nhân"])


@router.get("", response_model=UserOut, summary="1.2.1 Xem thông tin cá nhân")
def get_profile(current: CurrentUser = Depends(get_current_user)):
    return profile_controller.get_profile(current)


@router.put("", response_model=UserOut, summary="1.2.1 Cập nhật thông tin cá nhân")
def update_profile(data: ProfileUpdate, current: CurrentUser = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    return profile_controller.update_profile(db, current, data)


@router.post("/change-password", response_model=MessageResponse, summary="1.2.2 Đổi mật khẩu")
def change_password(data: ChangePasswordRequest, current: CurrentUser = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    return profile_controller.change_password(db, current, data)

