from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.database.db import Base


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    credits: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    exam_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    chapters: Mapped[list["KnowledgeChapter"]] = relationship(
        back_populates="subject", cascade="all, delete-orphan", passive_deletes=True
    )
    questions: Mapped[list["Question"]] = relationship(
        back_populates="subject", cascade="all, delete-orphan", passive_deletes=True
    )
