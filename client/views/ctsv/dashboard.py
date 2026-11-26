"""Khung làm việc của Phòng Công tác Sinh viên (tái sử dụng 1.1 & 1.2 theo mục 2.0)."""
from PySide6.QtWidgets import QWidget

from client.views.common.role_shell import ModulePlaceholderCard, RoleWorkspaceShell


class CTSVDashboardView(RoleWorkspaceShell):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("CTSV", "Phòng Công tác Sinh viên", parent)
        self.add_page(
            "2.1  Hồ sơ & Trạng thái SV",
            "2.1. Quản lý hồ sơ và trạng thái học tập sinh viên",
            ModulePlaceholderCard(
                "2.1",
                "Quản lý hồ sơ và trạng thái sinh viên",
                "Quản lý khóa/ngành/lớp; thêm, sửa, khóa tài khoản, cập nhật trạng thái học tập "
                "(Đang học / Bảo lưu / Đình chỉ thi - 2.1.1); nhập Excel (2.1.2); tìm kiếm & lọc SV (2.1.4).",
                "Thành viên 2 (client/views/ctsv/)",
            ),
        )
        self.add_shared_profile_page("2.0")

