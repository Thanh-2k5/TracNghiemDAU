"""Giao diện Quản lý tài khoản (1.3.1 Thêm/Sửa/Khóa, 1.3.2 Reset mật khẩu, 1.3.3 Gán vai trò)."""
from typing import Any, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from client.api.http_client import APIError
from client.controllers.admin_controller import admin_controller
from client.models.user_model import UserProfile


class AccountFormDialog(QDialog):
    """1.3.1 - Hộp thoại Thêm mới hoặc Sửa thông tin tài khoản."""

    def __init__(
        self,
        roles: list[dict[str, Any]],
        user: Optional[UserProfile] = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.roles = roles
        self.editing_user = user
        self.setWindowTitle("Sửa thông tin tài khoản" if user else "Thêm tài khoản mới (1.3.1)")
        self.setModal(True)
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        self.username_edit = QLineEdit(user.username if user else "")
        self.username_edit.setPlaceholderText("3-50 ký tự (chữ, số, dấu _ hoặc .)")
        if user:
            self.username_edit.setReadOnly(True)

        self.full_name_edit = QLineEdit(user.full_name if user else "")
        self.email_edit = QLineEdit(user.email or "" if user else "")
        self.phone_edit = QLineEdit(user.phone or "" if user else "")

        form.addRow("Tên đăng nhập (*):", self.username_edit)
        form.addRow("Họ và tên (*):", self.full_name_edit)
        form.addRow("Email:", self.email_edit)
        form.addRow("Số điện thoại:", self.phone_edit)

        if not user:
            self.password_edit = QLineEdit()
            self.password_edit.setEchoMode(QLineEdit.Password)
            self.password_edit.setPlaceholderText("Để trống để dùng mật khẩu mặc định hệ thống")

            self.role_combo = QComboBox()
            for r in roles:
                self.role_combo.addItem(f"{r['name']} ({r['code']})", r["code"])

            self.active_cb = QCheckBox("Kích hoạt tài khoản ngay")
            self.active_cb.setChecked(True)

            form.addRow("Mật khẩu khởi tạo:", self.password_edit)
            form.addRow("Vai trò (7 tác nhân):", self.role_combo)
            form.addRow("Trạng thái:", self.active_cb)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Hủy")
        save_btn = QPushButton("Lưu tài khoản")
        save_btn.setObjectName("PrimaryBtn")
        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self._submit)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _submit(self) -> None:
        try:
            if self.editing_user:
                admin_controller.update_account(
                    user_id=self.editing_user.id,
                    full_name=self.full_name_edit.text(),
                    email=self.email_edit.text(),
                    phone=self.phone_edit.text(),
                )
            else:
                admin_controller.create_account(
                    username=self.username_edit.text(),
                    password=self.password_edit.text(),
                    full_name=self.full_name_edit.text(),
                    email=self.email_edit.text(),
                    phone=self.phone_edit.text(),
                    role_code=str(self.role_combo.currentData()),
                    is_active=self.active_cb.isChecked(),
                )
            self.accept()
        except APIError as err:
            QMessageBox.critical(self, "Không thể lưu tài khoản", err.message)


class AssignRoleDialog(QDialog):
    """1.3.3 - Hộp thoại gán vai trò phân quyền (1 trong 7 nhóm tác nhân)."""

    def __init__(
        self,
        user: UserProfile,
        roles: list[dict[str, Any]],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.user = user
        self.roles = roles
        self.setWindowTitle(f"Gán vai trò - {user.username} (1.3.3)")
        self.setModal(True)
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        info = QLabel(f"Tài khoản: <b>{user.full_name}</b> ({user.username})")
        layout.addWidget(info)

        self.role_combo = QComboBox()
        self.desc_lbl = QLabel("")
        self.desc_lbl.setWordWrap(True)
        self.desc_lbl.setObjectName("MutedText")

        current_idx = 0
        for idx, r in enumerate(roles):
            self.role_combo.addItem(f"{r['name']} ({r['code']})", r)
            if r["code"] == user.role_code:
                current_idx = idx
        self.role_combo.currentIndexChanged.connect(self._update_desc)
        self.role_combo.setCurrentIndex(current_idx)
        self._update_desc()

        form = QFormLayout()
        form.addRow("Chọn vai trò mới:", self.role_combo)
        layout.addLayout(form)
        layout.addWidget(self.desc_lbl)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Hủy")
        save_btn = QPushButton("Cập nhật phân quyền")
        save_btn.setObjectName("PrimaryBtn")
        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self._submit)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _update_desc(self) -> None:
        data = self.role_combo.currentData()
        if isinstance(data, dict):
            self.desc_lbl.setText(f"Mô tả quyền hạn: {data.get('description') or ''}")

    def _submit(self) -> None:
        data = self.role_combo.currentData()
        role_code = str(data["code"])
        try:
            admin_controller.assign_account_role(self.user.id, role_code)
            self.accept()
        except APIError as err:
            QMessageBox.critical(self, "Không thể gán vai trò", err.message)


class AccountManagementView(QWidget):
    """Màn hình 1.3 - Quản lý tài khoản và gán vai trò 7 tác nhân."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._roles: list[dict[str, Any]] = []
        self._accounts: list[UserProfile] = []
        self._page = 1
        self._page_size = 25
        self._total = 0

        self._build_ui()
        self.reload_all()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(12)

        # --- Thanh tìm kiếm & lọc ---
        filter_card = QFrame()
        filter_card.setObjectName("Card")
        fl = QHBoxLayout(filter_card)
        fl.setContentsMargins(14, 12, 14, 12)
        fl.setSpacing(10)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Tìm theo username, họ tên, email, SĐT...")
        self.search_edit.returnPressed.connect(self._search_from_first_page)

        self.role_filter = QComboBox()
        self.role_filter.addItem("Tất cả 7 vai trò", "")
        self.role_filter.currentIndexChanged.connect(self._search_from_first_page)

        self.status_filter = QComboBox()
        self.status_filter.addItem("Tất cả trạng thái", None)
        self.status_filter.addItem("Đang hoạt động", True)
        self.status_filter.addItem("Đã khóa", False)
        self.status_filter.currentIndexChanged.connect(self._search_from_first_page)

        search_btn = QPushButton("Tìm kiếm")
        search_btn.clicked.connect(self._search_from_first_page)

        add_btn = QPushButton("+ Thêm tài khoản (1.3.1)")
        add_btn.setObjectName("PrimaryBtn")
        add_btn.clicked.connect(self._open_create_dialog)

        fl.addWidget(self.search_edit, 2)
        fl.addWidget(self.role_filter, 1)
        fl.addWidget(self.status_filter, 1)
        fl.addWidget(search_btn)
        fl.addWidget(add_btn)
        root.addWidget(filter_card)

        # --- Thanh thao tác trên tài khoản được chọn ---
        action_bar = QHBoxLayout()
        self.summary_lbl = QLabel("Tổng số: 0 tài khoản")
        self.summary_lbl.setStyleSheet("font-weight: 700; color: #334155;")

        self.edit_btn = QPushButton("Sửa thông tin")
        self.edit_btn.clicked.connect(self._open_edit_dialog)

        self.toggle_btn = QPushButton("Khóa / Mở khóa")
        self.toggle_btn.setObjectName("WarningBtn")
        self.toggle_btn.clicked.connect(self._toggle_selected_status)

        self.reset_pwd_btn = QPushButton("Đặt lại mật khẩu (1.3.2)")
        self.reset_pwd_btn.clicked.connect(self._reset_selected_password)

        self.role_btn = QPushButton("Gán vai trò (1.3.3)")
        self.role_btn.setObjectName("SuccessBtn")
        self.role_btn.clicked.connect(self._assign_selected_role)

        action_bar.addWidget(self.summary_lbl)
        action_bar.addStretch()
        action_bar.addWidget(self.edit_btn)
        action_bar.addWidget(self.toggle_btn)
        action_bar.addWidget(self.reset_pwd_btn)
        action_bar.addWidget(self.role_btn)
        root.addLayout(action_bar)

        # --- Bảng danh sách tài khoản ---
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Tên đăng nhập", "Họ và tên", "Vai trò", "Email", "Số điện thoại", "Trạng thái"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.doubleClicked.connect(lambda _: self._open_edit_dialog())
        root.addWidget(self.table, 1)

        # --- Phân trang ---
        pager = QHBoxLayout()
        self.prev_btn = QPushButton("← Trang trước")
        self.next_btn = QPushButton("Trang sau →")
        self.page_lbl = QLabel("Trang 1")
        self.prev_btn.clicked.connect(self._prev_page)
        self.next_btn.clicked.connect(self._next_page)
        pager.addStretch()
        pager.addWidget(self.prev_btn)
        pager.addWidget(self.page_lbl)
        pager.addWidget(self.next_btn)
        root.addLayout(pager)

    def reload_all(self) -> None:
        try:
            self._roles = admin_controller.get_roles()
            self.role_filter.blockSignals(True)
            current = self.role_filter.currentData()
            self.role_filter.clear()
            self.role_filter.addItem("Tất cả 7 vai trò", "")
            for r in self._roles:
                self.role_filter.addItem(f"{r['name']} ({r['code']})", r["code"])
            idx = self.role_filter.findData(current)
            if idx >= 0:
                self.role_filter.setCurrentIndex(idx)
            self.role_filter.blockSignals(False)
        except APIError:
            pass
        self.load_accounts()

    def _search_from_first_page(self) -> None:
        self._page = 1
        self.load_accounts()

    def load_accounts(self) -> None:
        try:
            role_code = self.role_filter.currentData() or None
            status_val = self.status_filter.currentData()
            items, total = admin_controller.get_accounts(
                keyword=self.search_edit.text(),
                role_code=role_code,
                is_active=status_val,
                page=self._page,
                page_size=self._page_size,
            )
            self._accounts = items
            self._total = total
            self._render_table()
        except APIError as err:
            QMessageBox.warning(self, "Không thể tải danh sách tài khoản", err.message)

    def _render_table(self) -> None:
        self.table.setRowCount(len(self._accounts))
        for row, u in enumerate(self._accounts):
            status_txt = "Hoạt động" if u.is_active else "Đã khóa"
            cells = [
                str(u.id),
                u.username,
                u.full_name,
                f"{u.role_name} ({u.role_code})",
                u.email or "",
                u.phone or "",
                status_txt,
            ]
            for col, val in enumerate(cells):
                item = QTableWidgetItem(val)
                if col in (0, 6):
                    item.setTextAlignment(Qt.AlignCenter)
                if col == 6:
                    item.setForeground(QColor("#15803d" if u.is_active else "#dc2626"))
                self.table.setItem(row, col, item)

        max_page = max(1, (self._total + self._page_size - 1) // self._page_size)
        self.summary_lbl.setText(f"Tổng số: {self._total} tài khoản")
        self.page_lbl.setText(f"Trang {self._page} / {max_page}")
        self.prev_btn.setEnabled(self._page > 1)
        self.next_btn.setEnabled(self._page < max_page)

    def _selected_user(self) -> Optional[UserProfile]:
        row = self.table.currentRow()
        if 0 <= row < len(self._accounts):
            return self._accounts[row]
        QMessageBox.information(self, "Chưa chọn tài khoản", "Vui lòng chọn một tài khoản trong bảng.")
        return None

    def _open_create_dialog(self) -> None:
        if not self._roles:
            self.reload_all()
        dlg = AccountFormDialog(self._roles, user=None, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self.load_accounts()

    def _open_edit_dialog(self) -> None:
        user = self._selected_user()
        if not user:
            return
        dlg = AccountFormDialog(self._roles, user=user, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self.load_accounts()

    def _toggle_selected_status(self) -> None:
        user = self._selected_user()
        if not user:
            return
        target_active = not user.is_active
        verb = "MỞ KHÓA" if target_active else "KHÓA"
        ans = QMessageBox.question(
            self,
            f"Xác nhận {verb} tài khoản (1.3.1)",
            f"Bạn có chắc muốn {verb} tài khoản '{user.username}' ({user.full_name}) không?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if ans != QMessageBox.Yes:
            return
        try:
            admin_controller.toggle_account_status(user.id, target_active)
            self.load_accounts()
        except APIError as err:
            QMessageBox.critical(self, "Thao tác thất bại", err.message)

    def _reset_selected_password(self) -> None:
        user = self._selected_user()
        if not user:
            return
        ans = QMessageBox.question(
            self,
            "Đặt lại mật khẩu mặc định (1.3.2)",
            f"Đặt lại mật khẩu mặc định cho tài khoản '{user.username}'?\n"
            "Người dùng sẽ bị đăng xuất khỏi phiên hiện tại và phải đổi mật khẩu khi đăng nhập lại.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if ans != QMessageBox.Yes:
            return
        try:
            msg, default_pwd = admin_controller.reset_account_password(user.id)
            QMessageBox.information(
                self,
                "Đã đặt lại mật khẩu",
                f"{msg}\n\nMật khẩu mặc định mới: {default_pwd}",
            )
            self.load_accounts()
        except APIError as err:
            QMessageBox.critical(self, "Không thể đặt lại mật khẩu", err.message)

    def _assign_selected_role(self) -> None:
        user = self._selected_user()
        if not user:
            return
        dlg = AssignRoleDialog(user, self._roles, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self.load_accounts()

    def _prev_page(self) -> None:
        if self._page > 1:
            self._page -= 1
            self.load_accounts()

    def _next_page(self) -> None:
        self._page += 1
        self.load_accounts()

