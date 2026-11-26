"""Khung làm việc của Sinh viên dự thi (tái sử dụng 1.1, 1.2 & lõi Socket Heartbeat)."""
from PySide6.QtWidgets import QWidget

from client.views.common.role_shell import ModulePlaceholderCard, RoleWorkspaceShell


class SinhVienDashboardView(RoleWorkspaceShell):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("SINHVIEN", "Sinh viên dự thi", parent)
        self.add_page(
            "7.1 - 7.2  Lịch thi & Phòng chờ",
            "7.1 - 7.2. Tra cứu lịch thi cá nhân & Phòng chờ trực tuyến",
            ModulePlaceholderCard(
                "7.1 - 7.2",
                "Lịch thi cá nhân & Kết nối phòng chờ",
                "Xem ca thi, phòng thi (7.1.1); vào phòng chờ kiểm tra kết nối Server và nhận thông báo (7.2.1).",
                "Thành viên 5 (client/views/sinhvien/)",
            ),
        )
        self.add_page(
            "7.3 - 7.5  Làm bài & Kết quả",
            "7.3 - 7.5. Làm bài thi trực tuyến, Auto-save & Xem kết quả",
            ModulePlaceholderCard(
                "7.3 - 7.5",
                "Làm bài trắc nghiệm, tự động lưu & chấm điểm",
                "Nhận đề JSON, đồng hồ đếm ngược đồng bộ Server (7.3), Auto-save & khôi phục khi rớt mạng (7.4), "
                "nộp bài và xem điểm ngay (7.5) trên nền `realtime_socket`.",
                "Thành viên 5 (client/views/sinhvien/)",
            ),
        )
        self.add_shared_profile_page("7.0")

