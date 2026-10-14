from __future__ import annotations
import json
import logging
import sys
import uuid
from contextvars import ContextVar

request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
shipment_id_ctx: ContextVar[str | None] = ContextVar("shipment_id", default=None)
job_id_ctx: ContextVar[str | None] = ContextVar("job_id", default=None)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_ctx.get(),
            "shipment_id": shipment_id_ctx.get(),
            "job_id": job_id_ctx.get(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)


def new_request_id() -> str:
    value = str(uuid.uuid4())
    request_id_ctx.set(value)
    return value
