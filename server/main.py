"""Entry point Backend Server: FastAPI (REST API) + TCP/WebSocket Real-time Server."""
from contextlib import asynccontextmanager
from datetime import datetime
import logging

import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from server.core.config import settings
from server.core.exceptions import AppError
from server.database.db import session_scope
from server.database.init_db import init_database
from server.routers import (
    account_router,
    auth_router,
    backup_router,
    network_router,
    profile_router,
    ws_router,
)
from server.services import network_service, session_service
from server.socket_server.connection_manager import socket_manager
from server.socket_server.tcp_server import tcp_server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("server")


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_database()
    socket_manager.activity_callback = session_service.touch_session_by_id
    socket_manager.start_monitor()

    if settings.SOCKET_AUTO_START:
        with session_scope() as db:
            cfg = network_service.get_config(db)
        try:
            await tcp_server.start(cfg["socket_host"], cfg["socket_port"])
        except OSError as exc:
            logger.error(
                "Không thể tự khởi động Socket Server tại %s:%s (%s)",
                cfg["socket_host"],
                cfg["socket_port"],
                exc,
            )
    try:
        yield
    finally:
        await tcp_server.stop("Server đang tắt dịch vụ")
        await socket_manager.stop_monitor()


app = FastAPI(
    title=settings.APP_NAME,
    description="Backend REST API & Real-time Socket Server cho Hệ Thống Thi Trắc Nghiệm DAU",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "code": exc.code, **exc.extra},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError):
    first_msg = "Dữ liệu đầu vào không hợp lệ"
    for err in exc.errors():
        msg = str(err.get("msg", ""))
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, "):]
        if msg:
            first_msg = msg
            break
    return JSONResponse(
        status_code=422,
        content={"detail": first_msg, "code": "VALIDATION_ERROR"},
    )


@app.get("/", tags=["Health Check"])
@app.get("/api/health", tags=["Health Check"])
def health_check():
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "server_time": datetime.now(),
        "socket": tcp_server.status(),
    }


app.include_router(auth_router.router)
app.include_router(profile_router.router)
app.include_router(account_router.router)
app.include_router(network_router.router)
app.include_router(backup_router.router)
app.include_router(ws_router.router)


def main():
    host, port = settings.API_HOST, settings.API_PORT
    try:
        init_database()
        with session_scope() as db:
            cfg = network_service.get_config(db)
            host, port = cfg["api_host"], cfg["api_port"]
    except Exception as exc:  # noqa: BLE001
        logger.warning("Sử dụng API_HOST/API_PORT từ .env (%s)", exc)

    uvicorn.run(
        "server.main:app",
        host=host,
        port=port,
        reload=settings.DEBUG,
    )


if __name__ == "__main__":
    main()
