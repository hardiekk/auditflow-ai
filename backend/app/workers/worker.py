from __future__ import annotations
from arq.connections import RedisSettings

from app.core.config import get_settings
from app.workers.queue import process_document_job


class WorkerSettings:
    functions = [process_document_job]
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
