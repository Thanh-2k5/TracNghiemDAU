"""Các hàm gọi REST API cho phân hệ Admin: 1.3 Tài khoản, 1.4 Mạng, 1.5 Sao lưu & Phục hồi."""
from pathlib import Path
from typing import Any, Optional

from client.api.http_client import api_client


# ======================== 1.3 Quản lý tài khoản ========================
def list_roles() -> list[dict[str, Any]]:
    return api_client.get("/api/admin/roles")


def list_accounts(
    keyword: Optional[str] = None,
    role_code: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = 1,
    page_size: int = 25,
) -> dict[str, Any]:
    params: dict[str, Any] = {"page": page, "page_size": page_size}
    if keyword:
        params["keyword"] = keyword
    if role_code:
        params["role_code"] = role_code
    if is_active is not None:
        params["is_active"] = is_active
    return api_client.get("/api/admin/accounts", params=params)


def create_account(payload: dict[str, Any]) -> dict[str, Any]:
    return api_client.post("/api/admin/accounts", payload)


def update_account(user_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    return api_client.put(f"/api/admin/accounts/{user_id}", payload)


def set_account_status(user_id: int, is_active: bool) -> dict[str, Any]:
    return api_client.patch(f"/api/admin/accounts/{user_id}/status", {"is_active": is_active})


def reset_password(user_id: int) -> dict[str, Any]:
    return api_client.post(f"/api/admin/accounts/{user_id}/reset-password", {})


def assign_role(user_id: int, role_code: str) -> dict[str, Any]:
    return api_client.put(f"/api/admin/accounts/{user_id}/role", {"role_code": role_code})


# ======================== 1.4 Quản trị mạng ========================
def get_network_config() -> dict[str, Any]:
    return api_client.get("/api/admin/network/config")


def save_network_config(payload: dict[str, Any]) -> dict[str, Any]:
    return api_client.put("/api/admin/network/config", payload)


def get_server_status() -> dict[str, Any]:
    return api_client.get("/api/admin/network/status")


def start_socket_server() -> dict[str, Any]:
    return api_client.post("/api/admin/network/start", {})


def stop_socket_server() -> dict[str, Any]:
    return api_client.post("/api/admin/network/stop", {})


def restart_socket_server() -> dict[str, Any]:
    return api_client.post("/api/admin/network/restart", {})


def get_connections() -> dict[str, Any]:
    return api_client.get("/api/admin/network/connections")


def kick_connection(connection_id: str) -> dict[str, Any]:
    return api_client.delete(f"/api/admin/network/connections/{connection_id}")


# ======================== 1.5 Sao lưu & phục hồi ========================
def list_backups() -> list[dict[str, Any]]:
    return api_client.get("/api/admin/backups")


def create_backup() -> dict[str, Any]:
    return api_client.post("/api/admin/backups", {}, timeout=120)


def download_backup(filename: str, destination: Path) -> Path:
    return api_client.download_file(f"/api/admin/backups/{filename}/download", destination)


def restore_server_backup(filename: str) -> dict[str, Any]:
    return api_client.post(f"/api/admin/backups/{filename}/restore", {}, timeout=120)


def restore_uploaded_backup(file_path: Path) -> dict[str, Any]:
    return api_client.upload_file("/api/admin/backups/restore", file_path)


def delete_backup(filename: str) -> dict[str, Any]:
    return api_client.delete(f"/api/admin/backups/{filename}")

