from __future__ import annotations
import logging

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.core.logging import job_id_ctx
from app.documents.pipeline import process_document_version

log = logging.getLogger(__name__)


def enqueue_document_processing(version_id: str) -> None:
    settings = get_settings()
    if settings.queue_backend == "arq":
        import asyncio

        from arq import create_pool
        from arq.connections import RedisSettings

        async def _enqueue() -> None:
            pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
            await pool.enqueue_job("process_document_job", version_id)
            await pool.aclose()

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(_enqueue())
        else:
            process_inline(version_id)
            return
    else:
        process_inline(version_id)


def process_inline(version_id: str) -> None:
    job_id_ctx.set(version_id)
    db = SessionLocal()
    try:
        process_document_version(db, version_id)
    except Exception:
        log.exception("document processing failed")
        db.rollback()
        raise
    finally:
        db.close()


async def process_document_job(ctx, version_id: str) -> None:
    process_inline(version_id)


class WorkerSettings:
    functions = [process_document_job]
    redis_settings = None

    def __init__(self) -> None:
        from arq.connections import RedisSettings

        self.redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
