from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.database.db import Base


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False
    )
    chapter_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("knowledge_chapters.id", ondelete="RESTRICT"), nullable=False
    )
    question_type: Mapped[str] = mapped_column(String(30), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(10), nullable=False, default="TB")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    answer: Mapped[dict | list | str | None] = mapped_column(JSON, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    subject: Mapped["Subject"] = relationship(back_populates="questions")
    chapter: Mapped["KnowledgeChapter"] = relationship(back_populates="questions")
