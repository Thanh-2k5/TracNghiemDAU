"""Router 1.5 - Sao lưu & phục hồi dữ liệu (Admin)."""
from fastapi import APIRouter, Depends, File, UploadFile

from server.controllers import backup_controller
from server.core.deps import CurrentUser, require_admin
from server.schemas.backup import BackupFileOut, RestoreResult
from server.schemas.common import MessageResponse

router = APIRouter(prefix="/api/admin/backups", tags=["1.5 Sao lưu & phục hồi (Admin)"])


@router.get("", response_model=list[BackupFileOut], summary="Danh sách tệp sao lưu trên Server")
def list_backups(_: CurrentUser = Depends(require_admin)):
    return backup_controller.list_backups()


@router.post("", response_model=BackupFileOut, status_code=201, summary="1.5.1 Sao lưu CSDL ra tệp .sql")
def create_backup(_: CurrentUser = Depends(require_admin)):
    return backup_controller.create_backup()


@router.post("/restore", response_model=RestoreResult, summary="1.5.1 Phục hồi từ tệp .sql tải lên")
async def restore_upload(file: UploadFile = File(...), _: CurrentUser = Depends(require_admin)):
    return await backup_controller.restore_from_upload(file)


@router.get("/{filename}/download", summary="Tải tệp sao lưu về máy")
def download(filename: str, _: CurrentUser = Depends(require_admin)):
    return backup_controller.download(filename)


@router.post("/{filename}/restore", response_model=RestoreResult, summary="1.5.1 Phục hồi từ tệp trên Server")
def restore_server_file(filename: str, _: CurrentUser = Depends(require_admin)):
    return backup_controller.restore_from_server_file(filename)


@router.delete("/{filename}", response_model=MessageResponse, summary="Xóa tệp sao lưu")
def delete(filename: str, _: CurrentUser = Depends(require_admin)):
    return backup_controller.delete(filename)

