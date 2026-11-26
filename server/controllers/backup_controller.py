"""Controller sao lưu & phục hồi dữ liệu (1.5) - Admin."""
from datetime import datetime

from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse

from server.core.exceptions import BadRequestError
from server.schemas.backup import BackupFileOut, RestoreResult
from server.schemas.common import MessageResponse
from server.services import backup_service

MAX_UPLOAD_BYTES = 200 * 1024 * 1024


def list_backups() -> list[BackupFileOut]:
    return [BackupFileOut(**item) for item in backup_service.list_backups()]


def create_backup() -> BackupFileOut:
    path = backup_service.create_backup()
    stat = path.stat()
    return BackupFileOut(filename=path.name, size_bytes=stat.st_size,
                         created_at=datetime.fromtimestamp(stat.st_mtime))


def download(filename: str) -> FileResponse:
    path = backup_service.get_backup_path(filename)
    return FileResponse(path, media_type="application/sql", filename=path.name)


def delete(filename: str) -> MessageResponse:
    backup_service.delete_backup(filename)
    return MessageResponse(message=f"Đã xóa tệp sao lưu '{filename}'")


def restore_from_server_file(filename: str) -> RestoreResult:
    count, safety = backup_service.restore_from_file(filename)
    return RestoreResult(message=f"Phục hồi dữ liệu từ '{filename}' thành công",
                         statements_executed=count, safety_backup=safety)


async def restore_from_upload(file: UploadFile) -> RestoreResult:
    if not (file.filename or "").lower().endswith(".sql"):
        raise BadRequestError("Chỉ chấp nhận tệp sao lưu định dạng .sql")
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise BadRequestError("Tệp sao lưu quá lớn (tối đa 200MB)")
    try:
        script = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise BadRequestError("Tệp sao lưu phải được mã hóa UTF-8") from exc
    count, safety = await run_in_threadpool(backup_service.restore_from_text, script)
    return RestoreResult(message=f"Phục hồi dữ liệu từ tệp '{file.filename}' thành công",
                         statements_executed=count, safety_backup=safety)
