"""Dịch vụ quản trị mạng (1.4): cấu hình IP/Port, Khởi động/Dừng Socket Server, theo dõi kết nối."""
from datetime import datetime

from sqlalchemy.orm import Session

from server.core.config import settings
from server.core.constants import ConfigKey
from server.core.exceptions import BadRequestError, NotFoundError
from server.models import SystemConfig
from server.schemas.network import NetworkConfig
from server.socket_server.connection_manager import socket_manager
from server.socket_server.tcp_server import tcp_server


# ======================= 1.4.1 Cấu hình IP / Port =======================
def _read_all(db: Session) -> dict[str, str]:
    return {row.key: row.value for row in db.query(SystemConfig).all() if row.value is not None}


def get_config(db: Session) -> dict:
    rows = _read_all(db)
    return {
        "socket_host": rows.get(ConfigKey.SOCKET_HOST.value, settings.SOCKET_HOST),
        "socket_port": int(rows.get(ConfigKey.SOCKET_PORT.value, settings.SOCKET_PORT)),
        "api_host": rows.get(ConfigKey.API_HOST.value, settings.API_HOST),
        "api_port": int(rows.get(ConfigKey.API_PORT.value, settings.API_PORT)),
    }


def _upsert(db: Session, key: ConfigKey, value: str) -> None:
    row = db.get(SystemConfig, key.value)
    if row is None:
        db.add(SystemConfig(key=key.value, value=value))
    else:
        row.value = value


def save_config(db: Session, cfg: NetworkConfig) -> dict:
    if cfg.socket_port == cfg.api_port:
        raise BadRequestError("Port Socket Server phải khác Port REST API")
    old = get_config(db)
    _upsert(db, ConfigKey.SOCKET_HOST, cfg.socket_host)
    _upsert(db, ConfigKey.SOCKET_PORT, str(cfg.socket_port))
    _upsert(db, ConfigKey.API_HOST, cfg.api_host)
    _upsert(db, ConfigKey.API_PORT, str(cfg.api_port))
    db.commit()

    notes = ["Đã lưu cấu hình mạng."]
    socket_changed = tcp_server.is_running and (tcp_server.host, tcp_server.port) != (cfg.socket_host, cfg.socket_port)
    api_changed = (old["api_host"], old["api_port"]) != (cfg.api_host, cfg.api_port)
    if socket_changed:
        notes.append("Khởi động lại Socket Server để áp dụng IP/Port mới.")
    if api_changed:
        notes.append("IP/Port REST API mới sẽ có hiệu lực ở lần khởi động lại tiến trình Server tiếp theo.")
    return {**cfg.model_dump(), "message": " ".join(notes), "restart_required": socket_changed or api_changed}


# ================== 1.4.2 Khởi động / Dừng Socket Server ==================
async def start_server(db: Session) -> None:
    if tcp_server.is_running:
        raise BadRequestError("Socket Server đang chạy")
    cfg = get_config(db)
    try:
        await tcp_server.start(cfg["socket_host"], cfg["socket_port"])
    except OSError as exc:
        raise BadRequestError(
            f"Không thể mở cổng {cfg['socket_host']}:{cfg['socket_port']} - {exc.strerror or exc}"
        ) from exc


async def stop_server() -> None:
    if not tcp_server.is_running:
        raise BadRequestError("Socket Server đang dừng")
    await tcp_server.stop("Máy chủ Socket đã được quản trị viên dừng hoạt động")


async def restart_server(db: Session) -> None:
    if tcp_server.is_running:
        await tcp_server.stop("Máy chủ Socket đang khởi động lại, vui lòng chờ kết nối lại")
    await start_server(db)


def get_status(message: str | None = None) -> dict:
    totals = socket_manager.totals()
    return {
        **tcp_server.status(),
        "connection_count": totals["connection_count"],
        "authenticated_count": totals["authenticated_count"],
        "server_time": datetime.now(),
        "message": message,
    }


def get_socket_info(db: Session) -> dict:
    """Thông tin Socket trả về cho Client khi đăng nhập."""
    if tcp_server.is_running:
        host, port = tcp_server.host, tcp_server.port
    else:
        cfg = get_config(db)
        host, port = cfg["socket_host"], cfg["socket_port"]
    return {
        "host": host,
        "port": port,
        "running": tcp_server.is_running,
        "heartbeat_interval": settings.HEARTBEAT_INTERVAL,
        "heartbeat_timeout": settings.HEARTBEAT_TIMEOUT,
    }


# ================= 1.4.3 Theo dõi kết nối & băng thông =================
def get_connections() -> dict:
    totals = socket_manager.totals()
    return {
        "status": get_status(),
        "total_bytes_in": totals["total_bytes_in"],
        "total_bytes_out": totals["total_bytes_out"],
        "total_rate_in_bps": totals["total_rate_in_bps"],
        "total_rate_out_bps": totals["total_rate_out_bps"],
        "connections": socket_manager.snapshot(),
    }


async def kick_connection(connection_id: str) -> None:
    if not await socket_manager.kick(connection_id, "Kết nối đã bị quản trị viên ngắt"):
        raise NotFoundError("Kết nối không tồn tại hoặc đã đóng")
