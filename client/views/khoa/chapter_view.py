from typing import Any, Optional

from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QFormLayout, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QMessageBox, QPushButton, QSpinBox, QTableWidget,
    QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget,
)

from client.api.http_client import APIError
from client.controllers.khoa_controller import khoa_controller


class ChapterDialog(QDialog):
    def __init__(self, subject_id: int, item: Optional[dict[str, Any]] = None, parent: QWidget | None = None):
        super().__init__(parent)
        self.subject_id = subject_id
        self.item = item
        self.setWindowTitle("Sửa chương" if item else "Thêm chương")
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name = QLineEdit(item["name"] if item else "")
        self.order = QSpinBox()
        self.order.setRange(1, 999)
        self.order.setValue(item["sort_order"] if item else 1)
        self.description = QTextEdit(item["description"] or "" if item else "")
        form.addRow("Tên chương (*):", self.name)
        form.addRow("Thứ tự:", self.order)
        form.addRow("Mô tả:", self.description)
        layout.addLayout(form)
        buttons = QHBoxLayout()
        cancel = QPushButton("Hủy")
        save = QPushButton("Lưu")
        save.setObjectName("PrimaryBtn")
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self.submit)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        layout.addLayout(buttons)

    def submit(self):
        if not self.name.text().strip():
            QMessageBox.warning(self, "Thiếu dữ liệu", "Vui lòng nhập tên chương.")
            return
        try:
            khoa_controller.save_chapter({
                "subject_id": self.subject_id,
                "name": self.name.text().strip(),
                "description": self.description.toPlainText().strip() or None,
                "sort_order": self.order.value(),
            }, self.item["id"] if self.item else None)
            self.accept()
        except APIError as err:
            QMessageBox.critical(self, "Không thể lưu", err.message)


class ChapterView(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.subjects: list[dict[str, Any]] = []
        self.items: list[dict[str, Any]] = []
        root = QVBoxLayout(self)
        filter_row = QHBoxLayout()
        self.subject_combo = QComboBox()
        self.subject_combo.currentIndexChanged.connect(self.reload)
        filter_row.addWidget(QLabel("Học phần:"))
        filter_row.addWidget(self.subject_combo, 1)
        add = QPushButton("+ Thêm chương")
        add.setObjectName("PrimaryBtn")
        add.clicked.connect(self.create)
        filter_row.addWidget(add)
        root.addLayout(filter_row)
        actions = QHBoxLayout()
        edit = QPushButton("Sửa")
        up = QPushButton("↑ Lên")
        down = QPushButton("↓ Xuống")
        delete = QPushButton("Xóa")
        delete.setObjectName("DangerBtn")
        edit.clicked.connect(self.edit_selected)
        up.clicked.connect(lambda: self.move(-1))
        down.clicked.connect(lambda: self.move(1))
        delete.clicked.connect(self.delete_selected)
        actions.addStretch()
        actions.addWidget(edit)
        actions.addWidget(up)
        actions.addWidget(down)
        actions.addWidget(delete)
        root.addLayout(actions)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Thứ tự", "Tên chương", "Mô tả"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.doubleClicked.connect(lambda _: self.edit_selected())
        root.addWidget(self.table)
        self.load_subjects()

    def load_subjects(self):
        try:
            self.subjects = khoa_controller.subjects()
            self.subject_combo.blockSignals(True)
            self.subject_combo.clear()
            for item in self.subjects:
                self.subject_combo.addItem(f"{item['code']} - {item['name']}", item["id"])
            self.subject_combo.blockSignals(False)
            self.reload()
        except APIError as err:
            QMessageBox.warning(self, "Không tải được học phần", err.message)

    def subject_id(self) -> Optional[int]:
        return self.subject_combo.currentData()

    def reload(self):
        subject_id = self.subject_id()
        if subject_id is None:
            self.items = []
        else:
            try:
                self.items = khoa_controller.chapters(subject_id)
            except APIError as err:
                QMessageBox.warning(self, "Không tải được chương", err.message)
                return
        self.table.setRowCount(len(self.items))
        for row, item in enumerate(self.items):
            values = [str(item["id"]), str(item["sort_order"]), item["name"], item["description"] or ""]
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(value))

    def selected(self) -> Optional[dict[str, Any]]:
        row = self.table.currentRow()
        return self.items[row] if 0 <= row < len(self.items) else None

    def create(self):
        subject_id = self.subject_id()
        if subject_id is None:
            QMessageBox.information(self, "Chưa có học phần", "Hãy tạo học phần trước.")
            return
        if ChapterDialog(subject_id, parent=self).exec() == QDialog.Accepted:
            self.reload()

    def edit_selected(self):
        item = self.selected()
        subject_id = self.subject_id()
        if item and subject_id and ChapterDialog(subject_id, item, self).exec() == QDialog.Accepted:
            self.reload()

    def move(self, delta: int):
        row = self.table.currentRow()
        target = row + delta
        if row < 0 or not 0 <= target < len(self.items):
            return
        ids = [item["id"] for item in self.items]
        ids[row], ids[target] = ids[target], ids[row]
        try:
            khoa_controller.reorder_chapters(self.subject_id(), ids)
            self.reload()
            self.table.selectRow(target)
        except APIError as err:
            QMessageBox.critical(self, "Không thể sắp xếp", err.message)

    def delete_selected(self):
        item = self.selected()
        if not item:
            return
        if QMessageBox.question(self, "Xác nhận xóa", f"Xóa chương '{item['name']}'?") != QMessageBox.Yes:
            return
        try:
            khoa_controller.delete_chapter(item["id"])
            self.reload()
        except APIError as err:
            QMessageBox.critical(self, "Không thể xóa", err.message)
