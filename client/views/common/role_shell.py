"""Khung giao diện làm việc chuẩn (Sidebar + Topbar trạng thái Socket + Vùng nội dung) cho cả 7 tác nhân."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from client.models.user_model import UserProfile, session_state
from client.views.common.profile_view import ChangePasswordDialog, ProfileView
from client.views.styles import ROLE_ACCENT_COLORS


class ModulePlaceholderCard(QWidget):
    """Widget khung chờ sẵn cho các thành viên 2, 3, 4, 5 triển khai nghiệp vụ riêng."""

    def __init__(self, code: str, title: str, description: str, owner_hint: str) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        card = QFrame()
        card.setObjectName("Card")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(28, 28, 28, 28)
        cl.setSpacing(10)

        badge = QLabel(f"MODULE {code}")
        badge.setStyleSheet("font-size: 12px; font-weight: 700; color: #2563eb;")
        head = QLabel(title)
        head.setObjectName("PageTitle")
        desc = QLabel(description)
        desc.setWordWrap(True)
        hint = QLabel(f"Phân công triển khai: {owner_hint}")
        hint.setObjectName("MutedText")

        cl.addWidget(badge)
        cl.addWidget(head)
        cl.addWidget(desc)
        cl.addSpacing(8)
        cl.addWidget(hint)
        cl.addStretch()

        layout.addWidget(card)
        layout.addStretch()


class RoleWorkspaceShell(QWidget):
    """Khung làm việc tái sử dụng cho 7 vai trò (tích hợp sẵn 1.1.2 Đăng xuất, 1.2 Hồ sơ & Heartbeat)."""

    logout_requested = Signal()

    def __init__(self, role_code: str, role_title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.role_code = role_code
        self.role_title = role_title
        self._nav_buttons: list[QPushButton] = []
        self._page_titles: list[str] = []
        self._btn_group = QButtonGroup(self)
        self._btn_group.setExclusive(True)

        self._build_shell()
        session_state.user_changed.connect(self._update_user_banner)
        session_state.socket_state_changed.connect(self._update_socket_badge)
        if session_state.user:
            self._update_user_banner(session_state.user)
        self._update_socket_badge(session_state.socket_online, session_state.latency_ms)

    def _build_shell(self) -> None:
        accent = ROLE_ACCENT_COLORS.get(self.role_code, "#1e293b")
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---------------- Sidebar trái ----------------
        sidebar = QFrame()
        sidebar.setFixedWidth(255)
        sidebar.setStyleSheet("QFrame { background-color: #0f172a; color: #f8fafc; }")
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(14, 16, 14, 16)
        sb_layout.setSpacing(8)

        brand = QFrame()
        brand.setStyleSheet(
            f"QFrame {{ background-color: {accent}; border-radius: 8px; padding: 10px; }}"
        )
        bl = QVBoxLayout(brand)
        bl.setContentsMargins(10, 8, 10, 8)
        bl.setSpacing(2)
        app_lbl = QLabel("TRẮC NGHIỆM DAU")
        app_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #ffffff; background: transparent;")
        role_lbl = QLabel(self.role_title)
        role_lbl.setWordWrap(True)
        role_lbl.setStyleSheet("font-size: 15px; font-weight: 800; color: #ffffff; background: transparent;")
        bl.addWidget(app_lbl)
        bl.addWidget(role_lbl)
        sb_layout.addWidget(brand)
        sb_layout.addSpacing(8)

        self.nav_container = QVBoxLayout()
        self.nav_container.setSpacing(4)
        sb_layout.addLayout(self.nav_container)
        sb_layout.addStretch()

        pwd_btn = QPushButton("Đổi mật khẩu (1.2.2)")
        pwd_btn.setStyleSheet(
            "QPushButton { background-color: #1e293b; color: #e2e8f0; border: 1px solid #334155;"
            "text-align: left; padding: 8px 12px; border-radius: 6px; }"
            "QPushButton:hover { background-color: #334155; }"
        )
        pwd_btn.clicked.connect(lambda: ChangePasswordDialog(self, mandatory=False).exec())
        sb_layout.addWidget(pwd_btn)

        logout_btn = QPushButton("Đăng xuất & Đóng Socket (1.1.2)")
        logout_btn.setObjectName("DangerBtn")
        logout_btn.clicked.connect(self._confirm_logout)
        sb_layout.addWidget(logout_btn)

        # ---------------- Khu vực phải (Topbar + Stacked Pages) ----------------
        right_panel = QWidget()
        rp_layout = QVBoxLayout(right_panel)
        rp_layout.setContentsMargins(0, 0, 0, 0)
        rp_layout.setSpacing(0)

        topbar = QFrame()
        topbar.setFixedHeight(58)
        topbar.setStyleSheet(
            "QFrame { background-color: #ffffff; border-bottom: 1px solid #e2e8f0; }"
        )
        tb_layout = QHBoxLayout(topbar)
        tb_layout.setContentsMargins(20, 0, 20, 0)

        self.current_page_lbl = QLabel("")
        self.current_page_lbl.setStyleSheet("font-size: 15px; font-weight: 700; color: #0f172a;")

        self.socket_badge = QLabel("Socket: Offline")
        self.user_badge = QLabel("")
        self.user_badge.setStyleSheet("font-weight: 600; color: #334155;")

        tb_layout.addWidget(self.current_page_lbl)
        tb_layout.addStretch()
        tb_layout.addWidget(self.socket_badge)
        tb_layout.addSpacing(12)
        tb_layout.addWidget(self.user_badge)

        self.stack = QStackedWidget()
        rp_layout.addWidget(topbar)
        rp_layout.addWidget(self.stack, 1)

        root.addWidget(sidebar)
        root.addWidget(right_panel, 1)

    def add_page(self, nav_label: str, page_title: str, widget: QWidget) -> int:
        index = self.stack.addWidget(widget)
        self._page_titles.append(page_title)

        btn = QPushButton(nav_label)
        btn.setCheckable(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            "QPushButton { background-color: transparent; color: #cbd5e1; border: none;"
            "text-align: left; padding: 9px 12px; border-radius: 6px; font-weight: 600; }"
            "QPushButton:hover { background-color: #1e293b; color: #ffffff; }"
            "QPushButton:checked { background-color: #2563eb; color: #ffffff; }"
        )
        btn.clicked.connect(lambda _checked=False, idx=index: self.switch_page(idx))
        self._btn_group.addButton(btn, index)
        self._nav_buttons.append(btn)
        self.nav_container.addWidget(btn)

        if index == 0:
            btn.setChecked(True)
            self.current_page_lbl.setText(page_title)
        return index

    def add_shared_profile_page(self, code_label: str = "1.2") -> int:
        """Thêm trang Thông tin cá nhân & Đổi mật khẩu dùng chung vào cuối menu."""
        return self.add_page(
            f"{code_label}  Thông tin cá nhân",
            f"{code_label}. Thông tin cá nhân & Đổi mật khẩu",
            ProfileView(),
        )

    def switch_page(self, index: int) -> None:
        if 0 <= index < self.stack.count():
            self.stack.setCurrentIndex(index)
            self.current_page_lbl.setText(self._page_titles[index])
            self._nav_buttons[index].setChecked(True)

    def _update_user_banner(self, user: UserProfile | None) -> None:
        if user is None:
            self.user_badge.setText("")
        else:
            self.user_badge.setText(f"{user.full_name} ({user.username})")

    def _update_socket_badge(self, online: bool, latency_ms: float | None) -> None:
        if online:
            ping_txt = f" • {latency_ms:.1f} ms" if latency_ms is not None else ""
            self.socket_badge.setText(f"● Socket Online{ping_txt}")
            self.socket_badge.setStyleSheet(
                "background-color: #dcfce7; color: #15803d; font-weight: 700;"
                "padding: 4px 10px; border-radius: 12px; font-size: 12px;"
            )
        else:
            self.socket_badge.setText("○ Socket Đang kết nối...")
            self.socket_badge.setStyleSheet(
                "background-color: #fef3c7; color: #b45309; font-weight: 700;"
                "padding: 4px 10px; border-radius: 12px; font-size: 12px;"
            )

    def _confirm_logout(self) -> None:
        ans = QMessageBox.question(
            self,
            "Xác nhận đăng xuất (1.1.2)",
            "Bạn có chắc chắn muốn đăng xuất và đóng kết nối Socket hiện tại không?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if ans == QMessageBox.Yes:
            self.logout_requested.emit()

