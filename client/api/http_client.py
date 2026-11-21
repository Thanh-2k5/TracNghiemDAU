import os
from typing import Any, Dict, Optional
import requests
from dotenv import load_dotenv

load_dotenv()


class APIClient:
    """Lớp giao tiếp REST API (HTTP/JSON) với FastAPI Server."""

    def __init__(self, base_url: Optional[str] = None):
        host = os.getenv("API_HOST", "127.0.0.1")
        port = os.getenv("API_PORT", "8000")
        self.base_url = base_url or f"http://{host}:{port}"
        self.token: Optional[str] = None

    def set_token(self, token: str):
        self.token = token

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        response = requests.get(
            f"{self.base_url}/{endpoint.lstrip('/')}",
            params=params,
            headers=self._headers(),
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/{endpoint.lstrip('/')}",
            json=data,
            headers=self._headers(),
            timeout=10,
        )
        response.raise_for_status()
        return response.json()


api_client = APIClient()

