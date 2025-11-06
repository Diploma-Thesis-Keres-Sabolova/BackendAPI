import logging
import logging.handlers
import sys
import uuid
import os

from contextvars import ContextVar
from datetime import datetime
from typing import Optional

request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

from pythonjsonlogger import json


class RequestIdFilter(logging.Filter):
    """Add request_id from contextvar into LogRecord"""
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get() or "-"
        return True


class ContextFormatter(logging.Formatter):
    """Formatter that uses request_id if present"""
    default_msec_format = "%s.%03d"

    def format(self, record: logging.LogRecord) -> str:
        if not hasattr(record, "request_id"):
            record.request_id = request_id_var.get() or "-"
        if not hasattr(record, "isoTime"):
            record.isoTime = datetime.utcfromtimestamp(record.created).isoformat() + "Z"
        return super().format(record)


class LoggerConfigurator:
    def __init__(
        self,
        name: str = "app",
        level: int = logging.INFO,
        logfile: Optional[str] = "logs/app.log",
        when: str = "midnight",
        backup_count: int = 14,
        use_json: bool = False,
    ):
        self.name = name
        self.level = level
        self.logfile = logfile
        self.when = when
        self.backup_count = backup_count
        self.use_json = use_json

    def _create_console_handler(self) -> logging.Handler:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(self.level)

        if self.use_json:
            fmt = json.JsonFormatter('%(isoTime)s %(levelname)s %(name)s %(message)s %(request_id)s')
            ch.setFormatter(fmt)
        return ch

    def _create_file_handler(self) -> Optional[logging.Handler]:
        os.makedirs(os.path.dirname(self.logfile), exist_ok=True)
        if not self.logfile:
            return None
        handler = logging.handlers.TimedRotatingFileHandler(
            filename=self.logfile,
            when=self.when,
            backupCount=self.backup_count,
            encoding="utf-8",
        )
        handler.setLevel(self.level)
        if self.use_json:
            fmt = json.JsonFormatter('%(isoTime)s %(levelname)s %(name)s %(message)s %(request_id)s')
            handler.setFormatter(fmt)
        else:
            fmt_str = "%(isoTime)s [%(levelname)s] %(name)s %(request_id)s - %(message)s"
            handler.setFormatter(ContextFormatter(fmt_str))
        return handler

    def configure_root_logger(self):
        root = logging.getLogger()
        for h in list(root.handlers):
            root.removeHandler(h)

        root.setLevel(self.level)
        request_filter = RequestIdFilter()
        root.addFilter(request_filter)

        ch = self._create_console_handler()
        root.addHandler(ch)

        fh = self._create_file_handler()
        if fh:
            root.addHandler(fh)

        logging.getLogger("uvicorn.access").setLevel(logging.INFO)
        logging.getLogger("uvicorn.error").setLevel(logging.INFO)
        logging.getLogger("asyncio").setLevel(logging.WARNING)

    @staticmethod
    def set_request_id(rid: Optional[str] = None):
        """
        Helper to set request id in contextvar.
        If rid is None, new uuid4 is generated.
        """
        if rid is None:
            rid = str(uuid.uuid4())
        request_id_var.set(rid)
        return rid

    @staticmethod
    def clear_request_id():
        request_id_var.set(None)
