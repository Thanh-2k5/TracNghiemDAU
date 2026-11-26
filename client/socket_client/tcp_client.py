"""Lõi Socket Client (TCP/JSON + Heartbeat) tích hợp Qt Signal dùng chung cho 7 phân hệ.

Hỗ trợ:
- Bắt tay xác thực bằng JWT token (`auth` -> `auth_ok` / `auth_fail`)
- Tự động gửi gói tin `heartbeat` định kỳ và đo độ trễ RTT (`latency_ms`)
- Tự động kết nối lại khi mạng chập chờn hoặc khi Admin khởi động lại Socket Server
- Nhận sự kiện `force_logout` / `kicked` để cưỡng chế đăng xuất an toàn trên giao diện
- Cho phép các phân hệ khác (Coi thi 6.x, Sinh viên 7.x) gửi/nhận gói tin tùy biến
"""
import json
import socket
import threading
import time
from typing import Any, Optional

from PySide6.QtCore import QObject, Signal


class SocketClient(QObject):
    """Client kết nối Real-time TCP Socket không chặn luồng giao diện (non-blocking UI)."""

    connection_changed = Signal(bool)           # True = đã xác thực Socket, False = mất kết nối
    heartbeat_updated = Signal(float)           # latency_ms
    packet_received = Signal(str, dict)         # (ptype, data) cho các module 6.x, 7.x lắng nghe
    force_logged_out = Signal(str)              # reason
    server_notice = Signal(str)                 # thông báo từ Server

    def __init__(self) -> None:
        super().__init__()
        self._host: str = "127.0.0.1"
        self._port: int = 9000
        self._token: Optional[str] = None
        self._heartbeat_interval: float = 10.0

        self._sock: Optional[socket.socket] = None
        self._send_lock = threading.Lock()
        self._want_connected = False
        self._authenticated = False
        self._last_latency_ms: Optional[float] = None
        self._worker_id = 0

    @property
    def is_connected(self) -> bool:
        return self._authenticated and self._sock is not None

    def start_session(
        self,
        host: str,
        port: int,
        token: str,
        heartbeat_interval: int = 10,
    ) -> None:
        """Khởi chạy kết nối Socket cho phiên đăng nhập hiện tại."""
        self.stop_session(send_logout=False)
        clean_host = host.strip() if host else "127.0.0.1"
        if clean_host in ("0.0.0.0", ""):
            clean_host = "127.0.0.1"
        self._host = clean_host
        self._port = int(port)
        self._token = token
        self._heartbeat_interval = max(float(heartbeat_interval), 2.0)
        self._want_connected = True
        self._worker_id += 1
        current_worker = self._worker_id
        threading.Thread(
            target=self._connection_supervisor,
            args=(current_worker,),
            daemon=True,
        ).start()

    def stop_session(self, send_logout: bool = True) -> None:
        """1.1.2 - Đóng kết nối Socket an toàn khi đăng xuất."""
        self._want_connected = False
        self._worker_id += 1
        if send_logout and self._authenticated:
            self.send_packet("logout", {})
        self._close_raw_socket()
        if self._authenticated:
            self._authenticated = False
            self.connection_changed.emit(False)

    def send_packet(self, ptype: str, data: Optional[dict[str, Any]] = None, req_id: Optional[str] = None) -> bool:
        """Gửi gói tin JSON kết thúc bằng '\\n' lên Socket Server."""
        sock = self._sock
        if sock is None:
            return False
        packet: dict[str, Any] = {"type": ptype, "data": data or {}, "ts": time.time()}
        if req_id:
            packet["id"] = req_id
        raw = (json.dumps(packet, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
        try:
            with self._send_lock:
                sock.sendall(raw)
            return True
        except OSError:
            return False

    # ======================= Luồng nền =======================
    def _close_raw_socket(self) -> None:
        sock, self._sock = self._sock, None
        if sock is not None:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                sock.close()
            except OSError:
                pass

    def _connection_supervisor(self, worker_id: int) -> None:
        while self._want_connected and worker_id == self._worker_id and self._token:
            connected_ok = self._run_single_connection(worker_id)
            if self._authenticated:
                self._authenticated = False
                self.connection_changed.emit(False)
            if not self._want_connected or worker_id != self._worker_id:
                break
            time.sleep(2.0 if connected_ok else 3.0)

    def _run_single_connection(self, worker_id: int) -> bool:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(6.0)
        try:
            sock.connect((self._host, self._port))
            sock.settimeout(1.0)
        except OSError:
            try:
                sock.close()
            except OSError:
                pass
            return False

        self._sock = sock
        self._last_latency_ms = None
        if not self.send_packet("auth", {"token": self._token}):
            self._close_raw_socket()
            return False

        buffer = ""
        next_hb = time.monotonic() + self._heartbeat_interval
        try:
            while self._want_connected and worker_id == self._worker_id:
                now = time.monotonic()
                if self._authenticated and now >= next_hb:
                    self.send_packet(
                        "heartbeat",
                        {"client_ts": time.time(), "latency_ms": self._last_latency_ms},
                    )
                    next_hb = now + self._heartbeat_interval

                try:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    buffer += chunk.decode("utf-8", errors="replace")
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        if line.strip():
                            self._handle_line(line.strip())
                except socket.timeout:
                    continue
                except OSError:
                    break
        finally:
            self._close_raw_socket()
        return True

    def _handle_line(self, line: str) -> None:
        try:
            packet = json.loads(line)
        except json.JSONDecodeError:
            return
        if not isinstance(packet, dict):
            return
        ptype = str(packet.get("type") or "")
        data = packet.get("data") if isinstance(packet.get("data"), dict) else {}

        if ptype == "auth_ok":
            hb = data.get("heartbeat_interval")
            if isinstance(hb, (int, float)) and hb >= 2:
                self._heartbeat_interval = float(hb)
            self._authenticated = True
            self.connection_changed.emit(True)
            # Gửi heartbeat đầu tiên ngay để đo latency tức thì
            self.send_packet("heartbeat", {"client_ts": time.time()})
            return

        if ptype == "auth_fail":
            code = str(data.get("code") or "")
            msg = str(data.get("message") or "Xác thực Socket thất bại")
            self._want_connected = False
            self._close_raw_socket()
            if code in ("SESSION_REVOKED", "TOKEN_EXPIRED", "ACCOUNT_LOCKED", "INVALID_TOKEN"):
                self.force_logged_out.emit(msg)
            return

        if ptype == "heartbeat_ack":
            client_ts = data.get("client_ts")
            if isinstance(client_ts, (int, float)):
                rtt = max(0.1, round((time.time() - float(client_ts)) * 1000.0, 1))
                self._last_latency_ms = rtt
                self.heartbeat_updated.emit(rtt)
            return

        if ptype in ("force_logout", "kicked"):
            reason = str(data.get("reason") or data.get("message") or "Phiên đăng nhập đã bị đóng từ xa")
            self._want_connected = False
            self._authenticated = False
            self._close_raw_socket()
            self.connection_changed.emit(False)
            self.force_logged_out.emit(reason)
            return

        if ptype == "server_shutdown":
            msg = str(data.get("message") or "Socket Server tạm dừng")
            self.server_notice.emit(msg)
            return

        if ptype == "notify":
            msg = str(data.get("message") or "")
            if msg:
                self.server_notice.emit(msg)

        self.packet_received.emit(ptype, data)


realtime_socket = SocketClient()
