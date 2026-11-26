"""Schema cho module 1.5 - Sao lưu và phục hồi dữ liệu (Admin)."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class BackupFileOut(BaseModel):
    filename: str
    size_bytes: int
    created_at: datetime


class RestoreResult(BaseModel):
    message: str
    statements_executed: int
    safety_backup: Optional[str] = None

