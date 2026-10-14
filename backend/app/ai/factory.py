from __future__ import annotations
from app.ai.mock import MockAIProvider
from app.ai.provider import AIProvider
from app.core.config import get_settings


def get_ai_provider() -> AIProvider:
    settings = get_settings()
    mode = (settings.ai_provider or "auto").lower()
    if mode == "mock":
        return MockAIProvider()
    if mode == "openai" or (mode == "auto" and settings.openai_api_key):
        from app.ai.openai_provider import OpenAIProvider

        return OpenAIProvider()
    return MockAIProvider()
