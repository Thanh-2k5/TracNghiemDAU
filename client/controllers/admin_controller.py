"""Controller phía Client cho phân hệ Quản trị hệ thống (Admin: 1.3, 1.4, 1.5)."""
from pathlib import Path
from typing import Any, Optional

from client.api import admin_api
from client.models.user_model import UserProfile


class AdminController:
    # ======================== 1.3 Quản lý tài khoản ========================
    def get_roles(self) -> list[dict[str, Any]]:
        return admin_api.list_roles()

    def get_accounts(
        self,
        keyword: str = "",
        role_code: Optional[str] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[list[UserProfile], int]:
        resp = admin_api.list_accounts(
            keyword=keyword.strip() or None,
            role_code=role_code or None,
            is_active=is_active,
            page=page,
            page_size=page_size,
        )
        users = [UserProfile.from_dict(item) for item in resp.get("items", [])]
        return users, int(resp.get("total", len(users)))

    def create_account(
        self,
        username: str,
        password: str,
        full_name: str,
        email: str,
        phone: str,
        role_code: str,
        is_active: bool,
    ) -> UserProfile:
        payload = {
            "username": username.strip(),
            "password": password if password else None,
            "full_name": full_name.strip(),
            "email": email.strip() or None,
            "phone": phone.strip() or None,
            "role_code": role_code,
            "is_active": is_active,
        }
        return UserProfile.from_dict(admin_api.create_account(payload))

    def update_account(self, user_id: int, full_name: str, email: str, phone: str) -> UserProfile:
        payload = {
            "full_name": full_name.strip(),
            "email": email.strip() or None,
            "phone": phone.strip() or None,
        }
        return UserProfile.from_dict(admin_api.update_account(user_id, payload))

    def toggle_account_status(self, user_id: int, is_active: bool) -> UserProfile:
        return UserProfile.from_dict(admin_api.set_account_status(user_id, is_active))

    def reset_account_password(self, user_id: int) -> tuple[str, str]:
        resp = admin_api.reset_password(user_id)
        return str(resp.get("message", "")), str(resp.get("default_password", ""))

    def assign_account_role(self, user_id: int, role_code: str) -> UserProfile:
        return UserProfile.from_dict(admin_api.assign_role(user_id, role_code))

    # ======================== 1.4 Quản trị mạng ========================
    def get_network_config(self) -> dict[str, Any]:
        return admin_api.get_network_config()

    def save_network_config(
        self,
        api_host: str,
        api_port: int,
        socket_host: str,
        socket_port: int,
    ) -> dict[str, Any]:
        return admin_api.save_network_config(
            {
                "api_host": api_host.strip(),
                "api_port": int(api_port),
                "socket_host": socket_host.strip(),
                "socket_port": int(socket_port),
            }
        )

    def start_socket_server(self) -> dict[str, Any]:
        return admin_api.start_socket_server()

    def stop_socket_server(self) -> dict[str, Any]:
        return admin_api.stop_socket_server()

    def restart_socket_server(self) -> dict[str, Any]:
        return admin_api.restart_socket_server()

    def get_connections_overview(self) -> dict[str, Any]:
        return admin_api.get_connections()

    def kick_connection(self, connection_id: str) -> str:
        resp = admin_api.kick_connection(connection_id)
        return str(resp.get("message") or "Đã ngắt kết nối")

    # ======================== 1.5 Sao lưu & phục hồi ========================
    def list_backups(self) -> list[dict[str, Any]]:
        return admin_api.list_backups()

    def create_backup(self) -> dict[str, Any]:
        return admin_api.create_backup()

    def download_backup(self, filename: str, destination: Path) -> Path:
        return admin_api.download_backup(filename, destination)

    def restore_from_server(self, filename: str) -> dict[str, Any]:
        return admin_api.restore_server_backup(filename)

    def restore_from_local_file(self, file_path: Path) -> dict[str, Any]:
        return admin_api.restore_uploaded_backup(file_path)

    def delete_backup(self, filename: str) -> str:
        resp = admin_api.delete_backup(filename)
        return str(resp.get("message") or "Đã xóa bản sao lưu")


admin_controller = AdminController()

