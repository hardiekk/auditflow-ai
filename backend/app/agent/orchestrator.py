from __future__ import annotations
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import write_audit
from app.models.entities import (
    AgentAction,
    AgentDecision,
    AgentRun,
    ComplianceIssue,
    IssueStatus,
    Notification,
    Severity,
    Shipment,
    Task,
    TaskPriority,
    TaskStatus,
    uid,
)
from app.notifications.service import notify


def run_agent(db: Session, shipment: Shipment, trigger: str) -> AgentRun:
    issues = db.scalars(
        select(ComplianceIssue).where(
            ComplianceIssue.shipment_id == shipment.id,
            ComplianceIssue.status == IssueStatus.OPEN.value,
        )
    ).all()
    critical = [i for i in issues if i.severity == Severity.CRITICAL.value]
    decision = AgentDecision.NO_ACTION.value
    summary_parts: list[str] = []
    actions: list[tuple[str, str, bool]] = []

    if trigger == "DOCUMENT_PROCESSED":
        summary_parts.append("Document processing completed. Configured checks re-evaluated.")
    if critical:
        decision = AgentDecision.REQUEST_CORRECTION.value
        for issue in critical:
            existing = db.scalars(
                select(Task).where(
                    Task.issue_id == issue.id,
                    Task.status != TaskStatus.COMPLETED.value,
                )
            ).first()
            if existing:
                continue
            task = Task(
                id=uid(),
                organization_id=shipment.organization_id,
                shipment_id=shipment.id,
                issue_id=issue.id,
                title=issue.recommended_action or issue.title,
                description=issue.description,
                priority=TaskPriority.CRITICAL.value,
                due_date=datetime.now(timezone.utc) + timedelta(days=2),
                status=TaskStatus.WAITING_FOR_SUPPLIER.value,
                created_by="agent",
                supplier_id=shipment.supplier_id,
            )
            db.add(task)
            actions.append((AgentDecision.REQUEST_CORRECTION.value, f"Created supplier task for {issue.title}", False))
            write_audit(
                db,
                organization_id=shipment.organization_id,
                event_type="task_created",
                description=task.title,
                shipment_id=shipment.id,
                actor_type="agent",
                entity_type="task",
                entity_id=task.id,
            )
        notify(
            db,
            organization_id=shipment.organization_id,
            title="Critical issue detected",
            body=f"{shipment.reference_number}: {critical[0].title}",
            kind="critical_issue",
            shipment_id=shipment.id,
        )
        summary_parts.append("Critical configured-rule failures require document correction.")
    elif issues:
        decision = AgentDecision.CREATE_REVIEW_TASK.value
        summary_parts.append("Non-critical configured issues remain; review task recommended.")
        actions.append((AgentDecision.CREATE_REVIEW_TASK.value, "Queue shipment for human review.", False))
        notify(
            db,
            organization_id=shipment.organization_id,
            title="Shipment ready for review",
            body=f"{shipment.reference_number} has open configured warnings.",
            kind="ready_for_review",
            shipment_id=shipment.id,
        )
    else:
        decision = AgentDecision.NOTIFY_USER.value
        summary_parts.append("Configured compliance checks passed. Human clearance is still required.")
        notify(
            db,
            organization_id=shipment.organization_id,
            title="Configured checks passed",
            body=f"{shipment.reference_number} is ready for human clearance review.",
            kind="ready_for_review",
            shipment_id=shipment.id,
        )

    run = AgentRun(
        id=uid(),
        organization_id=shipment.organization_id,
        shipment_id=shipment.id,
        trigger=trigger,
        decision=decision,
        summary=" ".join(summary_parts),
    )
    db.add(run)
    for action_type, detail, approval in actions:
        db.add(
            AgentAction(
                id=uid(),
                run_id=run.id,
                organization_id=shipment.organization_id,
                shipment_id=shipment.id,
                action_type=action_type,
                detail=detail,
                requires_approval=approval,
            )
        )
    write_audit(
        db,
        organization_id=shipment.organization_id,
        event_type="agent_executed",
        description=run.summary,
        shipment_id=shipment.id,
        actor_type="agent",
        entity_type="agent_run",
        entity_id=run.id,
        metadata={"decision": decision},
    )
    return run
