"""Entry point ứng dụng Desktop Client (PySide6 - MVC) cho Hệ thống thi trắc nghiệm DAU."""
import sys
from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QApplication, QDialog, QMainWindow, QMessageBox, QStackedWidget, QWidget

from client.api.http_client import api_client
from client.controllers.auth_controller import auth_controller
from client.models.user_model import UserProfile, session_state
from client.socket_client.tcp_client import realtime_socket
from client.views.admin.admin_dashboard import AdminDashboardView
from client.views.coithi.dashboard import CoiThiDashboardView
from client.views.common.login_view import LoginView
from client.views.common.profile_view import ChangePasswordDialog
from client.views.common.role_shell import RoleWorkspaceShell
from client.views.ctsv.dashboard import CTSVDashboardView
from client.views.daotao.dashboard import DaoTaoDashboardView
from client.views.khaothi.dashboard import KhaoThiDashboardView
from client.views.khoa.dashboard import KhoaDashboardView
from client.views.sinhvien.dashboard import SinhVienDashboardView
from client.views.styles import APP_STYLESHEET

ROLE_VIEW_FACTORY: dict[str, type[RoleWorkspaceShell]] = {
    "ADMIN": AdminDashboardView,
    "CTSV": CTSVDashboardView,
    "DAOTAO": DaoTaoDashboardView,
    "KHOA": KhoaDashboardView,
    "KHAOTHI": KhaoThiDashboardView,
    "COITHI": CoiThiDashboardView,
    "SINHVIEN": SinhVienDashboardView,
}


class MainWindow(QMainWindow):
    """Cửa sổ chính điều hướng Đăng nhập <-> Không gian làm việc theo đúng vai trò (7 tác nhân)."""

    _unauthorized_signal = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Hệ Thống Thi Trắc Nghiệm Trực Tuyến DAU")
        self.resize(1220, 760)
        self.setMinimumSize(980, 640)

        self._active_workspace: Optional[QWidget] = None
        self._handling_forced_logout = False

        self.stack = QStackedWidget()
        self.stack.setObjectName("AppRoot")
        self.setCentralWidget(self.stack)

        self.login_view = LoginView()
        self.login_view.login_succeeded.connect(self._enter_role_workspace)
        self.stack.addWidget(self.login_view)

        # Nhận cảnh báo cưỡng chế đăng xuất từ cả kênh Socket và kênh REST 401
        realtime_socket.force_logged_out.connect(self._on_forced_logout)
        self._unauthorized_signal.connect(self._on_forced_logout)
        api_client.on_unauthorized = self._unauthorized_signal.emit

    def _enter_role_workspace(self, user: UserProfile) -> None:
        # Nếu tài khoản vừa reset mật khẩu hoặc tạo mới bằng mật khẩu mặc định -> yêu cầu đổi ngay
        if user.must_change_password:
            dlg = ChangePasswordDialog(self, mandatory=True)
            if dlg.exec() != QDialog.Accepted:
                auth_controller.logout()
                self.login_view.reset_form()
                return

        self._dispose_workspace()
        view_cls = ROLE_VIEW_FACTORY.get(user.role_code, SinhVienDashboardView)
        workspace = view_cls(self)
        workspace.logout_requested.connect(self._perform_logout)

        self._active_workspace = workspace
        self.stack.addWidget(workspace)
        self.stack.setCurrentWidget(workspace)
        self.setWindowTitle(
            f"Hệ Thống Thi Trắc Nghiệm DAU — {user.role_name} [{user.full_name}]"
        )

    def _dispose_workspace(self) -> None:
        if self._active_workspace is not None:
            self.stack.removeWidget(self._active_workspace)
            self._active_workspace.deleteLater()
            self._active_workspace = None

    def _perform_logout(self) -> None:
        auth_controller.logout()
        self._dispose_workspace()
        self.login_view.reset_form()
        self.stack.setCurrentWidget(self.login_view)
        self.setWindowTitle("Hệ Thống Thi Trắc Nghiệm Trực Tuyến DAU")

    def _on_forced_logout(self, reason: str) -> None:
        if self._handling_forced_logout or not session_state.is_authenticated:
            return
        self._handling_forced_logout = True
        try:
            auth_controller.clear_forced_session()
            self._dispose_workspace()
            self.login_view.reset_form()
            self.stack.setCurrentWidget(self.login_view)
            self.setWindowTitle("Hệ Thống Thi Trắc Nghiệm Trực Tuyến DAU")
            QMessageBox.warning(
                self,
                "Phiên đăng nhập đã kết thúc",
                reason or "Phiên làm việc của bạn đã bị đóng từ máy chủ.",
            )
        finally:
            self._handling_forced_logout = False

    def closeEvent(self, event) -> None:  # noqa: N802
        """Đảm bảo đóng kết nối Socket và hủy phiên an toàn khi tắt cửa sổ ứng dụng."""
        if session_state.is_authenticated:
            auth_controller.logout()
        super().closeEvent(event)


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLESHEET)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
