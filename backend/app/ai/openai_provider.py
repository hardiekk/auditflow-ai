from __future__ import annotations

import json
import time

from openai import OpenAI

from app.ai.provider import AIProvider, ClassificationResult, ExtractedField, ExtractionResult, ExplanationResult
from app.core.config import get_settings
from app.models.entities import DocumentType

DOC_TYPES = [t.value for t in DocumentType]


class OpenAIProvider(AIProvider):
    name = "openai"

    def __init__(self) -> None:
        settings = get_settings()
        self.client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
        self.model = settings.openai_model
        self.embed_model = settings.openai_embedding_model

    def classify(self, filename: str, text: str) -> ClassificationResult:
        prompt = {
            "filename": filename,
            "text_excerpt": text[:4000],
            "allowed_types": DOC_TYPES,
        }
        content = self._complete(
            "Classify this trade document. Return JSON {document_type, confidence, reason}. "
            "document_type must be one of the allowed types.",
            json.dumps(prompt),
        )
        data = json.loads(content)
        dtype = data.get("document_type") if data.get("document_type") in DOC_TYPES else DocumentType.OTHER.value
        return ClassificationResult(
            document_type=dtype,
            confidence=float(data.get("confidence", 0.7)),
            reason=str(data.get("reason", "")),
        )

    def extract(
        self,
        document_type: str,
        filename: str,
        text: str,
        pages: list[tuple[int, str]] | None = None,
    ) -> ExtractionResult:
        prompt = {
            "document_type": document_type,
            "filename": filename,
            "text": text[:8000],
        }
        content = self._complete(
            "Extract structured fields as JSON {fields:[{field, raw_value, page, confidence}], overall_confidence}. "
            "Never invent values that are not in the text. If unknown, omit the field.",
            json.dumps(prompt),
        )
        data = json.loads(content)
        fields = [ExtractedField(**item) for item in data.get("fields", [])]
        return ExtractionResult(
            fields=fields,
            raw_text=text,
            overall_confidence=float(data.get("overall_confidence", 0.7)),
        )

    def explain(self, prompt: str) -> ExplanationResult:
        content = self._complete(
            "Explain a configured compliance result. Do not claim legal compliance or violation. JSON {text}.",
            prompt,
        )
        data = json.loads(content)
        return ExplanationResult(text=str(data.get("text", content)))

    def embed(self, texts: list[str]) -> list[list[float]]:
        resp = self.client.embeddings.create(model=self.embed_model, input=texts)
        return [item.embedding for item in resp.data]

    def _complete(self, system: str, user: str) -> str:
        started = time.time()
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            response_format={"type": "json_object"},
            temperature=0,
        )
        _ = started
        return resp.choices[0].message.content or "{}"
