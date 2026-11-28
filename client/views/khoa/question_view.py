import json
from pathlib import Path
from typing import Any, Optional

from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QFileDialog, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
    QTextEdit, QVBoxLayout, QWidget,
)

from client.api.http_client import APIError
from client.controllers.khoa_controller import khoa_controller


QUESTION_TYPES = ["Single Choice", "True/False", "Multiple Choice", "Matching", "Drag & Drop", "List", "Fill in the Blank"]


class QuestionDialog(QDialog):
    def __init__(self, subjects: list[dict[str, Any]], chapters: list[dict[str, Any]],
                 item: Optional[dict[str, Any]] = None, parent: QWidget | None = None):
        super().__init__(parent)
        self.item = item
        self.subjects = subjects
        self.chapters = chapters
        self.setWindowTitle("Sửa câu hỏi" if item else "Thêm câu hỏi")
        self.setMinimumWidth(520)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.subject = QComboBox()
        for value in subjects:
            self.subject.addItem(f"{value['code']} - {value['name']}", value["id"])
        self.subject.currentIndexChanged.connect(self._reload_chapters)
        self.chapter = QComboBox()
        self.type = QComboBox()
        self.type.addItems(QUESTION_TYPES)
        self.difficulty = QComboBox()
        self.difficulty.addItems(["Dễ", "TB", "Khó"])
        self.content = QTextEdit(item["content"] if item else "")
        self.options = QTextEdit(json.dumps(item["options"], ensure_ascii=False, indent=2) if item and item.get("options") is not None else "")
        self.answer = QTextEdit(json.dumps(item["answer"], ensure_ascii=False, indent=2) if item and item.get("answer") is not None else "")
        self.explanation = QTextEdit(item["explanation"] or "" if item else "")
        form.addRow("Học phần (*):", self.subject)
        form.addRow("Chương (*):", self.chapter)
        form.addRow("Dạng câu hỏi:", self.type)
        form.addRow("Độ khó:", self.difficulty)
        form.addRow("Nội dung câu hỏi (*):", self.content)
        form.addRow("Lựa chọn / dữ liệu JSON:", self.options)
        form.addRow("Đáp án JSON:", self.answer)
        form.addRow("Giải thích:", self.explanation)
        layout.addLayout(form)
        if item:
            self.subject.setCurrentIndex(max(0, self.subject.findData(item["subject_id"])))
            self.type.setCurrentText(item["question_type"])
            self.difficulty.setCurrentText(item["difficulty"])
        self._reload_chapters()
        if item:
            self.chapter.setCurrentIndex(max(0, self.chapter.findData(item["chapter_id"])))
        buttons = QHBoxLayout()
        cancel = QPushButton("Hủy")
        save = QPushButton("Lưu")
        save.setObjectName("PrimaryBtn")
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self.submit)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        layout.addLayout(buttons)

    def _reload_chapters(self):
        subject_id = self.subject.currentData()
        current = self.chapter.currentData()
        self.chapter.blockSignals(True)
        self.chapter.clear()
        try:
            for chapter in khoa_controller.chapters(subject_id):
                self.chapter.addItem(f"{chapter['sort_order']}. {chapter['name']}", chapter["id"])
        except APIError:
            pass
        idx = self.chapter.findData(current)
        if idx >= 0:
            self.chapter.setCurrentIndex(idx)
        self.chapter.blockSignals(False)

    @staticmethod
    def _parse_json(text: str):
        text = text.strip()
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text

    def submit(self):
        if not self.content.toPlainText().strip() or self.chapter.count() == 0:
            QMessageBox.warning(self, "Thiếu dữ liệu", "Nhập nội dung câu hỏi và chọn chương.")
            return
        try:
            khoa_controller.save_question({
                "subject_id": self.subject.currentData(),
                "chapter_id": self.chapter.currentData(),
                "question_type": self.type.currentText(),
                "difficulty": self.difficulty.currentText(),
                "content": self.content.toPlainText().strip(),
                "options": self._parse_json(self.options.toPlainText()),
                "answer": self._parse_json(self.answer.toPlainText()),
                "explanation": self.explanation.toPlainText().strip() or None,
                "is_active": True,
            }, self.item["id"] if self.item else None)
            self.accept()
        except APIError as err:
            QMessageBox.critical(self, "Không thể lưu", err.message)


class MatrixDialog(QDialog):
    def __init__(self, subjects: list[dict[str, Any]], parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Lập ma trận câu hỏi")
        self.setMinimumWidth(500)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.subject = QComboBox()
        for item in subjects:
            self.subject.addItem(f"{item['code']} - {item['name']}", item["id"])
        self.name = QLineEdit()
        self.description = QTextEdit()
        self.matrix = QTextEdit(
            '{\n  "chapters": {"1": {"easy": 2, "medium": 2, "hard": 1}},\n'
            '  "total": 5\n}'
        )
        form.addRow("Học phần:", self.subject)
        form.addRow("Tên ma trận:", self.name)
        form.addRow("Mô tả:", self.description)
        form.addRow("Cấu trúc JSON:", self.matrix)
        layout.addLayout(form)
        buttons = QHBoxLayout()
        cancel = QPushButton("Hủy")
        save = QPushButton("Lưu ma trận")
        save.setObjectName("PrimaryBtn")
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self.submit)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        layout.addLayout(buttons)

    def submit(self):
        try:
            matrix = json.loads(self.matrix.toPlainText())
        except json.JSONDecodeError as err:
            QMessageBox.warning(self, "JSON không hợp lệ", str(err))
            return
        if not self.name.text().strip():
            QMessageBox.warning(self, "Thiếu dữ liệu", "Nhập tên ma trận.")
            return
        try:
            khoa_controller.create_matrix({
                "subject_id": self.subject.currentData(),
                "name": self.name.text().strip(),
                "description": self.description.toPlainText().strip() or None,
                "matrix": matrix,
            })
            self.accept()
        except APIError as err:
            QMessageBox.critical(self, "Không thể lưu", err.message)


class QuestionBankView(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.subjects: list[dict[str, Any]] = []
        self.items: list[dict[str, Any]] = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        filter_bar = QHBoxLayout()
        self.subject_filter = QComboBox()
        self.subject_filter.addItem("Tất cả học phần", None)
        self.chapter_filter = QComboBox()
        self.chapter_filter.addItem("Tất cả chương", None)
        self.difficulty_filter = QComboBox()
        self.difficulty_filter.addItem("Tất cả độ khó", None)
        self.difficulty_filter.addItems(["Dễ", "TB", "Khó"])
        self.keyword = QLineEdit()
        self.keyword.setPlaceholderText("Tìm nội dung câu hỏi...")
        find = QPushButton("Lọc")
        import_btn = QPushButton("Nhập Excel/Word")
        matrix_btn = QPushButton("Lập ma trận")
        add_btn = QPushButton("+ Thêm câu hỏi")
        add_btn.setObjectName("PrimaryBtn")
        find.clicked.connect(self.reload)
        import_btn.clicked.connect(self.import_file)
        matrix_btn.clicked.connect(self.open_matrix)
        add_btn.clicked.connect(self.create)
        self.subject_filter.currentIndexChanged.connect(self._subject_changed)
        filter_bar.addWidget(self.subject_filter)
        filter_bar.addWidget(self.chapter_filter)
        filter_bar.addWidget(self.difficulty_filter)
        filter_bar.addWidget(self.keyword, 1)
        filter_bar.addWidget(find)
        filter_bar.addWidget(import_btn)
        filter_bar.addWidget(matrix_btn)
        filter_bar.addWidget(add_btn)
        layout.addLayout(filter_bar)
        actions = QHBoxLayout()
        edit = QPushButton("Sửa")
        toggle = QPushButton("Ẩn/Hiện")
        delete = QPushButton("Xóa")
        delete.setObjectName("DangerBtn")
        edit.clicked.connect(self.edit_selected)
        toggle.clicked.connect(self.toggle_selected)
        delete.clicked.connect(self.delete_selected)
        actions.addStretch()
        actions.addWidget(edit)
        actions.addWidget(toggle)
        actions.addWidget(delete)
        layout.addLayout(actions)
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(["ID", "Học phần", "Chương", "Dạng", "Độ khó", "Nội dung", "Trạng thái", "Giải thích"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.doubleClicked.connect(lambda _: self.edit_selected())
        layout.addWidget(self.table)
        self.load_subjects()

    def load_subjects(self):
        try:
            self.subjects = khoa_controller.subjects()
            self.subject_filter.blockSignals(True)
            for item in self.subjects:
                self.subject_filter.addItem(f"{item['code']} - {item['name']}", item["id"])
            self.subject_filter.blockSignals(False)
            self.reload()
        except APIError as err:
            QMessageBox.warning(self, "Không tải được dữ liệu", err.message)

    def _subject_changed(self):
        subject_id = self.subject_filter.currentData()
        self.chapter_filter.blockSignals(True)
        self.chapter_filter.clear()
        self.chapter_filter.addItem("Tất cả chương", None)
        if subject_id:
            try:
                for item in khoa_controller.chapters(subject_id):
                    self.chapter_filter.addItem(item["name"], item["id"])
            except APIError:
                pass
        self.chapter_filter.blockSignals(False)
        self.reload()

    def reload(self):
        try:
            subject_id = self.subject_filter.currentData()
            chapter_id = self.chapter_filter.currentData()
            difficulty = self.difficulty_filter.currentText()
            if difficulty == "Tất cả độ khó":
                difficulty = None
            self.items = khoa_controller.questions(subject_id, chapter_id, difficulty, self.keyword.text())
            self.table.setRowCount(len(self.items))
            for row, item in enumerate(self.items):
                values = [
                    str(item["id"]), item["subject_code"], item["chapter_name"], item["question_type"],
                    item["difficulty"], item["content"], "Hiện" if item["is_active"] else "Ẩn",
                    item["explanation"] or "",
                ]
                for col, value in enumerate(values):
                    self.table.setItem(row, col, QTableWidgetItem(value))
        except APIError as err:
            QMessageBox.warning(self, "Không tải được câu hỏi", err.message)

    def selected(self) -> Optional[dict[str, Any]]:
        row = self.table.currentRow()
        return self.items[row] if 0 <= row < len(self.items) else None

    def create(self):
        if not self.subjects:
            QMessageBox.information(self, "Chưa có học phần", "Hãy tạo học phần trước.")
            return
        if QuestionDialog(self.subjects, [], parent=self).exec() == QDialog.Accepted:
            self.reload()

    def edit_selected(self):
        item = self.selected()
        if item and QuestionDialog(self.subjects, [], item, self).exec() == QDialog.Accepted:
            self.reload()

    def toggle_selected(self):
        item = self.selected()
        if not item:
            return
        try:
            khoa_controller.set_question_visibility(item["id"], not item["is_active"])
            self.reload()
        except APIError as err:
            QMessageBox.critical(self, "Không thể đổi trạng thái", err.message)

    def delete_selected(self):
        item = self.selected()
        if not item:
            return
        if QMessageBox.question(self, "Xác nhận xóa", "Xóa câu hỏi này?") != QMessageBox.Yes:
            return
        try:
            khoa_controller.delete_question(item["id"])
            self.reload()
        except APIError as err:
            QMessageBox.critical(self, "Không thể xóa", err.message)

    def import_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Chọn tệp câu hỏi", "", "Excel/Word (*.xlsx *.docx)")
        if not path:
            return
        try:
            result = khoa_controller.import_questions(Path(path))
            message = f"Đã nhập {result.get('imported', 0)} / {result.get('total', 0)} câu hỏi."
            if result.get("errors"):
                message += "\nLỗi:\n" + "\n".join(str(i) for i in result["errors"][:10])
            QMessageBox.information(self, "Kết quả nhập hàng loạt", message)
            self.reload()
        except APIError as err:
            QMessageBox.critical(self, "Không thể nhập", err.message)

    def open_matrix(self):
        if not self.subjects:
            QMessageBox.information(self, "Chưa có học phần", "Hãy tạo học phần trước.")
            return
        if MatrixDialog(self.subjects, self).exec() == QDialog.Accepted:
            QMessageBox.information(self, "Ma trận câu hỏi", "Đã lưu ma trận câu hỏi.")
