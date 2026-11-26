"""Bảng phiên đăng nhập - phục vụ đăng xuất an toàn và chặn trùng phiên song song."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.database.db import Base
from server.models.user import User


class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ip_address: Mapped[Optional[str]] = mapped_column(String(64))
    client_info: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    revoke_reason: Mapped[Optional[str]] = mapped_column(String(255))
    socket_connection_id: Mapped[Optional[str]] = mapped_column(String(36))

    user: Mapped[User] = relationship(lazy="joined")

    @property
    def is_valid(self) -> bool:
        """Phiên chưa bị thu hồi và chưa hết hạn token."""
        return self.revoked_at is None and self.expires_at > datetime.now()

    def __repr__(self) -> str:
        return f"<UserSession {self.id} user={self.user_id}>"
