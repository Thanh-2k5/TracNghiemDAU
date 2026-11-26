"""Hằng số dùng chung toàn hệ thống: mã vai trò (7 nhóm tác nhân), khóa cấu hình."""
from enum import Enum


class RoleCode(str, Enum):
    ADMIN = "ADMIN"
    CTSV = "CTSV"
    DAOTAO = "DAOTAO"
    KHOA = "KHOA"
    KHAOTHI = "KHAOTHI"
    COITHI = "COITHI"
    SINHVIEN = "SINHVIEN"


ROLE_DEFINITIONS = [
    (RoleCode.ADMIN, "Quản trị hệ thống", "Quản lý tài khoản, phân quyền, mạng và dữ liệu hệ thống"),
    (RoleCode.CTSV, "Phòng Công tác Sinh viên", "Quản lý hồ sơ và trạng thái học tập sinh viên"),
    (RoleCode.DAOTAO, "Phòng Đào tạo", "Xét điều kiện và lập danh sách dự thi"),
    (RoleCode.KHOA, "Khoa", "Quản lý học phần, chương kiến thức và ngân hàng câu hỏi"),
    (RoleCode.KHAOTHI, "Phòng Khảo thí", "Tổ chức kỳ thi, ca thi, phòng thi, sinh đề và kết quả"),
    (RoleCode.COITHI, "Cán bộ coi thi", "Điều khiển và giám sát phòng thi thời gian thực"),
    (RoleCode.SINHVIEN, "Sinh viên", "Tham gia thi trắc nghiệm trực tuyến"),
]

ROLE_NAMES = {code.value: name for code, name, _ in ROLE_DEFINITIONS}


class ConfigKey(str, Enum):
    """Khóa lưu trong bảng system_configs."""
    SOCKET_HOST = "network.socket_host"
    SOCKET_PORT = "network.socket_port"
    API_HOST = "network.api_host"
    API_PORT = "network.api_port"

