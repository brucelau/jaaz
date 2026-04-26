"""
Jaaz 日志服务 - 集中式结构化日志

特性：
- 标准 logging 模块 + JSON 输出
- Request ID 追踪（通过 contextvars）
- 自动注入 request_id / session_id / user_id
- 分级日志（debug/info/warning/error）
- emoji-free（方便日志聚合/过滤）
- 兼容现有 print() 语义的 wrapper

用法：
    from services.log_service import logger

    logger.info("user_login", user_id="u123", ip="1.2.3.4")
    logger.error("api_failed", code=500, path="/api/chat")
    logger.debug("selene_response", response_text="...")

对于现有 print() 替换：
    from services.log_service import print_log

    print_log("info", "chat_service", tool_list=[...])
    等价于 logger.info("chat_service", tool_list=[...])
"""

import sys
import os
import json
import logging
from contextvars import ContextVar
from typing import Any, Dict, Optional
from datetime import datetime, timezone

request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
session_id_var: ContextVar[Optional[str]] = ContextVar("session_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)

LOG_LEVEL = os.environ.get("JAAZ_LOG_LEVEL", "INFO").upper()
ENV = os.environ.get("JAAZ_ENV", "development")


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()
        extra = getattr(record, "extra_fields", {})
        log_entry = {
            "timestamp": ts,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            **extra,
        }
        if record.exc_info:
            log_entry["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False, default=str)


class ConsoleFormatter(logging.Formatter):
    RESET = "\033[0m"
    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        ts = datetime.fromtimestamp(record.created, tz=timezone.utc).strftime("%H:%M:%S")
        name = record.name.split(".")[-1][:20].ljust(20)
        extras = getattr(record, "extra_fields", {})
        extras_str = ""
        if extras:
            safe_extras = {
                k: (v[:200] + "..." if isinstance(v, str) and len(v) > 200 else v)
                for k, v in extras.items()
            }
            extras_str = "  " + json.dumps(safe_extras, ensure_ascii=False, default=str)
        return (
            f"{color}{record.levelname[0]}{self.RESET} "
            f"{ts} | {name} | {record.getMessage()}{extras_str}"
        )


def get_logger(name: str) -> logging.Logger:
    lg = logging.getLogger(name)
    if lg.handlers:
        return lg
    lg.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    lg.propagate = False
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    ch.setFormatter(ConsoleFormatter() if ENV != "production" else JSONFormatter())
    lg.addHandler(ch)
    return lg


class StructuredLogger:
    def __init__(self, name: str):
        self._logger = get_logger(name)

    def _build_extra(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        extra = {}
        req_id = request_id_var.get()
        if req_id:
            extra["request_id"] = req_id
        ses_id = session_id_var.get()
        if ses_id:
            extra["session_id"] = ses_id
        u_id = user_id_var.get()
        if u_id:
            extra["user_id"] = u_id
        extra.update(kwargs)
        return extra

    def _log(self, level: int, event: str, **kwargs: Any) -> None:
        extra = self._build_extra(kwargs)
        msg = f"[{event}]" if event else ""
        self._logger.log(level, msg, extra={"extra_fields": extra})

    def debug(self, event: str = "", **kwargs: Any) -> None:
        self._log(logging.DEBUG, event, **kwargs)

    def info(self, event: str = "", **kwargs: Any) -> None:
        self._log(logging.INFO, event, **kwargs)

    def warning(self, event: str = "", **kwargs: Any) -> None:
        self._log(logging.WARNING, event, **kwargs)

    def error(self, event: str = "", **kwargs: Any) -> None:
        self._log(logging.ERROR, event, **kwargs)

    def critical(self, event: str = "", **kwargs: Any) -> None:
        self._log(logging.CRITICAL, event, **kwargs)

    def exception(self, event: str = "", **kwargs: Any) -> None:
        self._log(logging.ERROR, event, **kwargs)

    def print(self, level: str, event: str, **kwargs: Any) -> None:
        level_map = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL,
        }
        self._log(level_map.get(level.lower(), logging.INFO), event, **kwargs)


logger = StructuredLogger("jaaz")
app_logger = StructuredLogger("jaaz.app")
chat_logger = StructuredLogger("jaaz.chat")
agent_logger = StructuredLogger("jaaz.agent")
tool_logger = StructuredLogger("jaaz.tool")
db_logger = StructuredLogger("jaaz.db")
ws_logger = StructuredLogger("jaaz.websocket")


def print_log(level: str, event: str, **kwargs: Any) -> None:
    logger.print(level, event, **kwargs)


def set_request_id(req_id: str) -> None:
    request_id_var.set(req_id)


def set_session_id(ses_id: str) -> None:
    session_id_var.set(ses_id)


def set_user_id(u_id: str) -> None:
    user_id_var.set(u_id)


def clear_context() -> None:
    request_id_var.set(None)
    session_id_var.set(None)
    user_id_var.set(None)
