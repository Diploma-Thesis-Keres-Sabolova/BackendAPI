import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Optional

from app.utils.logger_config import LoggerConfigurator

logger = logging.getLogger("BackendAPI.middleware")


class RequestIdMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, header_name: str = "X-Request-ID"):
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next):
        incoming_id: Optional[str] = request.headers.get(self.header_name)
        rid = LoggerConfigurator.set_request_id(incoming_id)
        start = time.time()
        try:
            logger.info(f"→ {request.method} {request.url.path} - start")
            response = await call_next(request)
            return response
        except Exception as exc:
            logger.exception(f"Unhandled exception for {request.method} {request.url.path}")
            raise
        finally:
            duration_ms = int((time.time() - start) * 1000)
            response_obj = locals().get("response")
            status = getattr(response_obj, "status_code", "-")

            logger.info(f"← {request.method} {request.url.path} - status={status} duration_ms={duration_ms} request_id={rid}")
            LoggerConfigurator.clear_request_id()
