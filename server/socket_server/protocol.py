"""Giao thức gói tin Socket dùng chung toàn hệ thống.

Mỗi gói tin là 1 đối tượng JSON (UTF-8) kết thúc bằng ký tự xuống dòng '\\n':

    {"type": "<loại gói>", "data": {...}, "ts": <unix time>, "id": "<tùy chọn>"}

Luồng chuẩn:
    Client -> auth {token}            Server -> auth_ok {connection_id, server_time, heartbeat_interval}
    Client -> heartbeat {client_ts}   Server -> heartbeat_ack {client_ts, server_time}
    Server -> force_logout {reason}   (bị đăng nhập nơi khác / tài khoản bị khóa ...)
    Client -> logout                  Server đóng kết nối an toàn

Các module khác (Phòng thi, Coi thi, Sinh viên...) chỉ cần định nghĩa thêm "type" mới
và đăng ký handler qua socket_manager.register_handler("exam.start", handler).
"""
import json
import time
from typing import Any, Optional

ENCODING = "utf-8"
DELIMITER = b"\n"


class PacketType:
    AUTH = "auth"
    AUTH_OK = "auth_ok"
    AUTH_FAIL = "auth_fail"
    HEARTBEAT = "heartbeat"
    HEARTBEAT_ACK = "heartbeat_ack"
    LOGOUT = "logout"
    FORCE_LOGOUT = "force_logout"
    KICKED = "kicked"
    SERVER_SHUTDOWN = "server_shutdown"
    NOTIFY = "notify"
    ERROR = "error"


class ProtocolError(ValueError):
    """Gói tin sai định dạng."""


def make_packet(ptype: str, data: Optional[dict[str, Any]] = None, request_id: Optional[str] = None) -> dict:
    packet: dict[str, Any] = {"type": ptype, "data": data or {}, "ts": time.time()}
    if request_id:
        packet["id"] = request_id
    return packet


def encode_packet(packet: dict) -> bytes:
    text = json.dumps(packet, ensure_ascii=False, separators=(",", ":"), default=str)
    return text.encode(ENCODING) + DELIMITER


def decode_packet(raw: bytes | str) -> dict:
    try:
        text = raw.decode(ENCODING) if isinstance(raw, (bytes, bytearray)) else raw
        obj = json.loads(text.strip())
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError("Gói tin không phải JSON hợp lệ") from exc
    if not isinstance(obj, dict) or not isinstance(obj.get("type"), str) or not obj["type"]:
        raise ProtocolError("Gói tin thiếu trường 'type'")
    data = obj.get("data")
    if data is None:
        obj["data"] = {}
    elif not isinstance(data, dict):
        raise ProtocolError("Trường 'data' phải là đối tượng JSON")
    return obj

