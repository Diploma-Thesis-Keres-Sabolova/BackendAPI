# Auth.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class AuthBase(ABC):
    """
    Abstract class for all types of authentification.
    """

    @abstractmethod
    def apply(self, params: Dict[str, Any], headers: Dict[str, str]) -> None:
        """
        Create auth metod based on type of authentification.
        """
        pass


class QueryAuth(AuthBase):
    """
    Query Authentification.:
    ?access_key=APIKEY
    """

    def __init__(self, param_name: str, api_key: str):
        self.param_name = param_name
        self.api_key = api_key

    def apply(self, params: Dict[str, Any], headers: Dict[str, str]) -> None:
        params[self.param_name] = self.api_key


class HeaderAuth(AuthBase):
    """
    HTTP Header Authentification.:
    X-API-Key: APIKEY
    """

    def __init__(self, header_name: str, prefix: Optional[str], api_key: str):
        self.header_name = header_name
        self.prefix = prefix.strip() + " " if prefix else ""
        self.api_key = api_key

    def apply(self, params: Dict[str, Any], headers: Dict[str, str]) -> None:
        headers[self.header_name] = f"{self.prefix}{self.api_key}"


class AuthorizationAuth(AuthBase):
    """
    Auth with Authorization header.:
    Authorization: Token APIKEY
    or
    Authorization: Bearer APIKEY
    """

    def __init__(self, prefix: str, api_key: str):
        self.prefix = prefix.strip() + " " if prefix else ""
        self.api_key = api_key

    def apply(self, params: Dict[str, Any], headers: Dict[str, str]) -> None:
        headers["Authorization"] = f"{self.prefix}{self.api_key}"
