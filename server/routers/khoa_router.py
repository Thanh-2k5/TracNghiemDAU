from typing import Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from server.controllers import khoa_controller
from server.core.deps import CurrentUser, require_roles
from server.core.constants import RoleCode
from server.database.db import get_db
from server.schemas.khoa import (
    ChapterBase, ChapterOut, MatrixCreate, MatrixOut, QuestionBase, QuestionOut, SubjectBase, SubjectOut,
)

router = APIRouter(prefix="/api/khoa", tags=["4.0-4.3 Quản lý Khoa"])
require_khoa = require_roles(RoleCode.KHOA, RoleCode.ADMIN)


@router.get("/subjects", response_model=list[SubjectOut])
def subjects(keyword: str = "", _: CurrentUser = Depends(require_khoa), db: Session = Depends(get_db)):
    return khoa_controller.list_subjects(db, keyword)


@router.post("/subjects", response_model=SubjectOut, status_code=201)
def create_subject(data: SubjectBase, _: CurrentUser = Depends(require_khoa), db: Session = Depends(get_db)):
    return khoa_controller.create_subject(db, data)


@router.put("/subjects/{subject_id}", response_model=SubjectOut)
def update_subject(subject_id: int, data: SubjectBase, _: CurrentUser = Depends(require_khoa), db: Session = Depends(get_db)):
    return khoa_controller.update_subject(db, subject_id, data)


@router.delete("/subjects/{subject_id}")
def delete_subject(subject_id: int, _: CurrentUser = Depends(require_khoa), db: Session = Depends(get_db)):
    return khoa_controller.delete_subject(db, subject_id)


@router.get("/chapters", response_model=list[ChapterOut])
def chapters(subject_id: Optional[int] = None, _: CurrentUser = Depends(require_khoa), db: Session = Depends(get_db)):
    return khoa_controller.list_chapters(db, subject_id)


@router.post("/chapters", status_code=201)
def create_chapter(data: ChapterBase, _: CurrentUser = Depends(require_khoa), db: Session = Depends(get_db)):
    return khoa_controller.create_chapter(db, data)


@router.put("/chapters/{chapter_id}")
def update_chapter(chapter_id: int, data: ChapterBase, _: CurrentUser = Depends(require_khoa), db: Session = Depends(get_db)):
    return khoa_controller.update_chapter(db, chapter_id, data)


@router.post("/subjects/{subject_id}/chapters/reorder")
def reorder_chapters(subject_id: int, ordered_ids: list[int], _: CurrentUser = Depends(require_khoa), db: Session = Depends(get_db)):
    return khoa_controller.reorder_chapters(db, subject_id, ordered_ids)


@router.delete("/chapters/{chapter_id}")
def delete_chapter(chapter_id: int, _: CurrentUser = Depends(require_khoa), db: Session = Depends(get_db)):
    return khoa_controller.delete_chapter(db, chapter_id)


@router.get("/questions", response_model=list[QuestionOut])
def questions(subject_id: Optional[int] = None, chapter_id: Optional[int] = None,
              difficulty: Optional[str] = Query(None, pattern=r"^(Dễ|TB|Khó)$"),
              keyword: str = "", _: CurrentUser = Depends(require_khoa), db: Session = Depends(get_db)):
    return khoa_controller.list_questions(db, subject_id, chapter_id, difficulty, keyword)


@router.post("/questions", response_model=QuestionOut, status_code=201)
def create_question(data: QuestionBase, current: CurrentUser = Depends(require_khoa), db: Session = Depends(get_db)):
    return khoa_controller.create_question(db, data, current)


@router.put("/questions/{question_id}", response_model=QuestionOut)
def update_question(question_id: int, data: QuestionBase, _: CurrentUser = Depends(require_khoa), db: Session = Depends(get_db)):
    return khoa_controller.update_question(db, question_id, data)


@router.patch("/questions/{question_id}/visibility", response_model=QuestionOut)
def set_question_visibility(question_id: int, is_active: bool, _: CurrentUser = Depends(require_khoa), db: Session = Depends(get_db)):
    return khoa_controller.set_question_active(db, question_id, is_active)


@router.delete("/questions/{question_id}")
def delete_question(question_id: int, _: CurrentUser = Depends(require_khoa), db: Session = Depends(get_db)):
    return khoa_controller.delete_question(db, question_id)


@router.post("/questions/import")
async def import_questions(file: UploadFile = File(...), current: CurrentUser = Depends(require_khoa), db: Session = Depends(get_db)):
    content = await file.read()
    return khoa_controller.import_questions(db, file.filename or "", content, current.user.id)


@router.get("/matrices", response_model=list[MatrixOut])
def matrices(subject_id: Optional[int] = None, _: CurrentUser = Depends(require_khoa), db: Session = Depends(get_db)):
    return khoa_controller.list_matrices(db, subject_id)


@router.post("/matrices", response_model=MatrixOut, status_code=201)
def create_matrix(data: MatrixCreate, _: CurrentUser = Depends(require_khoa), db: Session = Depends(get_db)):
    return khoa_controller.create_matrix(db, data)


@router.delete("/matrices/{matrix_id}")
def delete_matrix(matrix_id: int, _: CurrentUser = Depends(require_khoa), db: Session = Depends(get_db)):
    return khoa_controller.delete_matrix(db, matrix_id)
