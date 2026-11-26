"""Dịch vụ sao lưu & phục hồi dữ liệu (1.5.1) - xuất toàn bộ CSDL ra tệp .sql.

Viết thuần Python (không phụ thuộc mysqldump) để chạy được trên mọi máy có Python.
Hỗ trợ đầy đủ MySQL (chính thức) và SQLite (môi trường kiểm thử tự động).
"""
import re
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from server.core.config import settings
from server.core.exceptions import BadRequestError, NotFoundError
from server.database.db import engine

# Bảng phiên đăng nhập không sao lưu / không bị ghi đè khi phục hồi (giữ phiên Admin hiện tại)
EXCLUDED_TABLES = {"user_sessions"}
INSERT_BATCH = 200
SAFE_NAME_RE = re.compile(r"^[\w\-.]+\.sql$")
SKIP_PREFIXES = ("CREATE DATABASE", "USE ")
FORBIDDEN_PREFIXES = ("DROP DATABASE", "DROP SCHEMA", "CREATE USER", "DROP USER", "GRANT ", "REVOKE ")


def _dialect() -> str:
    name = engine.dialect.name
    if name not in ("mysql", "sqlite"):
        raise BadRequestError(f"Hệ quản trị CSDL '{name}' không hỗ trợ sao lưu .sql trực tiếp")
    return name


def backup_dir() -> Path:
    settings.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    return settings.BACKUP_DIR


def _unique_backup_path(prefix: str) -> Path:
    base = backup_dir()
    stamp = f"{datetime.now():%Y%m%d_%H%M%S}"
    candidate = base / f"{prefix}_{settings.DB_NAME}_{stamp}.sql"
    idx = 1
    while candidate.exists():
        candidate = base / f"{prefix}_{settings.DB_NAME}_{stamp}_{idx}.sql"
        idx += 1
    return candidate


def sql_literal(value: Any, dialect: str = "mysql") -> str:
    """Chuyển giá trị Python thành literal SQL an toàn."""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, Decimal)):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, datetime):
        return f"'{value.isoformat(sep=' ')}'"
    if isinstance(value, (date, time)):
        return f"'{value.isoformat()}'"
    if isinstance(value, timedelta):  # cột TIME của MySQL
        total = int(value.total_seconds())
        sign = "-" if total < 0 else ""
        total = abs(total)
        return f"'{sign}{total // 3600:02d}:{total % 3600 // 60:02d}:{total % 60:02d}'"
    if isinstance(value, (bytes, bytearray, memoryview)):
        raw = bytes(value)
        return f"X'{raw.hex()}'" if raw else "''"
    text = str(value)
    if dialect == "sqlite":
        return "'" + text.replace("'", "''") + "'"
    text = (text.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")
            .replace("\r", "\\r").replace("\x00", "\\0").replace("\x1a", "\\Z"))
    return f"'{text}'"


def split_sql_statements(script: str) -> list[str]:
    """Tách script SQL thành từng câu lệnh (xử lý chuỗi, backtick, comment)."""
    statements: list[str] = []
    buf: list[str] = []
    i, n = 0, len(script)
    quote: str | None = None
    while i < n:
        ch = script[i]
        nxt = script[i + 1] if i + 1 < n else ""
        if quote:
            buf.append(ch)
            if ch == "\\" and quote != "`" and i + 1 < n:
                buf.append(nxt)
                i += 2
                continue
            if ch == quote and nxt == quote and quote == "'":
                buf.append(nxt)
                i += 2
                continue
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in ("'", '"', "`"):
            quote = ch
            buf.append(ch)
        elif (ch == "-" and nxt == "-" and (i + 2 >= n or script[i + 2] in " \t\r\n")) or ch == "#":
            end = script.find("\n", i)
            i = n if end == -1 else end
            continue
        elif ch == "/" and nxt == "*":
            end = script.find("*/", i + 2)
            end = n if end == -1 else end + 2
            if i + 2 < n and script[i + 2] == "!":
                buf.append(script[i:end])
            i = end
            continue
        elif ch == ";":
            stmt = "".join(buf).strip()
            if stmt:
                statements.append(stmt)
            buf = []
        else:
            buf.append(ch)
        i += 1
    tail = "".join(buf).strip()
    if tail:
        statements.append(tail)
    return statements


def create_backup(prefix: str = "backup") -> Path:
    dialect = _dialect()
    path = _unique_backup_path(prefix)
    raw = engine.raw_connection()
    try:
        cur = raw.cursor()
        if dialect == "mysql":
            cur.execute("SHOW FULL TABLES WHERE Table_type = 'BASE TABLE'")
            tables = [row[0] for row in cur.fetchall()]
        else:
            cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
            tables = [row[0] for row in cur.fetchall()]

        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(f"-- Sao lưu CSDL `{settings.DB_NAME}` - Hệ thống thi trắc nghiệm DAU\n")
            f.write(f"-- Thời điểm: {datetime.now():%d/%m/%Y %H:%M:%S}\n\n")
            if dialect == "mysql":
                f.write("SET NAMES utf8mb4;\nSET FOREIGN_KEY_CHECKS=0;\n\n")
            else:
                f.write("PRAGMA foreign_keys=OFF;\n\n")

            for table in tables:
                if table in EXCLUDED_TABLES:
                    continue
                if dialect == "mysql":
                    cur.execute(f"SHOW CREATE TABLE `{table}`")
                    create_sql = cur.fetchone()[1]
                else:
                    cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,))
                    create_sql = cur.fetchone()[0]

                f.write(f"-- ----- Bảng `{table}` -----\nDROP TABLE IF EXISTS `{table}`;\n{create_sql};\n\n")
                cur.execute(f"SELECT * FROM `{table}`")
                columns = ", ".join(f"`{d[0]}`" for d in cur.description)
                if dialect == "mysql":
                    while True:
                        rows = cur.fetchmany(INSERT_BATCH)
                        if not rows:
                            break
                        values = ",\n".join(
                            "(" + ", ".join(sql_literal(v, dialect) for v in row) + ")" for row in rows
                        )
                        f.write(f"INSERT INTO `{table}` ({columns}) VALUES\n{values};\n")
                else:
                    for row in cur.fetchall():
                        vals = ", ".join(sql_literal(v, dialect) for v in row)
                        f.write(f"INSERT INTO `{table}` ({columns}) VALUES ({vals});\n")
                f.write("\n")

            if dialect == "mysql":
                f.write("SET FOREIGN_KEY_CHECKS=1;\n")
            else:
                f.write("PRAGMA foreign_keys=ON;\n")
    except Exception:
        path.unlink(missing_ok=True)
        raise
    finally:
        raw.close()
    return path


def list_backups() -> list[dict]:
    files = sorted(backup_dir().glob("*.sql"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [
        {"filename": p.name, "size_bytes": p.stat().st_size,
         "created_at": datetime.fromtimestamp(p.stat().st_mtime)}
        for p in files
    ]


def get_backup_path(filename: str) -> Path:
    if not SAFE_NAME_RE.match(filename):
        raise BadRequestError("Tên tệp sao lưu không hợp lệ")
    path = (backup_dir() / filename).resolve()
    if path.parent != backup_dir().resolve() or not path.is_file():
        raise NotFoundError("Không tìm thấy tệp sao lưu")
    return path


def delete_backup(filename: str) -> None:
    get_backup_path(filename).unlink()


def restore_from_text(script: str) -> tuple[int, str]:
    """Phục hồi CSDL từ nội dung .sql. Tự tạo bản sao lưu an toàn trước khi ghi đè."""
    dialect = _dialect()
    statements = []
    for stmt in split_sql_statements(script):
        upper = stmt.lstrip().upper()
        if upper.startswith(FORBIDDEN_PREFIXES):
            raise BadRequestError(f"Tệp phục hồi chứa câu lệnh không được phép: {stmt[:60]}...")
        if upper.startswith(SKIP_PREFIXES):
            continue
        if dialect == "sqlite" and upper.startswith("SET "):
            continue
        if dialect == "mysql" and upper.startswith("PRAGMA "):
            continue
        if any(f"`{t}`" in stmt[:200] or f" {t} " in stmt[:200] for t in EXCLUDED_TABLES) and upper.startswith(
            ("DROP", "CREATE", "INSERT")
        ):
            continue
        statements.append(stmt)
    if not any(s.lstrip().upper().startswith(("CREATE TABLE", "INSERT")) for s in statements):
        raise BadRequestError("Tệp sao lưu rỗng hoặc không đúng định dạng")

    safety = create_backup(prefix="pre_restore")
    raw = engine.raw_connection()
    try:
        cur = raw.cursor()
        cur.execute("SET FOREIGN_KEY_CHECKS=0" if dialect == "mysql" else "PRAGMA foreign_keys=OFF")
        for index, stmt in enumerate(statements, start=1):
            try:
                cur.execute(stmt)
            except Exception as exc:  # noqa: BLE001
                raw.rollback()
                raise BadRequestError(
                    f"Lỗi tại câu lệnh thứ {index}: {exc}. "
                    f"Dữ liệu trước khi phục hồi đã được lưu tại '{safety.name}'."
                ) from exc
        raw.commit()
    finally:
        try:
            cur = raw.cursor()
            cur.execute("SET FOREIGN_KEY_CHECKS=1" if dialect == "mysql" else "PRAGMA foreign_keys=ON")
        except Exception:  # noqa: BLE001
            pass
        raw.close()
    engine.dispose()
    return len(statements), safety.name


def restore_from_file(filename: str) -> tuple[int, str]:
    path = get_backup_path(filename)
    return restore_from_text(path.read_text(encoding="utf-8"))
