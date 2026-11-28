"""Import toàn bộ model để SQLAlchemy đăng ký metadata (create_all / quan hệ)."""
from server.models.role import Role
from server.models.user import User
from server.models.user_session import UserSession
from server.models.system_config import SystemConfig
from server.models.subject import Subject
from server.models.knowledge_chapter import KnowledgeChapter
from server.models.question import Question
from server.models.question_matrix import QuestionMatrix

__all__ = [
    "Role", "User", "UserSession", "SystemConfig", "Subject",
    "KnowledgeChapter", "Question", "QuestionMatrix",
]

