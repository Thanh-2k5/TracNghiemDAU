"""Lớp giao tiếp HTTP/JSON với FastAPI Server dùng chung cho toàn bộ Desktop Client."""
from pathlib import Path
from typing import Any, Callable, Optional
from urllib.parse import urlparse

import requests

from client.models.user_model import ClientEndpointConfig


class APIError(Exception):
    """Lỗi trả về từ tầng REST API hoặc lỗi kết nối mạng."""

    def __init__(
        self,
        message: str,
        status_code: int = 0,
        code: str = "NETWORK_ERROR",
        extra: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.extra = extra or {}


class APIClient:
    """HTTP Client quản lý Bearer Token, bắt lỗi thống nhất và truyền tải JSON / File."""

    def __init__(self, base_url: Optional[str] = None) -> None:
        if base_url:
            self.base_url = base_url.rstrip("/")
        else:
            host, port = ClientEndpointConfig.load()
            self.base_url = f"http://{host}:{port}"
        self.token: Optional[str] = None
        self.on_unauthorized: Optional[Callable[[str], None]] = None

    @property
    def server_host(self) -> str:
        parsed = urlparse(self.base_url)
        return parsed.hostname or "127.0.0.1"

    @property
    def server_port(self) -> int:
        parsed = urlparse(self.base_url)
        return parsed.port or 8000

    def set_endpoint(self, host: str, port: int, persist: bool = True) -> None:
        clean_host = host.strip()
        if clean_host == "0.0.0.0":
            clean_host = "127.0.0.1"
        self.base_url = f"http://{clean_host}:{int(port)}"
        if persist:
            ClientEndpointConfig.save(clean_host, int(port))

    def set_token(self, token: Optional[str]) -> None:
        self.token = token

    def _headers(self, json_body: bool = True) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if json_body:
            headers["Content-Type"] = "application/json"
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _url(self, endpoint: str) -> str:
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def _handle_response(self, resp: requests.Response, notify_401: bool = True) -> Any:
        if 200 <= resp.status_code < 300:
            if not resp.content:
                return {}
            return resp.json()

        detail = f"Lỗi máy chủ (HTTP {resp.status_code})"
        code = "HTTP_ERROR"
        extra: dict[str, Any] = {}
        try:
            payload = resp.json()
            if isinstance(payload, dict):
                detail = str(payload.get("detail") or detail)
                code = str(payload.get("code") or code)
                extra = {k: v for k, v in payload.items() if k not in ("detail", "code")}
        except ValueError:
            if resp.text:
                detail = resp.text[:200]

        if resp.status_code == 401 and notify_401 and self.token and self.on_unauthorized:
            self.on_unauthorized(detail)

        raise APIError(detail, status_code=resp.status_code, code=code, extra=extra)

    def request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Optional[dict[str, Any]] = None,
        json_data: Optional[dict[str, Any]] = None,
        timeout: int = 15,
        notify_401: bool = True,
    ) -> Any:
        try:
            resp = requests.request(
                method=method,
                url=self._url(endpoint),
                params=params,
                json=json_data,
                headers=self._headers(json_body=True),
                timeout=timeout,
            )
        except requests.ConnectionError as exc:
            raise APIError(
                f"Không thể kết nối tới Server ({self.base_url}). "
                "Vui lòng kiểm tra Server đã khởi chạy và đúng địa chỉ IP/Port.",
                code="CONNECTION_ERROR",
            ) from exc
        except requests.Timeout as exc:
            raise APIError("Hết thời gian chờ phản hồi từ Server.", code="TIMEOUT") from exc
        except requests.RequestException as exc:
            raise APIError(f"Lỗi giao tiếp mạng: {exc}", code="NETWORK_ERROR") from exc
        return self._handle_response(resp, notify_401=notify_401)

    def get(self, endpoint: str, params: Optional[dict[str, Any]] = None) -> Any:
        return self.request("GET", endpoint, params=params)

    def post(
        self,
        endpoint: str,
        data: Optional[dict[str, Any]] = None,
        *,
        notify_401: bool = True,
        timeout: int = 15,
    ) -> Any:
        return self.request("POST", endpoint, json_data=data, notify_401=notify_401, timeout=timeout)

    def put(self, endpoint: str, data: Optional[dict[str, Any]] = None) -> Any:
        return self.request("PUT", endpoint, json_data=data)

    def patch(self, endpoint: str, data: Optional[dict[str, Any]] = None) -> Any:
        return self.request("PATCH", endpoint, json_data=data)

    def delete(self, endpoint: str) -> Any:
        return self.request("DELETE", endpoint)

    def upload_file(self, endpoint: str, file_path: Path, field_name: str = "file") -> Any:
        try:
            with open(file_path, "rb") as fh:
                resp = requests.post(
                    self._url(endpoint),
                    files={field_name: (file_path.name, fh, "application/sql")},
                    headers=self._headers(json_body=False),
                    timeout=120,
                )
        except requests.RequestException as exc:
            raise APIError(f"Không thể tải tệp lên Server: {exc}", code="UPLOAD_ERROR") from exc
        return self._handle_response(resp)

    def download_file(self, endpoint: str, destination: Path) -> Path:
        try:
            with requests.get(
                self._url(endpoint),
                headers=self._headers(json_body=False),
                stream=True,
                timeout=120,
            ) as resp:
                if resp.status_code >= 400:
                    self._handle_response(resp)
                destination.parent.mkdir(parents=True, exist_ok=True)
                with open(destination, "wb") as out:
                    for chunk in resp.iter_content(chunk_size=65536):
                        if chunk:
                            out.write(chunk)
        except requests.RequestException as exc:
            raise APIError(f"Không thể tải tệp từ Server: {exc}", code="DOWNLOAD_ERROR") from exc
        return destination


api_client = APIClient()
