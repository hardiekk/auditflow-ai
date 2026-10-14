from __future__ import annotations
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.audit.service import write_audit
from app.core.config import get_settings
from app.models.entities import (
    ComplianceIssue,
    ComplianceState,
    Evidence,
    IssueStatus,
    RiskAssessment,
    RiskFactor,
    RiskLevel,
    Severity,
    Shipment,
    Task,
    TaskStatus,
    uid,
)

POINTS = {
    Severity.CRITICAL.value: 30,
    Severity.HIGH.value: 20,
    Severity.MEDIUM.value: 10,
    Severity.LOW.value: 5,
}


def risk_level(score: int) -> str:
    if score >= 75:
        return RiskLevel.CRITICAL.value
    if score >= 50:
        return RiskLevel.HIGH.value
    if score >= 25:
        return RiskLevel.MEDIUM.value
    return RiskLevel.LOW.value


def derive_state(shipment: Shipment, open_issues: list[ComplianceIssue], processing: bool) -> str:
    if processing:
        return ComplianceState.PROCESSING.value
    if shipment.under_review:
        return ComplianceState.UNDER_REVIEW.value
    critical = [i for i in open_issues if i.severity == Severity.CRITICAL.value]
    warnings = [i for i in open_issues if i.severity != Severity.CRITICAL.value]
    if critical:
        return ComplianceState.BLOCKED.value
    if warnings:
        return ComplianceState.WARNING.value
    if shipment.document_completeness <= 0:
        return ComplianceState.DRAFT.value
    if not open_issues:
        return ComplianceState.READY_FOR_REVIEW.value
    return ComplianceState.WARNING.value


def recalculate_risk(db: Session, shipment: Shipment, processing: bool = False) -> RiskAssessment:
    settings = get_settings()
    issues = db.scalars(
        select(ComplianceIssue).where(
            ComplianceIssue.shipment_id == shipment.id,
            ComplianceIssue.status == IssueStatus.OPEN.value,
        )
    ).all()
    factors: list[tuple[str, int, str]] = []
    for issue in issues:
        factors.append((issue.title, POINTS.get(issue.severity, 10), "compliance"))
    low_conf = db.scalars(
        select(Evidence).where(
            Evidence.shipment_id == shipment.id,
            Evidence.confidence.is_not(None),
            Evidence.confidence < settings.low_confidence_threshold,
        )
    ).all()
    if low_conf:
        factors.append((f"OCR/extraction uncertainty ({len(low_conf)} fields)", min(3 * len(low_conf), 9), "uncertainty"))
    open_tasks = db.scalar(
        select(func.count(Task.id)).where(Task.shipment_id == shipment.id, Task.status != TaskStatus.COMPLETED.value)
    ) or 0
    if open_tasks:
        factors.append((f"Unresolved tasks ({open_tasks})", min(2 * int(open_tasks), 10), "workflow"))

    score = min(100, sum(p for _, p, _ in factors))
    previous = shipment.risk_score
    assessment = RiskAssessment(
        id=uid(),
        organization_id=shipment.organization_id,
        shipment_id=shipment.id,
        score=score,
        previous_score=previous,
        level=risk_level(score),
        reason=f"{len(factors)} contributing factors" if factors else "No open risk factors",
    )
    db.add(assessment)
    for label, points, category in factors:
        db.add(RiskFactor(id=uid(), assessment_id=assessment.id, label=label, points=points, category=category))

    new_state = derive_state(shipment, list(issues), processing)
    old_state = shipment.compliance_status
    shipment.risk_score = score
    shipment.risk_level = assessment.level
    shipment.compliance_status = new_state
    write_audit(
        db,
        organization_id=shipment.organization_id,
        event_type="risk_changed",
        description=f"Risk {previous} → {score}",
        shipment_id=shipment.id,
        previous_state=str(previous),
        new_state=str(score),
        metadata={"level": assessment.level, "factors": [f[0] for f in factors]},
    )
    if old_state != new_state:
        write_audit(
            db,
            organization_id=shipment.organization_id,
            event_type="shipment_state_changed",
            description=f"Compliance state {old_state} → {new_state}",
            shipment_id=shipment.id,
            previous_state=old_state,
            new_state=new_state,
        )
    return assessment
