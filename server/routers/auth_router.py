"""Router 1.1 - Xác thực và phiên đăng nhập (dùng chung cho 7 tác nhân)."""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from server.controllers import auth_controller
from server.core.deps import CurrentUser, get_current_user
from server.database.db import get_db
from server.schemas.auth import LoginRequest, LoginResponse, SessionInfo
from server.schemas.common import MessageResponse

router = APIRouter(prefix="/api/auth", tags=["1.1 Xác thực & phiên đăng nhập"])


@router.post("/login", response_model=LoginResponse, summary="1.1.1 Đăng nhập (1.1.3 chặn trùng phiên)")
def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    return auth_controller.login(db, req, request)


@router.post("/logout", response_model=MessageResponse, summary="1.1.2 Đăng xuất & đóng kết nối Socket")
def logout(current: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return auth_controller.logout(db, current)


@router.get("/session", response_model=SessionInfo, summary="Kiểm tra phiên hiện tại")
def session_info(current: CurrentUser = Depends(get_current_user)):
    return auth_controller.session_info(current)


@router.post("/heartbeat", summary="Heartbeat dự phòng qua REST")
def heartbeat(current: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return auth_controller.heartbeat(db, current)

