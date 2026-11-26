"""Khung làm việc của Cán bộ coi thi (tái sử dụng 1.1, 1.2 & lõi Socket Heartbeat)."""
from PySide6.QtWidgets import QWidget

from client.views.common.role_shell import ModulePlaceholderCard, RoleWorkspaceShell


class CoiThiDashboardView(RoleWorkspaceShell):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("COITHI", "Cán bộ Coi thi", parent)
        self.add_page(
            "6.1 - 6.2  Phòng thi & Điểm danh",
            "6.1 - 6.2. Phòng thi phụ trách & Điểm danh phòng chờ",
            ModulePlaceholderCard(
                "6.1 - 6.2",
                "Quản lý phòng thi được phân công & Điểm danh thí sinh",
                "Kiểm tra sĩ số Tổng/Có mặt/Vắng (6.1.1) và cập nhật điểm danh phòng chờ trực tuyến (6.2.1).",
                "Thành viên 4 (client/views/coithi/)",
            ),
        )
        self.add_page(
            "6.3 - 6.5  Điều khiển & Giám sát",
            "6.3 - 6.5. Điều khiển kỳ thi & Giám sát thời gian thực qua Socket",
            ModulePlaceholderCard(
                "6.3 - 6.5",
                "Điều khiển ca thi, Giám sát Heartbeat & Xử lý sự cố",
                "Phát đề đồng loạt, cộng giờ bù, thu bài (6.3); theo dõi tiến độ & rớt mạng (6.4); "
                "duyệt Reconnect & lập biên bản vi phạm (6.5) trên nền `realtime_socket`.",
                "Thành viên 5 (client/views/coithi/)",
            ),
        )
        self.add_shared_profile_page("6.0")

