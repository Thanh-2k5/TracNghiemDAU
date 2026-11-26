"""Khởi tạo CSDL MySQL, tạo bảng ORM và nạp dữ liệu mặc định (7 vai trò + tài khoản mẫu)."""
import logging

from sqlalchemy import create_engine, select, text

from server.core.config import settings
from server.core.constants import ROLE_DEFINITIONS, ConfigKey, RoleCode
from server.core.security import hash_password
from server.database.db import Base, engine, session_scope
from server.models import Role, SystemConfig, User

logger = logging.getLogger("database")

SEED_ACCOUNTS = [
    ("admin", "Admin@123", "Nguyễn Văn Thạnh (Admin)", "admin@dau.edu.vn", "0905111222", RoleCode.ADMIN),
    ("ctsv01", "Dau@123456", "Chuyên viên Phòng CTSV", "ctsv@dau.edu.vn", "0905111223", RoleCode.CTSV),
    ("daotao01", "Dau@123456", "Chuyên viên Phòng Đào tạo", "daotao@dau.edu.vn", "0905111224", RoleCode.DAOTAO),
    ("khoa_cntt", "Dau@123456", "Giảng viên Khoa CNTT", "khoacntt@dau.edu.vn", "0905111225", RoleCode.KHOA),
    ("khaothi01", "Dau@123456", "Chuyên viên Phòng Khảo thí", "khaothi@dau.edu.vn", "0905111226", RoleCode.KHAOTHI),
    ("coithi01", "Dau@123456", "Cán bộ Coi thi 01", "coithi01@dau.edu.vn", "0905111227", RoleCode.COITHI),
    ("sv221001", "Dau@123456", "Trần Minh Khoa (SV)", "sv221001@dau.edu.vn", "0905111228", RoleCode.SINHVIEN),
]


def ensure_mysql_database() -> None:
    """Tự động tạo database trên MySQL Server nếu chưa tồn tại."""
    if not settings.DATABASE_URL.startswith("mysql"):
        return
    server_engine = create_engine(settings.SERVER_DATABASE_URL, isolation_level="AUTOCOMMIT")
    try:
        with server_engine.connect() as conn:
            conn.execute(
                text(
                    f"CREATE DATABASE IF NOT EXISTS `{settings.DB_NAME}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            )
    finally:
        server_engine.dispose()


def seed_defaults() -> None:
    """Nạp 7 vai trò, cấu hình mạng mặc định và tài khoản mẫu (nếu bảng chưa có dữ liệu)."""
    with session_scope() as db:
        role_map: dict[str, Role] = {r.code: r for r in db.scalars(select(Role))}
        for code, name, desc in ROLE_DEFINITIONS:
            if code.value not in role_map:
                role = Role(code=code.value, name=name, description=desc)
                db.add(role)
                db.flush()
                role_map[code.value] = role

        default_configs = {
            ConfigKey.SOCKET_HOST.value: settings.SOCKET_HOST,
            ConfigKey.SOCKET_PORT.value: str(settings.SOCKET_PORT),
            ConfigKey.API_HOST.value: settings.API_HOST,
            ConfigKey.API_PORT.value: str(settings.API_PORT),
        }
        for key, val in default_configs.items():
            if db.get(SystemConfig, key) is None:
                db.add(SystemConfig(key=key, value=val))

        existing_users = db.scalar(select(User.id).limit(1))
        if existing_users is None:
            for username, raw_pwd, full_name, email, phone, role_code in SEED_ACCOUNTS:
                db.add(
                    User(
                        username=username,
                        password_hash=hash_password(raw_pwd),
                        full_name=full_name,
                        email=email,
                        phone=phone,
                        role_id=role_map[role_code.value].id,
                        is_active=True,
                        must_change_password=False,
                    )
                )
            logger.info("Đã khởi tạo 7 vai trò và %d tài khoản mẫu mặc định.", len(SEED_ACCOUNTS))


def init_database() -> None:
    ensure_mysql_database()
    Base.metadata.create_all(bind=engine)
    seed_defaults()

