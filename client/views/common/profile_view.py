"""Giao diện Thông tin cá nhân (1.2.1) & Đổi mật khẩu (1.2.2) tái sử dụng cho cả 7 tác nhân."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from client.api.http_client import APIError
from client.controllers.auth_controller import profile_controller
from client.models.user_model import UserProfile, session_state


class ChangePasswordDialog(QDialog):
    """1.2.2 - Hộp thoại đổi mật khẩu dùng chung (hỗ trợ chế độ bắt buộc đổi mật khẩu mặc định)."""

    def __init__(self, parent: QWidget | None = None, mandatory: bool = False) -> None:
        super().__init__(parent)
        self.mandatory = mandatory
        self.setWindowTitle(
            "Bắt buộc đổi mật khẩu mặc định" if mandatory else "Đổi mật khẩu tài khoản (1.2.2)"
        )
        self.setModal(True)
        self.setMinimumWidth(410)
        if mandatory:
            self.setWindowFlag(Qt.WindowCloseButtonHint, False)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        if mandatory:
            banner = QLabel(
                "Tài khoản của bạn đang sử dụng mật khẩu mặc định hoặc vừa được quản trị viên "
                "đặt lại mật khẩu. Vui lòng đổi mật khẩu mới để tiếp tục làm việc."
            )
            banner.setWordWrap(True)
            banner.setStyleSheet(
                "background-color: #fffbeb; color: #92400e; border: 1px solid #fde68a;"
                "border-radius: 6px; padding: 8px;"
            )
            layout.addWidget(banner)

        form = QFormLayout()
        self.old_pwd_edit = QLineEdit()
        self.old_pwd_edit.setEchoMode(QLineEdit.Password)
        self.old_pwd_edit.setPlaceholderText("Nhập mật khẩu hiện tại...")

        self.new_pwd_edit = QLineEdit()
        self.new_pwd_edit.setEchoMode(QLineEdit.Password)
        self.new_pwd_edit.setPlaceholderText("Từ 6 đến 64 ký tự, khác mật khẩu cũ...")

        self.confirm_pwd_edit = QLineEdit()
        self.confirm_pwd_edit.setEchoMode(QLineEdit.Password)
        self.confirm_pwd_edit.setPlaceholderText("Nhập lại mật khẩu mới...")

        form.addRow("Mật khẩu cũ (*):", self.old_pwd_edit)
        form.addRow("Mật khẩu mới (*):", self.new_pwd_edit)
        form.addRow("Xác nhận mật khẩu (*):", self.confirm_pwd_edit)
        layout.addLayout(form)

        show_cb = QCheckBox("Hiện mật khẩu")
        show_cb.toggled.connect(self._toggle_echo)
        layout.addWidget(show_cb)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        if not mandatory:
            cancel_btn = QPushButton("Hủy")
            cancel_btn.clicked.connect(self.reject)
            btn_row.addWidget(cancel_btn)
        else:
            logout_btn = QPushButton("Đăng xuất")
            logout_btn.clicked.connect(self.reject)
            btn_row.addWidget(logout_btn)

        save_btn = QPushButton("Cập nhật mật khẩu")
        save_btn.setObjectName("PrimaryBtn")
        save_btn.clicked.connect(self._submit)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _toggle_echo(self, show: bool) -> None:
        mode = QLineEdit.Normal if show else QLineEdit.Password
        for edit in (self.old_pwd_edit, self.new_pwd_edit, self.confirm_pwd_edit):
            edit.setEchoMode(mode)

    def _submit(self) -> None:
        old_p = self.old_pwd_edit.text()
        new_p = self.new_pwd_edit.text()
        cfm_p = self.confirm_pwd_edit.text()
        if not old_p or not new_p or not cfm_p:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập đầy đủ cả 3 trường mật khẩu.")
            return
        try:
            msg = profile_controller.change_password(old_p, new_p, cfm_p)
            QMessageBox.information(self, "Thành công", msg)
            self.accept()
        except APIError as err:
            QMessageBox.critical(self, "Không thể đổi mật khẩu", err.message)


class ProfileView(QWidget):
    """1.2.1 & 1.2.2 - Trang xem/cập nhật hồ sơ cá nhân & đổi mật khẩu dùng chung cho 7 phân hệ."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()
        session_state.user_changed.connect(self._populate_from_user)
        if session_state.user:
            self._populate_from_user(session_state.user)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("Thông tin cá nhân & Bảo mật tài khoản")
        title.setObjectName("PageTitle")
        refresh_btn = QPushButton("Tải lại từ Server")
        refresh_btn.clicked.connect(self.reload_profile)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(refresh_btn)
        root.addLayout(header)

        content_row = QHBoxLayout()
        content_row.setSpacing(16)

        # --- Cột trái: Xem & cập nhật hồ sơ (1.2.1) ---
        info_card = QFrame()
        info_card.setObjectName("Card")
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(22, 20, 22, 20)
        info_layout.setSpacing(12)

        sec1 = QLabel("1.2.1. Hồ sơ tài khoản")
        sec1.setObjectName("SectionTitle")
        info_layout.addWidget(sec1)

        form = QFormLayout()
        form.setSpacing(10)

        self.username_lbl = QLabel("-")
        self.username_lbl.setStyleSheet("font-weight: 700; color: #1e293b;")
        self.role_lbl = QLabel("-")
        self.role_lbl.setStyleSheet("font-weight: 700; color: #1d4ed8;")
        self.last_login_lbl = QLabel("-")
        self.last_login_lbl.setObjectName("MutedText")

        self.full_name_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("vd: hoten@dau.edu.vn")
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("vd: 0905123456")

        form.addRow("Tên đăng nhập:", self.username_lbl)
        form.addRow("Vai trò hệ thống:", self.role_lbl)
        form.addRow("Đăng nhập gần nhất:", self.last_login_lbl)
        form.addRow("Họ và tên (*):", self.full_name_edit)
        form.addRow("Email:", self.email_edit)
        form.addRow("Số điện thoại:", self.phone_edit)
        info_layout.addLayout(form)

        save_row = QHBoxLayout()
        save_row.addStretch()
        self.save_btn = QPushButton("Lưu thông tin cá nhân")
        self.save_btn.setObjectName("PrimaryBtn")
        self.save_btn.clicked.connect(self._save_profile)
        save_row.addWidget(self.save_btn)
        info_layout.addLayout(save_row)
        info_layout.addStretch()

        # --- Cột phải: Đổi mật khẩu (1.2.2) ---
        sec_card = QFrame()
        sec_card.setObjectName("Card")
        sec_layout = QVBoxLayout(sec_card)
        sec_layout.setContentsMargins(22, 20, 22, 20)
        sec_layout.setSpacing(12)

        sec2 = QLabel("1.2.2. Đổi mật khẩu đăng nhập")
        sec2.setObjectName("SectionTitle")
        sec_layout.addWidget(sec2)

        desc = QLabel(
            "Để bảo vệ tài khoản thi và quản lý đào tạo, hãy sử dụng mật khẩu tối thiểu 6 ký tự "
            "và không chia sẻ mật khẩu cho người khác."
        )
        desc.setWordWrap(True)
        desc.setObjectName("MutedText")
        sec_layout.addWidget(desc)

        open_pwd_btn = QPushButton("Mở hộp thoại Đổi mật khẩu")
        open_pwd_btn.setObjectName("WarningBtn")
        open_pwd_btn.clicked.connect(lambda: ChangePasswordDialog(self, mandatory=False).exec())
        sec_layout.addWidget(open_pwd_btn)
        sec_layout.addStretch()

        content_row.addWidget(info_card, 3)
        content_row.addWidget(sec_card, 2)
        root.addLayout(content_row)
        root.addStretch()

    def _populate_from_user(self, user: UserProfile | None) -> None:
        if user is None:
            return
        self.username_lbl.setText(user.username)
        self.role_lbl.setText(f"{user.role_name} ({user.role_code})")
        self.last_login_lbl.setText(str(user.last_login_at or "Chưa ghi nhận"))
        self.full_name_edit.setText(user.full_name)
        self.email_edit.setText(user.email or "")
        self.phone_edit.setText(user.phone or "")

    def reload_profile(self) -> None:
        try:
            profile_controller.refresh_profile()
        except APIError as err:
            QMessageBox.warning(self, "Lỗi tải hồ sơ", err.message)

    def _save_profile(self) -> None:
        full_name = self.full_name_edit.text().strip()
        if len(full_name) < 2:
            QMessageBox.warning(self, "Dữ liệu chưa hợp lệ", "Họ và tên phải từ 2 ký tự trở lên.")
            return
        try:
            profile_controller.update_profile(
                full_name=full_name,
                email=self.email_edit.text(),
                phone=self.phone_edit.text(),
            )
            QMessageBox.information(self, "Thành công", "Cập nhật thông tin cá nhân thành công.")
        except APIError as err:
            QMessageBox.critical(self, "Không thể cập nhật", err.message)

