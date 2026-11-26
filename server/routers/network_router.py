"""Router 1.4 - Quản trị mạng (Admin)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from server.controllers import network_controller
from server.core.deps import CurrentUser, require_admin
from server.database.db import get_db
from server.schemas.common import MessageResponse
from server.schemas.network import ConnectionsResponse, NetworkConfig, NetworkConfigResponse, ServerStatus

router = APIRouter(prefix="/api/admin/network", tags=["1.4 Quản trị mạng (Admin)"])


@router.get("/config", response_model=NetworkConfigResponse, summary="1.4.1 Xem cấu hình IP/Port")
def get_config(_: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    return network_controller.get_config(db)


@router.put("/config", response_model=NetworkConfigResponse, summary="1.4.1 Lưu cấu hình IP/Port")
def save_config(cfg: NetworkConfig, _: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    return network_controller.save_config(db, cfg)


@router.get("/status", response_model=ServerStatus, summary="1.4.2 Trạng thái Socket Server")
def status(_: CurrentUser = Depends(require_admin)):
    return network_controller.status()


@router.post("/start", response_model=ServerStatus, summary="1.4.2 Khởi động Socket Server")
async def start(_: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    return await network_controller.start(db)


@router.post("/stop", response_model=ServerStatus, summary="1.4.2 Dừng Socket Server")
async def stop(_: CurrentUser = Depends(require_admin)):
    return await network_controller.stop()


@router.post("/restart", response_model=ServerStatus, summary="1.4.2 Khởi động lại Socket Server")
async def restart(_: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    return await network_controller.restart(db)


@router.get("/connections", response_model=ConnectionsResponse, summary="1.4.3 Danh sách kết nối & băng thông")
def connections(_: CurrentUser = Depends(require_admin)):
    return network_controller.connections()


@router.delete("/connections/{connection_id}", response_model=MessageResponse, summary="Ngắt 1 kết nối")
async def kick(connection_id: str, _: CurrentUser = Depends(require_admin)):
    return await network_controller.kick(connection_id)

