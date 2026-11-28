from pathlib import Path
from typing import Any, Optional

from client.api import khoa_api


class KhoaController:
    def subjects(self, keyword: str = "") -> list[dict[str, Any]]:
        return khoa_api.list_subjects(keyword)

    def save_subject(self, data: dict[str, Any], subject_id: Optional[int] = None) -> dict[str, Any]:
        return khoa_api.update_subject(subject_id, data) if subject_id else khoa_api.create_subject(data)

    def delete_subject(self, subject_id: int) -> dict[str, Any]:
        return khoa_api.delete_subject(subject_id)

    def chapters(self, subject_id: Optional[int] = None) -> list[dict[str, Any]]:
        return khoa_api.list_chapters(subject_id)

    def save_chapter(self, data: dict[str, Any], chapter_id: Optional[int] = None) -> dict[str, Any]:
        return khoa_api.update_chapter(chapter_id, data) if chapter_id else khoa_api.create_chapter(data)

    def reorder_chapters(self, subject_id: int, ordered_ids: list[int]) -> list[dict[str, Any]]:
        return khoa_api.reorder_chapters(subject_id, ordered_ids)

    def delete_chapter(self, chapter_id: int) -> dict[str, Any]:
        return khoa_api.delete_chapter(chapter_id)

    def questions(
        self,
        subject_id: Optional[int] = None,
        chapter_id: Optional[int] = None,
        difficulty: Optional[str] = None,
        keyword: str = "",
    ) -> list[dict[str, Any]]:
        return khoa_api.list_questions(subject_id, chapter_id, difficulty, keyword)

    def save_question(self, data: dict[str, Any], question_id: Optional[int] = None) -> dict[str, Any]:
        return khoa_api.update_question(question_id, data) if question_id else khoa_api.create_question(data)

    def set_question_visibility(self, question_id: int, is_active: bool) -> dict[str, Any]:
        return khoa_api.set_question_visibility(question_id, is_active)

    def delete_question(self, question_id: int) -> dict[str, Any]:
        return khoa_api.delete_question(question_id)

    def import_questions(self, file_path: Path) -> dict[str, Any]:
        return khoa_api.import_questions(file_path)

    def matrices(self, subject_id: Optional[int] = None) -> list[dict[str, Any]]:
        return khoa_api.list_matrices(subject_id)

    def create_matrix(self, data: dict[str, Any]) -> dict[str, Any]:
        return khoa_api.create_matrix(data)

    def delete_matrix(self, matrix_id: int) -> dict[str, Any]:
        return khoa_api.delete_matrix(matrix_id)


khoa_controller = KhoaController()
