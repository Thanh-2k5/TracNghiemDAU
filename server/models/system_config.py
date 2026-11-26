"""Bảng cấu hình hệ thống dạng key-value (VD: IP/Port Socket Server)."""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from server.database.db import Base


class SystemConfig(Base):
    __tablename__ = "system_configs"

    key: Mapped[str] = mapped_column("config_key", String(64), primary_key=True)
    value: Mapped[Optional[str]] = mapped_column("config_value", Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )

