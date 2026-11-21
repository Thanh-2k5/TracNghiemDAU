import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget


class MainWindow(QMainWindow):
    """Cửa sổ chính của ứng dụng Desktop Client (PySide6)."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hệ Thống Thi Trắc Nghiệm DAU")
        self.resize(1024, 720)

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        title_label = QLabel("HỆ THỐNG THI TRẮC NGHIỆM DAU")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title_label)

        self.setCentralWidget(central_widget)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
