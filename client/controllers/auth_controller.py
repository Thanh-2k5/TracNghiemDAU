"""Controller xác thực & thông tin cá nhân phía Client (1.1 & 1.2 - tái sử dụng cho 7 tác nhân)."""
from typing import Any

from client.api import auth_api
from client.api.http_client import APIError, api_client
from client.models.user_model import UserProfile, session_state
from client.socket_client.tcp_client import realtime_socket


class AuthController:
    """Điều phối Đăng nhập, Chặn trùng phiên, Kết nối Socket và Đăng xuất an toàn."""

    def __init__(self) -> None:
        realtime_socket.connection_changed.connect(self._on_socket_connection)
        realtime_socket.heartbeat_updated.connect(self._on_socket_heartbeat)

    def _on_socket_connection(self, online: bool) -> None:
        session_state.set_socket_state(online, session_state.latency_ms if online else None)

    def _on_socket_heartbeat(self, latency_ms: float) -> None:
        session_state.set_socket_state(True, latency_ms)

    def login(self, username: str, password: str, force: bool = False) -> UserProfile:
        resp = auth_api.login(username.strip(), password, force=force)
        token = resp["access_token"]
        session_id = resp["session_id"]
        user = UserProfile.from_dict(resp["user"])
        socket_info: dict[str, Any] = resp.get("socket") or {}

        api_client.set_token(token)
        session_state.set_login(token, session_id, user)

        sock_host = str(socket_info.get("host") or "")
        if sock_host in ("", "0.0.0.0"):
            sock_host = api_client.server_host
        sock_port = int(socket_info.get("port") or 9000)
        hb_interval = int(socket_info.get("heartbeat_interval") or 10)
        realtime_socket.start_session(sock_host, sock_port, token, hb_interval)
        return user

    def logout(self) -> None:
        """1.1.2 - Đóng Socket an toàn trước, sau đó hủy phiên trên REST Server và xóa token."""
        realtime_socket.stop_session(send_logout=True)
        if api_client.token:
            try:
                auth_api.logout()
            except APIError:
                pass
        api_client.set_token(None)
        session_state.clear()

    def clear_forced_session(self) -> None:
        """Dọn trạng thái cục bộ khi nhận sự kiện cưỡng chế đăng xuất từ Server."""
        realtime_socket.stop_session(send_logout=False)
        api_client.set_token(None)
        session_state.clear()


class ProfileController:
    """Điều phối module 1.2 - Xem/cập nhật thông tin cá nhân & Đổi mật khẩu."""

    def refresh_profile(self) -> UserProfile:
        data = auth_api.get_profile()
        user = UserProfile.from_dict(data)
        session_state.update_user(user)
        return user

    def update_profile(self, full_name: str, email: str, phone: str) -> UserProfile:
        data = auth_api.update_profile(
            full_name=full_name.strip(),
            email=email.strip() or None,
            phone=phone.strip() or None,
        )
        user = UserProfile.from_dict(data)
        session_state.update_user(user)
        return user

    def change_password(self, old_password: str, new_password: str, confirm_password: str) -> str:
        res = auth_api.change_password(old_password, new_password, confirm_password)
        if session_state.user and session_state.user.must_change_password:
            session_state.user.must_change_password = False
            session_state.update_user(session_state.user)
        return str(res.get("message") or "Đổi mật khẩu thành công")


auth_controller = AuthController()
profile_controller = ProfileController()

