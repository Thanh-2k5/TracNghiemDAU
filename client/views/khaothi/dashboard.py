"""Khung làm việc của Phòng Khảo thí (tái sử dụng 1.1 & 1.2 theo mục 5.0)."""
from PySide6.QtWidgets import QWidget

from client.views.common.role_shell import ModulePlaceholderCard, RoleWorkspaceShell


class KhaoThiDashboardView(RoleWorkspaceShell):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("KHAOTHI", "Phòng Khảo thí", parent)
        self.add_page(
            "5.1 - 5.4  Tổ chức thi",
            "5.1 - 5.4. Quản lý kỳ thi, ca thi, phòng thi & xếp lịch",
            ModulePlaceholderCard(
                "5.1 - 5.4",
                "Quản lý kỳ thi, ca thi, phòng thi & phân công coi thi",
                "Thiết lập đợt thi, ca thi, phòng thi trực tuyến, gán thí sinh và phân công cán bộ coi thi.",
                "Thành viên 4 (client/views/khaothi/)",
            ),
        )
        self.add_page(
            "5.5  Sinh đề tự động",
            "5.5. Thiết lập ma trận & Sinh đề tự động",
            ModulePlaceholderCard(
                "5.5",
                "Sinh mã đề tự động theo ma trận",
                "Bốc ngẫu nhiên câu hỏi theo ma trận, trộn câu hỏi và đáp án cho từng mã đề (5.5.1 - 5.5.2).",
                "Thành viên 4 (client/views/khaothi/)",
            ),
        )
        self.add_page(
            "5.6  Thống kê kết quả",
            "5.6. Quản lý & thống kê kết quả thi",
            ModulePlaceholderCard(
                "5.6",
                "Tra cứu điểm thi, phổ điểm & Xuất báo cáo Excel/PDF",
                "Xem lịch sử chọn đáp án, thống kê phổ điểm và xuất bảng điểm chính thức (5.6.1).",
                "Thành viên 5 (client/views/khaothi/)",
            ),
        )
        self.add_shared_profile_page("5.0")

