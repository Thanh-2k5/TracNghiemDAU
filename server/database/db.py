from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from server.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency cung cấp database session cho các FastAPI routers."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

