"""Khung làm việc của Phòng Đào tạo (tái sử dụng 1.1 & 1.2 theo mục 3.0)."""
from PySide6.QtWidgets import QWidget

from client.views.common.role_shell import ModulePlaceholderCard, RoleWorkspaceShell


class DaoTaoDashboardView(RoleWorkspaceShell):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("DAOTAO", "Phòng Đào tạo", parent)
        self.add_page(
            "3.1  Danh sách sinh viên",
            "3.1. Quản lý danh sách sinh viên",
            ModulePlaceholderCard(
                "3.1",
                "Xem, tìm kiếm và lọc danh sách sinh viên",
                "Phục vụ xét duyệt điều kiện dự thi (3.1.1 - tái sử dụng bộ lọc 2.1.4).",
                "Thành viên 2 (client/views/daotao/)",
            ),
        )
        self.add_page(
            "3.2  Kiểm tra điều kiện thi",
            "3.2. Kiểm tra điều kiện dự thi",
            ModulePlaceholderCard(
                "3.2",
                "Đối chiếu tự động điều kiện dự thi",
                "Đối chiếu trạng thái học tập, đăng ký tín chỉ, điểm quá trình, học phí (3.2.1).",
                "Thành viên 2 (client/views/daotao/)",
            ),
        )
        self.add_page(
            "3.3  Danh sách dự thi",
            "3.3. Lập & phê duyệt danh sách dự thi",
            ModulePlaceholderCard(
                "3.3 - 3.4",
                "Lập, chốt danh sách dự thi & Xuất báo cáo Excel",
                "Gán sinh viên vào kỳ thi, chốt khóa danh sách chính thức (3.3.1) và xuất tệp .xlsx (3.4.1).",
                "Thành viên 2 (client/views/daotao/)",
            ),
        )
        self.add_shared_profile_page("3.0")

