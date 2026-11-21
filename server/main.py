import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from server.core.config import settings
from server.socket_server.manager import socket_manager

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend REST API & Real-time Socket Server cho Hệ Thống Thi Trắc Nghiệm DAU",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health Check"])
def health_check():
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
    }


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await socket_manager.connect(client_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # Xử lý gói tin JSON real-time từ Client gửi lên
            await socket_manager.send_json(
                client_id,
                {"event": "ack", "client_id": client_id, "received": data},
            )
    except WebSocketDisconnect:
        socket_manager.disconnect(client_id)


def main():
    uvicorn.run(
        "server.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )


if __name__ == "__main__":
    main()
