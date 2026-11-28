from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from server.core.deps import CurrentUser
from server.core.exceptions import BadRequestError
from server.models import KnowledgeChapter, Subject
from server.schemas.khoa import (
    ChapterOut, MatrixOut, QuestionOut, SubjectOut,
)
from server.services import khoa_service


def subject_out(item) -> SubjectOut:
    return SubjectOut.model_validate(item)


def chapter_out(item) -> ChapterOut:
    return ChapterOut.model_validate(item)


def question_out(item) -> QuestionOut:
    data = QuestionOut.model_validate(item)
    data.subject_code = item.subject.code
    data.subject_name = item.subject.name
    data.chapter_name = item.chapter.name
    return data


def list_subjects(db: Session, keyword: str = "") -> list[SubjectOut]:
    return [subject_out(i) for i in khoa_service.list_subjects(db, keyword)]


def create_subject(db: Session, data): return subject_out(khoa_service.create_subject(db, data))
def update_subject(db: Session, subject_id: int, data): return subject_out(khoa_service.update_subject(db, subject_id, data))
def delete_subject(db: Session, subject_id: int) -> dict:
    khoa_service.delete_subject(db, subject_id)
    return {"message": "Đã xóa học phần"}


def list_chapters(db: Session, subject_id: Optional[int] = None) -> list[ChapterOut]:
    return [chapter_out(i) for i in khoa_service.list_chapters(db, subject_id)]


def create_chapter(db: Session, data): return chapter_out(khoa_service.create_chapter(db, data))
def update_chapter(db: Session, chapter_id: int, data): return chapter_out(khoa_service.update_chapter(db, chapter_id, data))
def reorder_chapters(db: Session, subject_id: int, ordered_ids: list[int]) -> list[ChapterOut]:
    return [chapter_out(i) for i in khoa_service.reorder_chapters(db, subject_id, ordered_ids)]
def delete_chapter(db: Session, chapter_id: int) -> dict:
    khoa_service.delete_chapter(db, chapter_id)
    return {"message": "Đã xóa chương kiến thức"}


def list_questions(db: Session, subject_id: Optional[int], chapter_id: Optional[int],
                   difficulty: Optional[str], keyword: str = "") -> list[QuestionOut]:
    return [question_out(i) for i in khoa_service.list_questions(db, subject_id, chapter_id, difficulty, keyword)]


def create_question(db: Session, data, current: CurrentUser): return question_out(khoa_service.create_question(db, data, current.user.id))
def update_question(db: Session, question_id: int, data): return question_out(khoa_service.update_question(db, question_id, data))
def set_question_active(db: Session, question_id: int, is_active: bool):
    return question_out(khoa_service.set_question_active(db, question_id, is_active))
def delete_question(db: Session, question_id: int) -> dict:
    khoa_service.delete_question(db, question_id)
    return {"message": "Đã xóa câu hỏi"}


def import_questions(db: Session, filename: str, content: bytes, created_by: int) -> dict:
    raw_rows = khoa_service.parse_import_file(filename, content)
    imported = 0
    errors = []
    for index, row in enumerate(raw_rows, start=2):
        try:
            subject = db.scalar(select(Subject).where(Subject.code == row["subject_code"]))
            if subject is None:
                raise BadRequestError("Không tìm thấy mã môn")
            chapter = db.scalar(
                select(KnowledgeChapter).where(
                    KnowledgeChapter.subject_id == subject.id,
                    KnowledgeChapter.name == row["chapter"],
                )
            )
            if chapter is None:
                raise BadRequestError("Không tìm thấy chương kiến thức")
            if row["question_type"] not in khoa_service.QUESTION_TYPES:
                raise BadRequestError("Dạng câu hỏi không hợp lệ")
            if row["difficulty"] not in khoa_service.DIFFICULTIES:
                raise BadRequestError("Độ khó không hợp lệ")
            if not row["content"]:
                raise BadRequestError("Thiếu nội dung câu hỏi")
            from server.schemas.khoa import QuestionBase
            data = QuestionBase(
                subject_id=subject.id,
                chapter_id=chapter.id,
                question_type=row["question_type"],
                difficulty=row["difficulty"],
                content=row["content"],
                options=row["options"],
                answer=row["answer"],
                explanation=row["explanation"],
                is_active=True,
            )
            khoa_service.create_question(db, data, created_by)
            imported += 1
        except Exception as exc:
            errors.append({"row": index, "error": str(exc)})
    db.flush()
    return {"imported": imported, "errors": errors, "total": len(raw_rows)}


def list_matrices(db: Session, subject_id: Optional[int] = None) -> list[MatrixOut]:
    return [MatrixOut.model_validate(i) for i in khoa_service.list_matrices(db, subject_id)]


def create_matrix(db: Session, data): return MatrixOut.model_validate(khoa_service.create_matrix(db, data))
def delete_matrix(db: Session, matrix_id: int) -> dict:
    khoa_service.delete_matrix(db, matrix_id)
    return {"message": "Đã xóa ma trận câu hỏi"}
