"""Trang làm việc tổng hợp của tác nhân Admin (kết hợp 1.2, 1.3, 1.4, 1.5)."""
from PySide6.QtWidgets import QWidget

from client.views.admin.account_management_view import AccountManagementView
from client.views.admin.backup_restore_view import BackupRestoreView
from client.views.admin.network_management_view import NetworkManagementView
from client.views.common.role_shell import RoleWorkspaceShell


class AdminDashboardView(RoleWorkspaceShell):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("ADMIN", "Quản trị hệ thống (Admin)", parent)
        self.account_view = AccountManagementView()
        self.network_view = NetworkManagementView()
        self.backup_view = BackupRestoreView()

        self.add_page("1.3  Quản lý tài khoản", "1.3. Quản lý tài khoản & Phân quyền 7 tác nhân", self.account_view)
        self.add_page("1.4  Quản trị mạng", "1.4. Quản trị mạng & Giám sát Socket thời gian thực", self.network_view)
        self.add_page("1.5  Dữ liệu & Vận hành", "1.5. Sao lưu & Phục hồi cơ sở dữ liệu (.sql)", self.backup_view)
        self.add_shared_profile_page("1.2")

