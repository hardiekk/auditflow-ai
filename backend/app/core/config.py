from __future__ import annotations
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    app_name: str = "AuditFlow AI"
    app_env: str = "development"
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 480
    api_cors_origins: str = "http://localhost:3000"

    database_url: str = "sqlite:///./auditflow.db"
    redis_url: str = "redis://localhost:6379/0"
    queue_backend: str = "inline"

    storage_backend: str = "local"
    storage_local_path: str = "./data/storage"
    s3_endpoint: str = ""
    s3_bucket: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_region: str = "us-east-1"

    ai_provider: str = "auto"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    low_confidence_threshold: float = 0.8

    demo_org_name: str = "Northwind Logistics"
    demo_admin_email: str = "admin@auditflow.demo"
    demo_admin_password: str = "AuditFlow!demo"

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.api_cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
