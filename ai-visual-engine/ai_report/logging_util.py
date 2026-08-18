"""Structured logging (requirement #18).

Emits one JSON line per event. Never logs API keys, tokens, or raw secrets —
callers pass only the fields defined here.
"""
import json
import logging
import sys
import time
import uuid

_SENSITIVE = {"api_key", "token", "password", "secret", "authorization"}


def get_logger(name: str = "ai_report") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def new_request_id() -> str:
    return uuid.uuid4().hex[:12]


def _redact(payload: dict) -> dict:
    clean = {}
    for k, v in payload.items():
        if k.lower() in _SENSITIVE:
            clean[k] = "***redacted***"
        else:
            clean[k] = v
    return clean


def log_event(event: str, **fields) -> None:
    """Emit a structured JSON log line."""
    record = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "event": event}
    record.update(_redact(fields))
    get_logger().info(json.dumps(record, default=str))
