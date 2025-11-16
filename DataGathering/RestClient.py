# utils/rest_client.py
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional, Dict, Any, Union

class RestClient:
    """
    class that handles communicatoin with REST APIs...
    """

    DEFAULT_TIMEOUT = 10
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_BACKOFF_FACTOR = 0.2
    DEFAULT_USER_AGENT = "DataGatheringBot/1.0"

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url.rstrip("/") if base_url else None
        self.timeout = self.DEFAULT_TIMEOUT

        retry_strategy = Retry(
            total=self.DEFAULT_MAX_RETRIES,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
            backoff_factor=self.DEFAULT_BACKOFF_FACTOR,
            raise_on_status=False,
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session = requests.Session()
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        self.default_headers = {
            "User-Agent": self.DEFAULT_USER_AGENT,
            "Accept": "application/json",
        }

    def _make_url(self, path: str) -> str:
        if not self.base_url:
            return path
        return f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"

    def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Union[Dict, str]:
        """Makes GET request"""
        url = self._make_url(path)
        merged_headers = {**self.default_headers, **(headers or {})}

        try:
            response = self.session.get(url, params=params, headers=merged_headers, timeout=self.timeout)
            response.raise_for_status()
            try:
                return response.json()
            except ValueError:
                return response.text
        except requests.RequestException as e:
            print(f"[RestClient] GET {url} failed: {e}")
            raise

    def post(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Union[Dict, str]:
        """Makes POST request"""
        url = self._make_url(path)
        merged_headers = {**self.default_headers, **(headers or {})}

        try:
            response = self.session.post(url, data=data, json=json, headers=merged_headers, timeout=self.timeout)
            response.raise_for_status()
            try:
                return response.json()
            except ValueError:
                return response.text
        except requests.RequestException as e:
            print(f"[RestClient] POST {url} failed: {e}")
            raise

    def put(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Union[Dict, str]:
        """Makes PUT request"""
        url = self._make_url(path)
        merged_headers = {**self.default_headers, **(headers or {})}

        try:
            response = self.session.put(
                url,
                data=data,
                json=json,
                headers=merged_headers,
                timeout=self.timeout
            )
            response.raise_for_status()

            try:
                return response.json()
            except ValueError:
                return response.text

        except requests.RequestException as e:
            print(f"[RestClient] PUT {url} failed: {e}")
            raise

    def delete(
        self,
        path: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> Union[Dict, str]:
        """Makes DELETE request"""
        url = self._make_url(path)
        merged_headers = {**self.default_headers, **(headers or {})}

        try:
            response = self.session.delete(url, headers=merged_headers, timeout=self.timeout)
            response.raise_for_status()

            try:
                return response.json()
            except ValueError:
                return response.text

        except requests.RequestException as e:
            print(f"[RestClient] DELETE {url} failed: {e}")
            raise
