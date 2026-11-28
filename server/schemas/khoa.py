from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SubjectBase(BaseModel):
    code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=200)
    credits: int = Field(ge=1, le=20)
    exam_duration_minutes: int = Field(ge=1, le=600)
    description: Optional[str] = None
    is_active: bool = True


class SubjectOut(SubjectBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ChapterBase(BaseModel):
    subject_id: int
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    sort_order: int = Field(default=1, ge=1)


class ChapterOut(ChapterBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class QuestionBase(BaseModel):
    subject_id: int
    chapter_id: int
    question_type: str = Field(pattern=r"^(Single Choice|True/False|Multiple Choice|Matching|Drag & Drop|List|Fill in the Blank)$")
    difficulty: str = Field(pattern=r"^(Dễ|TB|Khó)$")
    content: str = Field(min_length=1)
    options: Optional[object] = None
    answer: Optional[object] = None
    explanation: Optional[str] = None
    is_active: bool = True


class QuestionOut(QuestionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    subject_code: Optional[str] = None
    subject_name: Optional[str] = None
    chapter_name: Optional[str] = None


class MatrixCreate(BaseModel):
    subject_id: int
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    matrix: dict


class MatrixOut(MatrixCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
