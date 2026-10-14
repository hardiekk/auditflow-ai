from __future__ import annotations
from sqlalchemy.orm import Session

from app.models.entities import ActorType, AuditEvent, WorkflowEvent, uid


def write_audit(
    db: Session,
    *,
    organization_id: str,
    event_type: str,
    description: str,
    shipment_id: str | None = None,
    actor_id: str | None = None,
    actor_type: str = ActorType.SYSTEM.value,
    entity_type: str | None = None,
    entity_id: str | None = None,
    metadata: dict | None = None,
    previous_state: str | None = None,
    new_state: str | None = None,
) -> AuditEvent:
    event = AuditEvent(
        organization_id=organization_id,
        event_type=event_type,
        description=description,
        shipment_id=shipment_id,
        actor_id=actor_id,
        actor_type=actor_type,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata_json=metadata or {},
        previous_state=previous_state,
        new_state=new_state,
    )
    db.add(event)
    return event


def emit_workflow(
    db: Session,
    *,
    organization_id: str,
    event_type: str,
    shipment_id: str | None = None,
    payload: dict | None = None,
) -> WorkflowEvent:
    event = WorkflowEvent(
        id=uid(),
        organization_id=organization_id,
        shipment_id=shipment_id,
        event_type=event_type,
        payload=payload or {},
    )
    db.add(event)
    return event
