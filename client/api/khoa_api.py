from pathlib import Path
from typing import Any, Optional

from client.api.http_client import api_client


def list_subjects(keyword: str = "") -> list[dict[str, Any]]:
    return api_client.get("/api/khoa/subjects", params={"keyword": keyword} if keyword else None)


def create_subject(payload: dict[str, Any]) -> dict[str, Any]:
    return api_client.post("/api/khoa/subjects", payload)


def update_subject(subject_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    return api_client.put(f"/api/khoa/subjects/{subject_id}", payload)


def delete_subject(subject_id: int) -> dict[str, Any]:
    return api_client.delete(f"/api/khoa/subjects/{subject_id}")


def list_chapters(subject_id: Optional[int] = None) -> list[dict[str, Any]]:
    params = {"subject_id": subject_id} if subject_id else None
    return api_client.get("/api/khoa/chapters", params=params)


def create_chapter(payload: dict[str, Any]) -> dict[str, Any]:
    return api_client.post("/api/khoa/chapters", payload)


def update_chapter(chapter_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    return api_client.put(f"/api/khoa/chapters/{chapter_id}", payload)


def reorder_chapters(subject_id: int, ordered_ids: list[int]) -> list[dict[str, Any]]:
    return api_client.post(f"/api/khoa/subjects/{subject_id}/chapters/reorder", ordered_ids)


def delete_chapter(chapter_id: int) -> dict[str, Any]:
    return api_client.delete(f"/api/khoa/chapters/{chapter_id}")


def list_questions(
    subject_id: Optional[int] = None,
    chapter_id: Optional[int] = None,
    difficulty: Optional[str] = None,
    keyword: str = "",
) -> list[dict[str, Any]]:
    params: dict[str, Any] = {}
    if subject_id: params["subject_id"] = subject_id
    if chapter_id: params["chapter_id"] = chapter_id
    if difficulty: params["difficulty"] = difficulty
    if keyword: params["keyword"] = keyword
    return api_client.get("/api/khoa/questions", params=params or None)


def create_question(payload: dict[str, Any]) -> dict[str, Any]:
    return api_client.post("/api/khoa/questions", payload)


def update_question(question_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    return api_client.put(f"/api/khoa/questions/{question_id}", payload)


def set_question_visibility(question_id: int, is_active: bool) -> dict[str, Any]:
    return api_client.request(
        "PATCH",
        f"/api/khoa/questions/{question_id}/visibility",
        params={"is_active": str(is_active).lower()},
    )


def delete_question(question_id: int) -> dict[str, Any]:
    return api_client.delete(f"/api/khoa/questions/{question_id}")


def import_questions(file_path: Path) -> dict[str, Any]:
    return api_client.upload_file("/api/khoa/questions/import", file_path)


def list_matrices(subject_id: Optional[int] = None) -> list[dict[str, Any]]:
    params = {"subject_id": subject_id} if subject_id else None
    return api_client.get("/api/khoa/matrices", params=params)


def create_matrix(payload: dict[str, Any]) -> dict[str, Any]:
    return api_client.post("/api/khoa/matrices", payload)


def delete_matrix(matrix_id: int) -> dict[str, Any]:
    return api_client.delete(f"/api/khoa/matrices/{matrix_id}")
