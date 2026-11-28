import json
from io import BytesIO
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from server.core.exceptions import BadRequestError, ConflictError, NotFoundError
from server.models import KnowledgeChapter, Question, QuestionMatrix, Subject
from server.schemas.khoa import ChapterBase, MatrixCreate, QuestionBase, SubjectBase


QUESTION_TYPES = {
    "Single Choice", "True/False", "Multiple Choice", "Matching",
    "Drag & Drop", "List", "Fill in the Blank",
}
DIFFICULTIES = {"Dễ", "TB", "Khó"}


def list_subjects(db: Session, keyword: str = "") -> list[Subject]:
    stmt = select(Subject)
    if keyword:
        text = f"%{keyword.strip()}%"
        stmt = stmt.where(Subject.code.ilike(text) | Subject.name.ilike(text))
    return list(db.scalars(stmt.order_by(Subject.code)))


def get_subject(db: Session, subject_id: int) -> Subject:
    item = db.get(Subject, subject_id)
    if item is None:
        raise NotFoundError("Không tìm thấy học phần")
    return item


def create_subject(db: Session, data: SubjectBase) -> Subject:
    if db.scalar(select(Subject).where(Subject.code == data.code.strip())):
        raise ConflictError("Mã học phần đã tồn tại")
    item = Subject(**data.model_dump())
    item.code = item.code.strip()
    item.name = item.name.strip()
    db.add(item)
    db.flush()
    db.commit()
    return item


def update_subject(db: Session, subject_id: int, data: SubjectBase) -> Subject:
    item = get_subject(db, subject_id)
    code_owner = db.scalar(select(Subject.id).where(Subject.code == data.code.strip(), Subject.id != subject_id))
    if code_owner is not None:
        raise ConflictError("Mã học phần đã tồn tại")
    for key, value in data.model_dump().items():
        setattr(item, key, value)
    item.code = item.code.strip()
    item.name = item.name.strip()
    db.flush()
    db.commit()
    return item


def delete_subject(db: Session, subject_id: int) -> None:
    item = get_subject(db, subject_id)
    db.delete(item)
    db.flush()
    db.commit()


def list_chapters(db: Session, subject_id: Optional[int] = None) -> list[KnowledgeChapter]:
    stmt = select(KnowledgeChapter)
    if subject_id:
        stmt = stmt.where(KnowledgeChapter.subject_id == subject_id)
    return list(db.scalars(stmt.order_by(KnowledgeChapter.subject_id, KnowledgeChapter.sort_order)))


def get_chapter(db: Session, chapter_id: int) -> KnowledgeChapter:
    item = db.get(KnowledgeChapter, chapter_id)
    if item is None:
        raise NotFoundError("Không tìm thấy chương kiến thức")
    return item


def create_chapter(db: Session, data: ChapterBase) -> KnowledgeChapter:
    get_subject(db, data.subject_id)
    item = KnowledgeChapter(**data.model_dump())
    item.name = item.name.strip()
    db.add(item)
    db.flush()
    db.commit()
    return item


def update_chapter(db: Session, chapter_id: int, data: ChapterBase) -> KnowledgeChapter:
    item = get_chapter(db, chapter_id)
    get_subject(db, data.subject_id)
    for key, value in data.model_dump().items():
        setattr(item, key, value)
    item.name = item.name.strip()
    db.flush()
    db.commit()
    return item


def delete_chapter(db: Session, chapter_id: int) -> None:
    item = get_chapter(db, chapter_id)
    if db.scalar(select(Question.id).where(Question.chapter_id == chapter_id).limit(1)):
        raise ConflictError("Không thể xóa chương đang có câu hỏi")
    db.delete(item)
    db.flush()
    db.commit()


def reorder_chapters(db: Session, subject_id: int, ordered_ids: list[int]) -> list[KnowledgeChapter]:
    get_subject(db, subject_id)
    chapters = list(db.scalars(select(KnowledgeChapter).where(KnowledgeChapter.subject_id == subject_id)))
    by_id = {chapter.id: chapter for chapter in chapters}
    if set(ordered_ids) != set(by_id) or len(ordered_ids) != len(by_id):
        raise BadRequestError("Danh sách chương sắp xếp không hợp lệ")
    for sort_order, chapter_id in enumerate(ordered_ids, start=1):
        by_id[chapter_id].sort_order = sort_order
    db.flush()
    db.commit()
    return list(db.scalars(select(KnowledgeChapter).where(KnowledgeChapter.subject_id == subject_id).order_by(KnowledgeChapter.sort_order)))


def list_questions(db: Session, subject_id: Optional[int], chapter_id: Optional[int],
                   difficulty: Optional[str], keyword: str = "") -> list[Question]:
    stmt = select(Question)
    if subject_id:
        stmt = stmt.where(Question.subject_id == subject_id)
    if chapter_id:
        stmt = stmt.where(Question.chapter_id == chapter_id)
    if difficulty:
        stmt = stmt.where(Question.difficulty == difficulty)
    if keyword:
        stmt = stmt.where(Question.content.ilike(f"%{keyword.strip()}%"))
    return list(db.scalars(stmt.order_by(Question.id.desc())))


def get_question(db: Session, question_id: int) -> Question:
    item = db.get(Question, question_id)
    if item is None:
        raise NotFoundError("Không tìm thấy câu hỏi")
    return item


def create_question(db: Session, data: QuestionBase, created_by: Optional[int] = None) -> Question:
    get_subject(db, data.subject_id)
    chapter = get_chapter(db, data.chapter_id)
    if chapter.subject_id != data.subject_id:
        raise BadRequestError("Chương không thuộc học phần đã chọn")
    item = Question(**data.model_dump(), created_by=created_by)
    db.add(item)
    db.flush()
    db.commit()
    return item


def update_question(db: Session, question_id: int, data: QuestionBase) -> Question:
    item = get_question(db, question_id)
    get_subject(db, data.subject_id)
    chapter = get_chapter(db, data.chapter_id)
    if chapter.subject_id != data.subject_id:
        raise BadRequestError("Chương không thuộc học phần đã chọn")
    for key, value in data.model_dump().items():
        setattr(item, key, value)
    db.flush()
    db.commit()
    return item


def set_question_active(db: Session, question_id: int, is_active: bool) -> Question:
    item = get_question(db, question_id)
    item.is_active = is_active
    db.flush()
    db.commit()
    return item


def delete_question(db: Session, question_id: int) -> None:
    db.delete(get_question(db, question_id))
    db.flush()
    db.commit()


def list_matrices(db: Session, subject_id: Optional[int] = None) -> list[QuestionMatrix]:
    stmt = select(QuestionMatrix)
    if subject_id:
        stmt = stmt.where(QuestionMatrix.subject_id == subject_id)
    return list(db.scalars(stmt.order_by(QuestionMatrix.id.desc())))


def create_matrix(db: Session, data: MatrixCreate) -> QuestionMatrix:
    get_subject(db, data.subject_id)
    item = QuestionMatrix(**data.model_dump())
    db.add(item)
    db.flush()
    db.commit()
    return item


def delete_matrix(db: Session, matrix_id: int) -> None:
    item = db.get(QuestionMatrix, matrix_id)
    if item is None:
        raise NotFoundError("Không tìm thấy ma trận")
    db.delete(item)
    db.flush()
    db.commit()


def parse_import_file(filename: str, content: bytes) -> list[dict]:
    ext = filename.lower().rsplit(".", 1)[-1]
    rows: list[dict] = []
    if ext == "xlsx":
        try:
            import openpyxl
        except ImportError as exc:
            raise BadRequestError("Thiếu thư viện openpyxl để đọc Excel") from exc
        wb = openpyxl.load_workbook(BytesIO(content), read_only=True)
        ws = wb.active
        headers = [str(c.value).strip() if c.value is not None else "" for c in next(ws.iter_rows())]
        for values in ws.iter_rows(min_row=2, values_only=True):
            if not any(v is not None for v in values):
                continue
            rows.append(dict(zip(headers, values)))
    elif ext == "docx":
        try:
            from docx import Document
        except ImportError as exc:
            raise BadRequestError("Thiếu thư viện python-docx để đọc Word") from exc
        document = Document(BytesIO(content))
        block: dict[str, str] = {}
        for para in list(document.paragraphs) + [None]:
            text = para.text.strip() if para is not None else ""
            if text:
                if ":" in text:
                    key, val = text.split(":", 1)
                    block[key.strip().lower().replace(" ", "_")] = val.strip()
                else:
                    block["content"] = (block.get("content", "") + "\n" + text).strip()
            elif block:
                rows.append(block)
                block = {}
    else:
        raise BadRequestError("Chỉ hỗ trợ tệp Excel (.xlsx) hoặc Word (.docx)")

    normalized = []
    for raw in rows:
        def get(*names):
            for name in names:
                for key, value in raw.items():
                    if str(key).strip().lower().replace(" ", "_") == name:
                        return value
            return None

        options = get("options")
        answer = get("answer")
        if isinstance(options, str):
            try:
                options = json.loads(options)
            except json.JSONDecodeError:
                options = [item.strip() for item in options.split("|") if item.strip()]
        if isinstance(answer, str):
            try:
                answer = json.loads(answer)
            except json.JSONDecodeError:
                answer = answer
        normalized.append({
            "subject_code": str(get("subject_code", "mã_môn") or "").strip(),
            "chapter": str(get("chapter", "chương") or "").strip(),
            "question_type": str(get("question_type", "type", "dạng") or "Single Choice").strip(),
            "difficulty": str(get("difficulty", "độ_khó") or "TB").strip(),
            "content": str(get("content", "nội_dung", "câu_hỏi") or "").strip(),
            "options": options,
            "answer": answer,
            "explanation": get("explanation", "giải_thích"),
        })
    if not normalized:
        raise BadRequestError("Tệp không có dòng câu hỏi hợp lệ")
    return normalized
