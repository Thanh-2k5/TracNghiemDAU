"""Giao diện Đăng nhập (1.1.1) & Xử lý chặn trùng phiên song song (1.1.3) dùng chung 7 tác nhân."""
from PySide6.QtCore import Qt, Signal
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
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from client.api.http_client import APIError, api_client
from client.controllers.auth_controller import auth_controller
from client.models.user_model import UserProfile


class ServerEndpointDialog(QDialog):
    """Hộp thoại cấu hình địa chỉ IP & Port Server kết nối từ máy trạm."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Cấu hình kết nối Máy chủ")
        self.setModal(True)
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.host_input = QLineEdit(api_client.server_host)
        self.host_input.setPlaceholderText("VD: 127.0.0.1 hoặc 192.168.1.10")

        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(api_client.server_port)

        form.addRow("Địa chỉ IP Server:", self.host_input)
        form.addRow("Cổng REST API:", self.port_input)
        layout.addLayout(form)

        note = QLabel("Lưu ý: Cổng Socket Real-time sẽ tự động đồng bộ từ Server sau khi đăng nhập.")
        note.setWordWrap(True)
        note.setObjectName("MutedText")
        layout.addWidget(note)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Hủy")
        save_btn = QPushButton("Lưu cấu hình")
        save_btn.setObjectName("PrimaryBtn")
        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _on_save(self) -> None:
        host = self.host_input.text().strip()
        if not host:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập địa chỉ IP hoặc tên miền Server.")
            return
        api_client.set_endpoint(host, self.port_input.value(), persist=True)
        self.accept()


class LoginView(QWidget):
    """Màn hình đăng nhập trung tâm cho cả 7 nhóm tác nhân."""

    login_succeeded = Signal(object)  # UserProfile

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setObjectName("Card")
        card.setFixedWidth(430)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 32, 32, 28)
        card_layout.setSpacing(14)

        school_lbl = QLabel("TRƯỜNG ĐẠI HỌC KIẾN TRÚC ĐÀ NẴNG (DAU)")
        school_lbl.setAlignment(Qt.AlignCenter)
        school_lbl.setStyleSheet("font-size: 12px; font-weight: 700; color: #1d4ed8; letter-spacing: 0.5px;")
        card_layout.addWidget(school_lbl)

        title = QLabel("HỆ THỐNG THI TRẮC NGHIỆM TRỰC TUYẾN")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 17px; font-weight: 800; color: #0f172a;")
        card_layout.addWidget(title)

        sub = QLabel("Đăng nhập bằng tài khoản được cấp cho từng vai trò")
        sub.setAlignment(Qt.AlignCenter)
        sub.setObjectName("MutedText")
        card_layout.addWidget(sub)

        card_layout.addSpacing(6)

        user_lbl = QLabel("Tên đăng nhập")
        user_lbl.setStyleSheet("font-weight: 600;")
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Nhập mã sinh viên / tên tài khoản...")

        pwd_lbl = QLabel("Mật khẩu")
        pwd_lbl.setStyleSheet("font-weight: 600;")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("Nhập mật khẩu...")

        self.show_pwd_cb = QCheckBox("Hiện mật khẩu")
        self.show_pwd_cb.toggled.connect(
            lambda checked: self.password_edit.setEchoMode(
                QLineEdit.Normal if checked else QLineEdit.Password
            )
        )

        self.error_lbl = QLabel("")
        self.error_lbl.setWordWrap(True)
        self.error_lbl.setStyleSheet(
            "color: #b91c1c; background-color: #fef2f2; border: 1px solid #fecaca;"
            "border-radius: 6px; padding: 8px;"
        )
        self.error_lbl.setVisible(False)

        self.login_btn = QPushButton("Đăng nhập hệ thống")
        self.login_btn.setObjectName("PrimaryBtn")
        self.login_btn.setMinimumHeight(38)
        self.login_btn.clicked.connect(self._handle_login)
        self.password_edit.returnPressed.connect(self._handle_login)
        self.username_edit.returnPressed.connect(self.password_edit.setFocus)

        footer = QHBoxLayout()
        self.endpoint_lbl = QLabel()
        self.endpoint_lbl.setObjectName("MutedText")
        self._refresh_endpoint_label()

        cfg_btn = QPushButton("Cấu hình Server")
        cfg_btn.clicked.connect(self._open_endpoint_dialog)
        footer.addWidget(self.endpoint_lbl, 1)
        footer.addWidget(cfg_btn)

        card_layout.addWidget(user_lbl)
        card_layout.addWidget(self.username_edit)
        card_layout.addWidget(pwd_lbl)
        card_layout.addWidget(self.password_edit)
        card_layout.addWidget(self.show_pwd_cb)
        card_layout.addWidget(self.error_lbl)
        card_layout.addSpacing(4)
        card_layout.addWidget(self.login_btn)
        card_layout.addSpacing(6)
        card_layout.addLayout(footer)

        outer.addWidget(card)

    def _refresh_endpoint_label(self) -> None:
        self.endpoint_lbl.setText(f"Server: {api_client.base_url}")

    def _open_endpoint_dialog(self) -> None:
        dlg = ServerEndpointDialog(self)
        if dlg.exec() == QDialog.Accepted:
            self._refresh_endpoint_label()

    def reset_form(self, clear_username: bool = False) -> None:
        if clear_username:
            self.username_edit.clear()
        self.password_edit.clear()
        self.error_lbl.setVisible(False)
        self._refresh_endpoint_label()

    def _show_error(self, message: str) -> None:
        self.error_lbl.setText(message)
        self.error_lbl.setVisible(True)

    def _handle_login(self) -> None:
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        if not username or not password:
            self._show_error("Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu.")
            return

        self.error_lbl.setVisible(False)
        self.login_btn.setEnabled(False)
        self.login_btn.setText("Đang xác thực...")
        try:
            user = auth_controller.login(username, password, force=False)
            self._on_authenticated(user)
        except APIError as err:
            if err.code == "SESSION_CONFLICT":
                self._prompt_session_conflict(username, password, err)
            else:
                self._show_error(err.message)
        finally:
            self.login_btn.setEnabled(True)
            self.login_btn.setText("Đăng nhập hệ thống")

    def _prompt_session_conflict(self, username: str, password: str, err: APIError) -> None:
        """1.1.3 - Cảnh báo trùng phiên đăng nhập song song và cho phép cưỡng chế đăng xuất phiên cũ."""
        client_desc = err.extra.get("client_info") or "Thiết bị khác"
        question = (
            f"{err.message}\n"
            f"Thiết bị đang hoạt động: {client_desc}\n\n"
            "Bạn có muốn ĐĂNG XUẤT phiên cũ để tiếp tục đăng nhập trên máy này không?"
        )
        ans = QMessageBox.question(
            self,
            "Cảnh báo trùng phiên đăng nhập (1.1.3)",
            question,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if ans != QMessageBox.Yes:
            self._show_error("Đã hủy đăng nhập do tài khoản đang hoạt động ở phiên khác.")
            return
        try:
            user = auth_controller.login(username, password, force=True)
            self._on_authenticated(user)
        except APIError as force_err:
            self._show_error(force_err.message)

    def _on_authenticated(self, user: UserProfile) -> None:
        self.password_edit.clear()
        self.login_succeeded.emit(user)

