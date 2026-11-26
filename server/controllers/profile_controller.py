"""Controller thông tin cá nhân (1.2) - dùng chung cho 7 tác nhân."""
from sqlalchemy.orm import Session

from server.core.deps import CurrentUser
from server.schemas.auth import UserOut
from server.schemas.common import MessageResponse
from server.schemas.profile import ChangePasswordRequest, ProfileUpdate
from server.services import user_service


def get_profile(current: CurrentUser) -> UserOut:
    return UserOut.model_validate(current.user)


def update_profile(db: Session, current: CurrentUser, data: ProfileUpdate) -> UserOut:
    return UserOut.model_validate(user_service.update_profile(db, current.user, data))


def change_password(db: Session, current: CurrentUser, data: ChangePasswordRequest) -> MessageResponse:
    user_service.change_password(db, current.user, data)
    return MessageResponse(message="Đổi mật khẩu thành công")

