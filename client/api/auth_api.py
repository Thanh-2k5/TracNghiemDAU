"""Các hàm gọi REST API cho module 1.1 (Xác thực) và 1.2 (Thông tin cá nhân)."""
import platform
import socket
from typing import Any

from client.api.http_client import api_client


def _client_info() -> str:
    return f"Desktop PySide6 ({platform.system()} {platform.release()} - {socket.gethostname()})"


def login(username: str, password: str, force: bool = False) -> dict[str, Any]:
    return api_client.post(
        "/api/auth/login",
        {
            "username": username,
            "password": password,
            "force": force,
            "client_info": _client_info(),
        },
        notify_401=False,
    )


def logout() -> dict[str, Any]:
    return api_client.post("/api/auth/logout", {}, notify_401=False)


def get_session() -> dict[str, Any]:
    return api_client.get("/api/auth/session")


def send_rest_heartbeat() -> dict[str, Any]:
    return api_client.post("/api/auth/heartbeat", {})


def get_profile() -> dict[str, Any]:
    return api_client.get("/api/profile")


def update_profile(full_name: str, email: str | None, phone: str | None) -> dict[str, Any]:
    return api_client.put(
        "/api/profile",
        {"full_name": full_name, "email": email or None, "phone": phone or None},
    )


def change_password(old_password: str, new_password: str, confirm_password: str) -> dict[str, Any]:
    return api_client.post(
        "/api/profile/change-password",
        {
            "old_password": old_password,
            "new_password": new_password,
            "confirm_password": confirm_password,
        },
    )

