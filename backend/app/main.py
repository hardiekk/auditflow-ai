from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.auth import router as auth_router
from app.api.routes.ops import router as ops_router
from app.core.config import get_settings
from app.core.db import Base, engine, SessionLocal
from app.core.logging import configure_logging

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    configure_logging()
    log.info("Starting up AuditFlow AI backend...")
    
    # Ensure tables exist
    try:
        Base.metadata.create_all(bind=engine)
        log.info("Database schema initialized successfully.")
    except Exception as e:
        log.exception(f"Database initialization warning: {e}")

    # Auto-seed if database has no organizations
    try:
        from app.models.entities import Organization
        from sqlalchemy import select
        with SessionLocal() as db:
            org = db.scalars(select(Organization)).first()
            if not org:
                log.info("Empty database detected. Running initial seeder...")
                from app.seed import run_seed
                run_seed(db)
                log.info("Initial seeding completed.")
    except Exception as e:
        log.exception(f"Auto-seed warning: {e}")

    yield

    # Shutdown
    log.info("Shutting down AuditFlow AI backend...")


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Autonomous Trade Compliance & Cross-Border Audit Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
origins = list(set(settings.cors_list + [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "*"
]))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers (both with /api/v1 and root prefixes for maximum frontend compatibility)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(auth_router)

app.include_router(ops_router, prefix="/api/v1")
app.include_router(ops_router)


@app.get("/", tags=["system"])
def root():
    return {
        "status": "ok",
        "app": settings.app_name,
        "env": settings.app_env,
        "version": "1.0.0",
        "docs": "/docs",
        "api_prefix": "/api/v1",
        "demo_admin": settings.demo_admin_email,
    }


@app.get("/health", tags=["system"])
@app.get("/api/v1/health", tags=["system"])
def health_check():
    from sqlalchemy import text
    db_status = "healthy"
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"unhealthy: {exc}"

    return {
        "status": "healthy" if "unhealthy" not in db_status else "degraded",
        "database": db_status,
        "ai_provider": settings.ai_provider,
        "storage": settings.storage_backend,
    }


@app.get("/api/v1/meta", tags=["system"])
def system_meta():
    return {
        "app_name": settings.app_name,
        "env": settings.app_env,
        "demo_org": settings.demo_org_name,
        "demo_admin_email": settings.demo_admin_email,
        "demo_admin_password": settings.demo_admin_password,
        "ai_provider": settings.ai_provider,
        "openai_model": settings.openai_model,
        "low_confidence_threshold": settings.low_confidence_threshold,
    }
