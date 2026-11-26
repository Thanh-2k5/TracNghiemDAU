"""Giao diện Quản trị mạng (1.4.1 Cấu hình IP/Port, 1.4.2 Khởi động/Dừng, 1.4.3 Giám sát kết nối & băng thông)."""
from typing import Any

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from client.api.http_client import APIError
from client.controllers.admin_controller import admin_controller
from client.views.styles import format_bps, format_bytes, format_uptime


class NetworkManagementView(QWidget):
    """Màn hình 1.4 - Cấu hình mạng, điều khiển Socket Server và theo dõi băng thông thời gian thực."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._connections: list[dict[str, Any]] = []
        self._timer = QTimer(self)
        self._timer.setInterval(2500)
        self._timer.timeout.connect(self.refresh_monitoring)

        self._build_ui()
        self.load_network_config()
        self.refresh_monitoring()

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        if self.auto_refresh_cb.isChecked() and not self._timer.isActive():
            self._timer.start()
        self.refresh_monitoring()

    def hideEvent(self, event) -> None:  # noqa: N802
        self._timer.stop()
        super().hideEvent(event)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(14)

        top_row = QHBoxLayout()
        top_row.setSpacing(14)

        # --- 1.4.1 Cấu hình IP & Port ---
        cfg_card = QFrame()
        cfg_card.setObjectName("Card")
        cfg_layout = QVBoxLayout(cfg_card)
        cfg_layout.setContentsMargins(18, 16, 18, 16)
        cfg_layout.setSpacing(10)

        t1 = QLabel("1.4.1. Cấu hình địa chỉ IP & Port Server")
        t1.setObjectName("SectionTitle")
        cfg_layout.addWidget(t1)

        form = QGridLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)

        self.api_host_edit = QLineEdit("127.0.0.1")
        self.api_port_spin = QSpinBox()
        self.api_port_spin.setRange(1024, 65535)
        self.api_port_spin.setValue(8000)

        self.socket_host_edit = QLineEdit("0.0.0.0")
        self.socket_port_spin = QSpinBox()
        self.socket_port_spin.setRange(1024, 65535)
        self.socket_port_spin.setValue(9000)

        form.addWidget(QLabel("IP REST API:"), 0, 0)
        form.addWidget(self.api_host_edit, 0, 1)
        form.addWidget(QLabel("Port REST API:"), 0, 2)
        form.addWidget(self.api_port_spin, 0, 3)

        form.addWidget(QLabel("IP Socket Server:"), 1, 0)
        form.addWidget(self.socket_host_edit, 1, 1)
        form.addWidget(QLabel("Port Socket:"), 1, 2)
        form.addWidget(self.socket_port_spin, 1, 3)
        cfg_layout.addLayout(form)

        cfg_btns = QHBoxLayout()
        reload_cfg_btn = QPushButton("Đọc cấu hình")
        reload_cfg_btn.clicked.connect(self.load_network_config)
        save_cfg_btn = QPushButton("Lưu cấu hình mạng")
        save_cfg_btn.setObjectName("PrimaryBtn")
        save_cfg_btn.clicked.connect(self._save_config)
        cfg_btns.addStretch()
        cfg_btns.addWidget(reload_cfg_btn)
        cfg_btns.addWidget(save_cfg_btn)
        cfg_layout.addLayout(cfg_btns)

        # --- 1.4.2 Điều khiển trạng thái Socket Server ---
        ctrl_card = QFrame()
        ctrl_card.setObjectName("Card")
        ctrl_layout = QVBoxLayout(ctrl_card)
        ctrl_layout.setContentsMargins(18, 16, 18, 16)
        ctrl_layout.setSpacing(10)

        t2 = QLabel("1.4.2. Điều khiển dịch vụ Socket Server")
        t2.setObjectName("SectionTitle")
        ctrl_layout.addWidget(t2)

        info_form = QFormLayout()
        self.state_badge = QLabel("ĐANG KIỂM TRA...")
        self.listen_lbl = QLabel("-")
        self.uptime_lbl = QLabel("00:00:00")
        info_form.addRow("Trạng thái:", self.state_badge)
        info_form.addRow("Đang lắng nghe:", self.listen_lbl)
        info_form.addRow("Thời gian chạy:", self.uptime_lbl)
        ctrl_layout.addLayout(info_form)

        ctrl_btns = QHBoxLayout()
        self.start_btn = QPushButton("Khởi động")
        self.start_btn.setObjectName("SuccessBtn")
        self.start_btn.clicked.connect(self._start_server)

        self.stop_btn = QPushButton("Dừng Server")
        self.stop_btn.setObjectName("DangerBtn")
        self.stop_btn.clicked.connect(self._stop_server)

        self.restart_btn = QPushButton("Khởi động lại")
        self.restart_btn.setObjectName("WarningBtn")
        self.restart_btn.clicked.connect(self._restart_server)

        ctrl_btns.addWidget(self.start_btn)
        ctrl_btns.addWidget(self.stop_btn)
        ctrl_btns.addWidget(self.restart_btn)
        ctrl_layout.addLayout(ctrl_btns)

        top_row.addWidget(cfg_card, 3)
        top_row.addWidget(ctrl_card, 2)
        root.addLayout(top_row)

        # --- 1.4.3 Thống kê băng thông & kết nối thời gian thực ---
        stats_row = QHBoxLayout()
        stats_row.setSpacing(10)
        self.stat_conn_val = self._create_stat_box(stats_row, "Kết nối đang mở")
        self.stat_in_val = self._create_stat_box(stats_row, "Tổng dữ liệu nhận")
        self.stat_out_val = self._create_stat_box(stats_row, "Tổng dữ liệu gửi")
        self.stat_rate_val = self._create_stat_box(stats_row, "Băng thông (Nhận / Gửi)")
        root.addLayout(stats_row)

        mon_bar = QHBoxLayout()
        t3 = QLabel("1.4.3. Danh sách kết nối Socket & Heartbeat thời gian thực")
        t3.setObjectName("SectionTitle")

        self.auto_refresh_cb = QCheckBox("Tự động cập nhật (2.5s)")
        self.auto_refresh_cb.setChecked(True)
        self.auto_refresh_cb.toggled.connect(
            lambda on: self._timer.start() if on else self._timer.stop()
        )

        refresh_btn = QPushButton("Làm mới ngay")
        refresh_btn.clicked.connect(self.refresh_monitoring)

        kick_btn = QPushButton("Ngắt kết nối đã chọn")
        kick_btn.setObjectName("DangerBtn")
        kick_btn.clicked.connect(self._kick_selected)

        mon_bar.addWidget(t3)
        mon_bar.addStretch()
        mon_bar.addWidget(self.auto_refresh_cb)
        mon_bar.addWidget(refresh_btn)
        mon_bar.addWidget(kick_btn)
        root.addLayout(mon_bar)

        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels(
            [
                "Mã kết nối",
                "Giao thức",
                "Địa chỉ IP",
                "Tài khoản",
                "Vai trò",
                "Ping (ms)",
                "Heartbeat",
                "Đã nhận / Đã gửi",
                "Tốc độ (In / Out)",
            ]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        hdr = self.table.horizontalHeader()
        for col in range(9):
            hdr.setSectionResizeMode(
                col, QHeaderView.Stretch if col in (2, 3, 7, 8) else QHeaderView.ResizeToContents
            )
        root.addWidget(self.table, 1)

    def _create_stat_box(self, parent_layout: QHBoxLayout, title_txt: str) -> QLabel:
        box = QFrame()
        box.setObjectName("StatCard")
        bl = QVBoxLayout(box)
        bl.setContentsMargins(14, 10, 14, 10)
        bl.setSpacing(2)
        lbl = QLabel(title_txt)
        lbl.setObjectName("MutedText")
        val = QLabel("0")
        val.setStyleSheet("font-size: 16px; font-weight: 800; color: #0f172a;")
        bl.addWidget(lbl)
        bl.addWidget(val)
        parent_layout.addWidget(box, 1)
        return val

    def load_network_config(self) -> None:
        try:
            cfg = admin_controller.get_network_config()
            self.api_host_edit.setText(str(cfg.get("api_host", "127.0.0.1")))
            self.api_port_spin.setValue(int(cfg.get("api_port", 8000)))
            self.socket_host_edit.setText(str(cfg.get("socket_host", "0.0.0.0")))
            self.socket_port_spin.setValue(int(cfg.get("socket_port", 9000)))
        except APIError:
            pass

    def _save_config(self) -> None:
        try:
            res = admin_controller.save_network_config(
                api_host=self.api_host_edit.text(),
                api_port=self.api_port_spin.value(),
                socket_host=self.socket_host_edit.text(),
                socket_port=self.socket_port_spin.value(),
            )
            QMessageBox.information(self, "Lưu cấu hình thành công", str(res.get("message") or "Đã lưu."))
            self.refresh_monitoring()
        except APIError as err:
            QMessageBox.critical(self, "Cấu hình không hợp lệ", err.message)

    def _start_server(self) -> None:
        try:
            admin_controller.start_socket_server()
            self.refresh_monitoring()
        except APIError as err:
            QMessageBox.critical(self, "Không thể khởi động Socket Server", err.message)

    def _stop_server(self) -> None:
        ans = QMessageBox.question(
            self,
            "Xác nhận dừng Socket Server (1.4.2)",
            "Dừng Socket Server sẽ tạm ngắt kết nối real-time của tất cả máy trạm đang mở.\n"
            "Bạn vẫn có thể khởi động lại ngay trên màn hình này (REST API vẫn hoạt động).",
            QMessageBox.Yes | QMessageBox.No,
        )
        if ans != QMessageBox.Yes:
            return
        try:
            admin_controller.stop_socket_server()
            self.refresh_monitoring()
        except APIError as err:
            QMessageBox.critical(self, "Không thể dừng Socket Server", err.message)

    def _restart_server(self) -> None:
        try:
            admin_controller.restart_socket_server()
            self.refresh_monitoring()
        except APIError as err:
            QMessageBox.critical(self, "Không thể khởi động lại", err.message)

    def refresh_monitoring(self) -> None:
        try:
            data = admin_controller.get_connections_overview()
        except APIError:
            return

        st = data.get("status") or {}
        running = bool(st.get("running"))
        if running:
            self.state_badge.setText("● RUNNING (Đang chạy)")
            self.state_badge.setStyleSheet("color: #15803d; font-weight: 800;")
            self.listen_lbl.setText(f"{st.get('host')}:{st.get('port')}")
        else:
            self.state_badge.setText("■ STOPPED (Đã dừng)")
            self.state_badge.setStyleSheet("color: #dc2626; font-weight: 800;")
            self.listen_lbl.setText("Chưa mở cổng")

        self.uptime_lbl.setText(format_uptime(int(st.get("uptime_seconds", 0))))
        self.start_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)

        conn_cnt = int(st.get("connection_count", 0))
        auth_cnt = int(st.get("authenticated_count", 0))
        self.stat_conn_val.setText(f"{conn_cnt} ({auth_cnt} xác thực)")
        self.stat_in_val.setText(format_bytes(data.get("total_bytes_in", 0)))
        self.stat_out_val.setText(format_bytes(data.get("total_bytes_out", 0)))
        self.stat_rate_val.setText(
            f"↓ {format_bps(data.get('total_rate_in_bps', 0))}  |  "
            f"↑ {format_bps(data.get('total_rate_out_bps', 0))}"
        )

        selected_id = self._selected_connection_id()
        self._connections = data.get("connections") or []
        self.table.setRowCount(len(self._connections))
        restore_row = -1

        for row, c in enumerate(self._connections):
            cid = str(c.get("connection_id", ""))
            if cid == selected_id:
                restore_row = row
            user_txt = (
                f"{c.get('username')} ({c.get('full_name')})"
                if c.get("authenticated")
                else "Chưa xác thực"
            )
            ping = c.get("latency_ms")
            ping_txt = f"{ping:.1f}" if isinstance(ping, (int, float)) else "-"
            hb_sec = float(c.get("seconds_since_heartbeat", 0))
            io_txt = f"{format_bytes(c.get('bytes_in', 0))} / {format_bytes(c.get('bytes_out', 0))}"
            rate_txt = f"↓{format_bps(c.get('rate_in_bps', 0))} ↑{format_bps(c.get('rate_out_bps', 0))}"

            vals = [
                cid,
                str(c.get("transport", "")),
                str(c.get("address", "")),
                user_txt,
                str(c.get("role_code") or "-"),
                ping_txt,
                f"{hb_sec:.1f}s trước",
                io_txt,
                rate_txt,
            ]
            for col, v in enumerate(vals):
                item = QTableWidgetItem(v)
                if col in (0, 1, 4, 5, 6):
                    item.setTextAlignment(Qt.AlignCenter)
                if col == 6 and hb_sec > 15:
                    item.setForeground(QColor("#d97706"))
                self.table.setItem(row, col, item)

        if restore_row >= 0:
            self.table.selectRow(restore_row)

    def _selected_connection_id(self) -> str | None:
        row = self.table.currentRow()
        if 0 <= row < len(self._connections):
            return str(self._connections[row].get("connection_id"))
        return None

    def _kick_selected(self) -> None:
        cid = self._selected_connection_id()
        if not cid:
            QMessageBox.information(self, "Chưa chọn kết nối", "Vui lòng chọn một kết nối trong bảng.")
            return
        try:
            admin_controller.kick_connection(cid)
            self.refresh_monitoring()
        except APIError as err:
            QMessageBox.warning(self, "Không thể ngắt kết nối", err.message)

