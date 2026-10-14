from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.factory import get_ai_provider
from app.models.entities import RegulationChunk, RegulatoryDocument, RegulatorySource


def retrieve_regulation(db: Session, query: str, destination: str | None = None) -> dict:
    sources = db.scalars(select(RegulatorySource)).all()
    if not sources:
        return {
            "found": False,
            "message": "No configured regulatory source found.",
            "disclaimer": "Demo knowledge base only. Not complete global regulation.",
        }
    chunks = db.scalars(select(RegulationChunk)).all()
    if not chunks:
        return {
            "found": False,
            "message": "No configured regulatory source found.",
            "disclaimer": "Demo knowledge base only. Not complete global regulation.",
        }
    provider = get_ai_provider()
    q_vec = provider.embed([query])[0]
    scored = []
    for chunk in chunks:
        vec = chunk.embedding or provider.embed([chunk.text])[0]
        score = sum(a * b for a, b in zip(q_vec, vec))
        if destination and destination.lower() in chunk.text.lower():
            score += 0.2
        scored.append((score, chunk))
    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best = scored[0]
    if best_score < 0.1:
        return {
            "found": False,
            "message": "No configured regulatory source found.",
            "disclaimer": "Demo knowledge base only. Not complete global regulation.",
        }
    doc = db.get(RegulatoryDocument, best.document_id)
    source = db.get(RegulatorySource, doc.source_id) if doc else None
    return {
        "found": True,
        "source": source.title if source else "Demo Regulation Dataset",
        "section": best.section,
        "relevant_requirement": best.text,
        "retrieved_because": query,
        "confidence": round(min(best_score, 1.0), 2),
        "disclaimer": "Source: Demo Regulation Dataset. This is not a complete legal corpus.",
    }


class RegulationMonitor:
    """Future architecture: ingest new regulations, diff versions, find affected shipments."""

    def detect_and_notify(self, db: Session) -> None:
        raise NotImplementedError(
            "Regulatory version monitoring is documented for a later release and is not implemented in the MVP."
        )
