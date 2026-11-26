"""Bảng màu, QSS Stylesheet và hàm định dạng hiển thị dùng chung trên Desktop Client."""

ROLE_ACCENT_COLORS = {
    "ADMIN": "#b85d19",
    "CTSV": "#1d4ed8",
    "DAOTAO": "#0f766e",
    "KHOA": "#6d28d9",
    "KHAOTHI": "#be123c",
    "COITHI": "#0369a1",
    "SINHVIEN": "#15803d",
}

APP_STYLESHEET = """
QMainWindow, QWidget#AppRoot {
    background-color: #f4f6f9;
    color: #1e293b;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}

QFrame#Card {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
}

QFrame#StatCard {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
}

QLabel#PageTitle {
    font-size: 18px;
    font-weight: 700;
    color: #0f172a;
}

QLabel#SectionTitle {
    font-size: 14px;
    font-weight: 700;
    color: #1e293b;
}

QLabel#MutedText {
    color: #64748b;
    font-size: 12px;
}

QLineEdit, QComboBox, QSpinBox {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 10px;
    min-height: 20px;
    color: #0f172a;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #2563eb;
}

QPushButton {
    background-color: #e2e8f0;
    color: #1e293b;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 7px 14px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #cbd5e1;
}

QPushButton:disabled {
    background-color: #f1f5f9;
    color: #94a3b8;
    border-color: #e2e8f0;
}

QPushButton#PrimaryBtn {
    background-color: #1d4ed8;
    color: #ffffff;
    border: 1px solid #1e40af;
}

QPushButton#PrimaryBtn:hover {
    background-color: #1e40af;
}

QPushButton#SuccessBtn {
    background-color: #15803d;
    color: #ffffff;
    border: 1px solid #166534;
}

QPushButton#SuccessBtn:hover {
    background-color: #166534;
}

QPushButton#WarningBtn {
    background-color: #d97706;
    color: #ffffff;
    border: 1px solid #b45309;
}

QPushButton#WarningBtn:hover {
    background-color: #b45309;
}

QPushButton#DangerBtn {
    background-color: #dc2626;
    color: #ffffff;
    border: 1px solid #b91c1c;
}

QPushButton#DangerBtn:hover {
    background-color: #b91c1c;
}

QTableWidget {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    gridline-color: #f1f5f9;
    selection-background-color: #dbeafe;
    selection-color: #0f172a;
}

QHeaderView::section {
    background-color: #f8fafc;
    color: #334155;
    font-weight: 700;
    padding: 8px;
    border: none;
    border-bottom: 1px solid #e2e8f0;
    border-right: 1px solid #f1f5f9;
}
"""


def format_bytes(num_bytes: int | float) -> str:
    val = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if abs(val) < 1024.0 or unit == "GB":
            return f"{int(val)} B" if unit == "B" else f"{val:.1f} {unit}"
        val /= 1024.0
    return f"{val:.1f} GB"


def format_bps(bps: float) -> str:
    return f"{format_bytes(bps)}/s"


def format_uptime(seconds: int) -> str:
    h, rem = divmod(max(0, int(seconds)), 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

