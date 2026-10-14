from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class ExtractedField(BaseModel):
    field: str
    raw_value: Any = None
    page: int | None = 1
    confidence: float = 0.9


class ClassificationResult(BaseModel):
    document_type: str
    confidence: float
    reason: str = ""


class ExtractionResult(BaseModel):
    fields: list[ExtractedField] = Field(default_factory=list)
    raw_text: str = ""
    overall_confidence: float = 0.9


class ExplanationResult(BaseModel):
    text: str
    citations: list[dict] = Field(default_factory=list)


class AIProvider(ABC):
    name: str = "base"

    @abstractmethod
    def classify(self, filename: str, text: str) -> ClassificationResult: ...

    @abstractmethod
    def extract(
        self,
        document_type: str,
        filename: str,
        text: str,
        pages: list[tuple[int, str]] | None = None,
    ) -> ExtractionResult: ...

    @abstractmethod
    def explain(self, prompt: str) -> ExplanationResult: ...

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]: ...
