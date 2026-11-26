"""Cấu hình tập trung cho Server (đọc từ biến môi trường / file .env)."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


def _bool(name: str, default: str = "False") -> bool:
    return os.getenv(name, default).strip().lower() in ("true", "1", "yes", "on")


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "Hệ Thống Thi Trắc Nghiệm DAU")
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = _bool("DEBUG", "True")
    SQL_ECHO: bool = _bool("SQL_ECHO", "False")

    # --- REST API Server (FastAPI) ---
    API_HOST: str = os.getenv("API_HOST", "127.0.0.1")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))

    # --- Real-time Socket Server (TCP) ---
    SOCKET_HOST: str = os.getenv("SOCKET_HOST", "0.0.0.0")
    SOCKET_PORT: int = int(os.getenv("SOCKET_PORT", "9000"))
    SOCKET_AUTO_START: bool = _bool("SOCKET_AUTO_START", "True")
    SOCKET_MAX_PACKET_SIZE: int = int(os.getenv("SOCKET_MAX_PACKET_SIZE", str(4 * 1024 * 1024)))
    SOCKET_AUTH_TIMEOUT: int = int(os.getenv("SOCKET_AUTH_TIMEOUT", "10"))

    # --- Heartbeat & phiên đăng nhập ---
    HEARTBEAT_INTERVAL: int = int(os.getenv("HEARTBEAT_INTERVAL", "10"))
    HEARTBEAT_TIMEOUT: int = int(os.getenv("HEARTBEAT_TIMEOUT", "30"))
    SESSION_ALIVE_SECONDS: int = int(os.getenv("SESSION_ALIVE_SECONDS", "90"))

    # --- MySQL Database ---
    DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "tracnghiem_dau")
    # Cho phép ghi đè toàn bộ chuỗi kết nối (VD: sqlite:///test.db khi chạy kiểm thử)
    DATABASE_URL_OVERRIDE: str = os.getenv("DATABASE_URL", "")

    # --- Bảo mật & JWT ---
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change_this_to_a_secure_random_secret_key")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))
    DEFAULT_PASSWORD: str = os.getenv("DEFAULT_PASSWORD", "Dau@123456")

    # --- Sao lưu dữ liệu ---
    BACKUP_DIR: Path = Path(os.getenv("BACKUP_DIR", str(BASE_DIR / "backups")))

    @property
    def DATABASE_URL(self) -> str:
        if self.DATABASE_URL_OVERRIDE:
            return self.DATABASE_URL_OVERRIDE
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )

    @property
    def SERVER_DATABASE_URL(self) -> str:
        """Chuỗi kết nối tới MySQL Server (không chỉ định database) - dùng để tạo DB."""
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/?charset=utf8mb4"
        )


settings = Settings()
