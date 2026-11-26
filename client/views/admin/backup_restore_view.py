"""Giao diện Dữ liệu & vận hành (1.5.1 Sao lưu CSDL ra .sql và Phục hồi dữ liệu hệ thống)."""
from pathlib import Path
from typing import Any, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from client.api.http_client import APIError
from client.controllers.admin_controller import admin_controller
from client.views.styles import format_bytes


class BackupRestoreView(QWidget):
    """Màn hình 1.5 - Sao lưu (Backup) và Phục hồi (Restore) cơ sở dữ liệu."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._backups: list[dict[str, Any]] = []
        self._build_ui()
        self.load_backups()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(14)

        top_card = QFrame()
        top_card.setObjectName("Card")
        tl = QVBoxLayout(top_card)
        tl.setContentsMargins(18, 16, 18, 16)
        tl.setSpacing(10)

        head = QLabel("1.5.1. Sao lưu (Backup) và Phục hồi (Restore) Cơ sở dữ liệu")
        head.setObjectName("SectionTitle")
        tl.addWidget(head)

        note = QLabel(
            "Hệ thống xuất toàn bộ cấu trúc bảng và dữ liệu ra tệp chuẩn .sql (UTF-8). "
            "Khi phục hồi dữ liệu, Server sẽ tự động tạo thêm một bản sao lưu an toàn (pre_restore_*.sql) "
            "trước khi ghi đè nhằm đảm bảo không mất dữ liệu."
        )
        note.setWordWrap(True)
        note.setObjectName("MutedText")
        tl.addWidget(note)

        btn_row = QHBoxLayout()
        backup_server_btn = QPushButton("+ Tạo bản sao lưu trên Server")
        backup_server_btn.setObjectName("PrimaryBtn")
        backup_server_btn.clicked.connect(self._create_server_backup)

        backup_save_btn = QPushButton("Sao lưu & Lưu tệp .sql về máy...")
        backup_save_btn.setObjectName("SuccessBtn")
        backup_save_btn.clicked.connect(self._create_and_download_backup)

        restore_file_btn = QPushButton("Phục hồi từ tệp .sql trên máy...")
        restore_file_btn.setObjectName("WarningBtn")
        restore_file_btn.clicked.connect(self._restore_from_local_file)

        refresh_btn = QPushButton("Làm mới danh sách")
        refresh_btn.clicked.connect(self.load_backups)

        btn_row.addWidget(backup_server_btn)
        btn_row.addWidget(backup_save_btn)
        btn_row.addWidget(restore_file_btn)
        btn_row.addStretch()
        btn_row.addWidget(refresh_btn)
        tl.addLayout(btn_row)
        root.addWidget(top_card)

        # --- Thanh thao tác với bản sao lưu trong bảng ---
        table_actions = QHBoxLayout()
        lbl = QLabel("Danh sách các tệp sao lưu đang lưu trữ trên Server")
        lbl.setStyleSheet("font-weight: 700; color: #334155;")

        dl_btn = QPushButton("Tải tệp đã chọn về máy")
        dl_btn.clicked.connect(self._download_selected)

        restore_srv_btn = QPushButton("Phục hồi từ bản đã chọn")
        restore_srv_btn.setObjectName("WarningBtn")
        restore_srv_btn.clicked.connect(self._restore_selected_on_server)

        del_btn = QPushButton("Xóa bản sao lưu")
        del_btn.setObjectName("DangerBtn")
        del_btn.clicked.connect(self._delete_selected)

        table_actions.addWidget(lbl)
        table_actions.addStretch()
        table_actions.addWidget(dl_btn)
        table_actions.addWidget(restore_srv_btn)
        table_actions.addWidget(del_btn)
        root.addLayout(table_actions)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Tên tệp sao lưu (.sql)", "Dung lượng", "Thời điểm tạo"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        root.addWidget(self.table, 1)

    def load_backups(self) -> None:
        try:
            self._backups = admin_controller.list_backups()
            self._render_table()
        except APIError:
            pass

    def _render_table(self) -> None:
        self.table.setRowCount(len(self._backups))
        for row, b in enumerate(self._backups):
            vals = [
                str(b.get("filename", "")),
                format_bytes(int(b.get("size_bytes", 0))),
                str(b.get("created_at", "")).replace("T", " ")[:19],
            ]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(val)
                if col in (1, 2):
                    item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)

    def _selected_filename(self) -> Optional[str]:
        row = self.table.currentRow()
        if 0 <= row < len(self._backups):
            return str(self._backups[row].get("filename"))
        QMessageBox.information(self, "Chưa chọn tệp", "Vui lòng chọn một bản sao lưu trong danh sách.")
        return None

    def _create_server_backup(self) -> None:
        try:
            created = admin_controller.create_backup()
            QMessageBox.information(
                self,
                "Sao lưu thành công",
                f"Đã tạo tệp sao lưu: {created.get('filename')} "
                f"({format_bytes(int(created.get('size_bytes', 0)))}).",
            )
            self.load_backups()
        except APIError as err:
            QMessageBox.critical(self, "Sao lưu thất bại", err.message)

    def _create_and_download_backup(self) -> None:
        try:
            created = admin_controller.create_backup()
            filename = str(created.get("filename"))
            self.load_backups()
        except APIError as err:
            QMessageBox.critical(self, "Sao lưu thất bại", err.message)
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Lưu tệp sao lưu .sql", filename, "SQL Backup (*.sql)"
        )
        if not save_path:
            return
        try:
            admin_controller.download_backup(filename, Path(save_path))
            QMessageBox.information(self, "Hoàn tất", f"Đã lưu bản sao lưu tại:\n{save_path}")
        except APIError as err:
            QMessageBox.critical(self, "Không thể tải tệp", err.message)

    def _download_selected(self) -> None:
        filename = self._selected_filename()
        if not filename:
            return
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Lưu tệp sao lưu .sql", filename, "SQL Backup (*.sql)"
        )
        if not save_path:
            return
        try:
            admin_controller.download_backup(filename, Path(save_path))
            QMessageBox.information(self, "Đã tải xuống", f"Đã lưu tệp tại:\n{save_path}")
        except APIError as err:
            QMessageBox.critical(self, "Không thể tải xuống", err.message)

    def _restore_selected_on_server(self) -> None:
        filename = self._selected_filename()
        if not filename:
            return
        ans = QMessageBox.warning(
            self,
            "Xác nhận phục hồi dữ liệu (1.5.1)",
            f"Bạn sắp khôi phục cơ sở dữ liệu về thời điểm của tệp:\n'{filename}'\n\n"
            "Dữ liệu hiện tại sẽ được tự động sao lưu vào tệp pre_restore_*.sql trước khi thực thi.\n"
            "Tiếp tục phục hồi?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if ans != QMessageBox.Yes:
            return
        try:
            res = admin_controller.restore_from_server(filename)
            QMessageBox.information(
                self,
                "Phục hồi thành công",
                f"{res.get('message')}\n"
                f"Số câu lệnh SQL đã chạy: {res.get('statements_executed')}\n"
                f"Bản sao lưu an toàn: {res.get('safety_backup')}",
            )
            self.load_backups()
        except APIError as err:
            QMessageBox.critical(self, "Phục hồi thất bại", err.message)

    def _restore_from_local_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Chọn tệp sao lưu .sql cần phục hồi", "", "SQL Backup (*.sql)"
        )
        if not file_path:
            return
        p = Path(file_path)
        ans = QMessageBox.warning(
            self,
            "Xác nhận phục hồi từ tệp máy trạm (1.5.1)",
            f"Tải lên và phục hồi CSDL từ tệp:\n'{p.name}'?\n\n"
            "Hệ thống sẽ tạo bản sao lưu an toàn trước khi khôi phục.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if ans != QMessageBox.Yes:
            return
        try:
            res = admin_controller.restore_from_local_file(p)
            QMessageBox.information(
                self,
                "Phục hồi thành công",
                f"{res.get('message')}\n"
                f"Số câu lệnh SQL đã chạy: {res.get('statements_executed')}\n"
                f"Bản sao lưu an toàn: {res.get('safety_backup')}",
            )
            self.load_backups()
        except APIError as err:
            QMessageBox.critical(self, "Phục hồi thất bại", err.message)

    def _delete_selected(self) -> None:
        filename = self._selected_filename()
        if not filename:
            return
        ans = QMessageBox.question(
            self,
            "Xóa tệp sao lưu",
            f"Xóa vĩnh viễn tệp '{filename}' khỏi máy chủ?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if ans != QMessageBox.Yes:
            return
        try:
            admin_controller.delete_backup(filename)
            self.load_backups()
        except APIError as err:
            QMessageBox.critical(self, "Không thể xóa", err.message)

