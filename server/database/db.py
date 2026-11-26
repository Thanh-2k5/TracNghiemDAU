"""Kết nối MySQL bằng SQLAlchemy: engine, session factory, Base ORM và dependency get_db."""
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from server.core.config import settings


class Base(DeclarativeBase):
    """Lớp cơ sở cho toàn bộ ORM model của hệ thống."""


def _build_engine():
    url = settings.DATABASE_URL
    kwargs: dict = {"echo": settings.SQL_ECHO, "pool_pre_ping": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        kwargs.update(pool_recycle=3600, pool_size=10, max_overflow=20)
    return create_engine(url, **kwargs)


engine = _build_engine()

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """Dependency cung cấp database session cho các FastAPI router."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Iterator[Session]:
    """Context manager dùng ngoài HTTP (socket server, script): tự commit / rollback."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
