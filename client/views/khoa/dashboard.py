"""Khung làm việc của Khoa (tái sử dụng 1.1 & 1.2 theo mục 4.0)."""
from PySide6.QtWidgets import QWidget

from client.views.common.role_shell import RoleWorkspaceShell
from client.views.khoa.chapter_view import ChapterView
from client.views.khoa.question_view import QuestionBankView
from client.views.khoa.subject_view import SubjectView


class KhoaDashboardView(RoleWorkspaceShell):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("KHOA", "Khoa chuyên môn", parent)
        self.add_page(
            "4.1  Môn học / Học phần",
            "4.1. Quản lý môn học / học phần",
            SubjectView(),
        )
        self.add_page(
            "4.2  Chương kiến thức",
            "4.2. Quản lý chương kiến thức",
            ChapterView(),
        )
        self.add_page(
            "4.3  Ngân hàng câu hỏi",
            "4.3. Quản lý ngân hàng câu hỏi 7 dạng",
            QuestionBankView(),
        )
        self.add_shared_profile_page("4.0")

