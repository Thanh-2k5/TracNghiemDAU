from typing import Any, Optional

from PySide6.QtWidgets import (
    QAbstractItemView, QDialog, QFormLayout, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPushButton, QSpinBox, QTableWidget,
    QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget,
)

from client.api.http_client import APIError
from client.controllers.khoa_controller import khoa_controller


class SubjectDialog(QDialog):
    def __init__(self, item: Optional[dict[str, Any]] = None, parent: QWidget | None = None):
        super().__init__(parent)
        self.item = item
        self.setWindowTitle("Sửa học phần" if item else "Thêm học phần")
        self.setMinimumWidth(430)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.code = QLineEdit(item["code"] if item else "")
        self.name = QLineEdit(item["name"] if item else "")
        self.credits = QSpinBox()
        self.credits.setRange(1, 20)
        self.credits.setValue(item["credits"] if item else 3)
        self.duration = QSpinBox()
        self.duration.setRange(1, 600)
        self.duration.setValue(item["exam_duration_minutes"] if item else 60)
        self.description = QTextEdit(item["description"] or "" if item else "")
        form.addRow("Mã học phần (*):", self.code)
        form.addRow("Tên học phần (*):", self.name)
        form.addRow("Số tín chỉ:", self.credits)
        form.addRow("Thời gian thi (phút):", self.duration)
        form.addRow("Mô tả:", self.description)
        layout.addLayout(form)
        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton("Hủy")
        save = QPushButton("Lưu")
        save.setObjectName("PrimaryBtn")
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self.submit)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        layout.addLayout(buttons)

    def submit(self):
        if not self.code.text().strip() or not self.name.text().strip():
            QMessageBox.warning(self, "Thiếu dữ liệu", "Vui lòng nhập mã và tên học phần.")
            return
        try:
            khoa_controller.save_subject({
                "code": self.code.text().strip(),
                "name": self.name.text().strip(),
                "credits": self.credits.value(),
                "exam_duration_minutes": self.duration.value(),
                "description": self.description.toPlainText().strip() or None,
                "is_active": True,
            }, self.item["id"] if self.item else None)
            self.accept()
        except APIError as err:
            QMessageBox.critical(self, "Không thể lưu", err.message)


class SubjectView(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.items: list[dict[str, Any]] = []
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        toolbar = QFrame()
        toolbar.setObjectName("Card")
        row = QHBoxLayout(toolbar)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Tìm theo mã hoặc tên học phần...")
        self.search.returnPressed.connect(self.reload)
        find = QPushButton("Tìm kiếm")
        find.clicked.connect(self.reload)
        add = QPushButton("+ Thêm học phần")
        add.setObjectName("PrimaryBtn")
        add.clicked.connect(self.create)
        row.addWidget(self.search, 1)
        row.addWidget(find)
        row.addWidget(add)
        root.addWidget(toolbar)
        actions = QHBoxLayout()
        edit = QPushButton("Sửa")
        delete = QPushButton("Xóa")
        delete.setObjectName("DangerBtn")
        edit.clicked.connect(self.edit_selected)
        delete.clicked.connect(self.delete_selected)
        actions.addStretch()
        actions.addWidget(edit)
        actions.addWidget(delete)
        root.addLayout(actions)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "Mã môn", "Tên môn", "Tín chỉ", "Thời gian thi", "Mô tả"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.doubleClicked.connect(lambda _: self.edit_selected())
        root.addWidget(self.table)
        self.reload()

    def reload(self):
        try:
            self.items = khoa_controller.subjects(self.search.text())
            self.table.setRowCount(len(self.items))
            for row, item in enumerate(self.items):
                values = [str(item["id"]), item["code"], item["name"], str(item["credits"]),
                          f"{item['exam_duration_minutes']} phút", item["description"] or ""]
                for col, value in enumerate(values):
                    self.table.setItem(row, col, QTableWidgetItem(value))
        except APIError as err:
            QMessageBox.warning(self, "Không tải được học phần", err.message)

    def selected(self) -> Optional[dict[str, Any]]:
        row = self.table.currentRow()
        if 0 <= row < len(self.items):
            return self.items[row]
        QMessageBox.information(self, "Chưa chọn học phần", "Vui lòng chọn một học phần trong bảng.")
        return None

    def create(self):
        if SubjectDialog(parent=self).exec() == QDialog.Accepted:
            self.reload()

    def edit_selected(self):
        item = self.selected()
        if item and SubjectDialog(item, self).exec() == QDialog.Accepted:
            self.reload()

    def delete_selected(self):
        item = self.selected()
        if not item:
            return
        if QMessageBox.question(self, "Xác nhận xóa", f"Xóa học phần '{item['name']}'?") != QMessageBox.Yes:
            return
        try:
            khoa_controller.delete_subject(item["id"])
            self.reload()
        except APIError as err:
            QMessageBox.critical(self, "Không thể xóa", err.message)
