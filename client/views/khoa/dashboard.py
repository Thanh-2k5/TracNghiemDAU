"""Khung làm việc của Khoa (tái sử dụng 1.1 & 1.2 theo mục 4.0)."""
from PySide6.QtWidgets import QWidget

from client.views.common.role_shell import ModulePlaceholderCard, RoleWorkspaceShell


class KhoaDashboardView(RoleWorkspaceShell):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("KHOA", "Khoa chuyên môn", parent)
        self.add_page(
            "4.1  Môn học / Học phần",
            "4.1. Quản lý môn học / học phần",
            ModulePlaceholderCard(
                "4.1",
                "Quản lý thông số học phần",
                "Thêm, sửa, xóa mã môn, tên môn, số tín chỉ, thời gian thi (4.1.1) và tìm kiếm môn học (4.1.2).",
                "Thành viên 3 (client/views/khoa/)",
            ),
        )
        self.add_page(
            "4.2  Chương kiến thức",
            "4.2. Quản lý chương kiến thức",
            ModulePlaceholderCard(
                "4.2",
                "Cấu trúc chương kiến thức",
                "Thêm, sửa, xóa và sắp xếp thứ tự chương thuộc từng học phần (4.2.1).",
                "Thành viên 3 (client/views/khoa/)",
            ),
        )
        self.add_page(
            "4.3  Ngân hàng câu hỏi",
            "4.3. Quản lý ngân hàng câu hỏi 7 dạng",
            ModulePlaceholderCard(
                "4.3",
                "Ngân hàng câu hỏi trắc nghiệm & Ma trận đề",
                "Quản lý 7 dạng câu hỏi (4.3.1), import Excel/Word (4.3.2), lập ma trận (4.3.3), lọc độ khó (4.3.4).",
                "Thành viên 3 (client/views/khoa/)",
            ),
        )
        self.add_shared_profile_page("4.0")

