from __future__ import annotations
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_current, org_owned, require_roles
from app.audit.service import write_audit
from app.compliance.engine import run_compliance
from app.core.db import get_db
from app.documents.pipeline import file_hash
from app.documents.storage import get_storage
from app.models.entities import (
    AgentAction,
    AgentRun,
    AuditEvent,
    ComplianceEvaluation,
    ComplianceIssue,
    ComplianceRule,
    DocumentVersion,
    Evidence,
    IssueStatus,
    Notification,
    ProcessingStatus,
    Review,
    RiskAssessment,
    RiskFactor,
    Shipment,
    ShipmentDocument,
    Task,
    TraceabilityEdge,
    TraceabilityNode,
    uid,
)
from app.risk.engine import recalculate_risk
from app.schemas.common import (
    IssueOut,
    ReviewRequest,
    ShipmentCreate,
    ShipmentOut,
    ShipmentUpdate,
    TaskCreate,
    TaskUpdate,
)
from app.workers.queue import enqueue_document_processing

router = APIRouter(tags=["operations"])
WRITE_ROLES = ("Admin", "Compliance Manager", "Operations Manager", "Reviewer")


def _shipment_out(s: Shipment) -> ShipmentOut:
    return ShipmentOut(
        id=s.id,
        reference_number=s.reference_number,
        origin_country=s.origin_country,
        destination_country=s.destination_country,
        origin_port=s.origin_port,
        destination_port=s.destination_port,
        shipment_date=s.shipment_date,
        estimated_arrival=s.estimated_arrival,
        carrier=s.carrier,
        status=s.status,
        compliance_status=s.compliance_status,
        risk_score=s.risk_score,
        risk_level=s.risk_level,
        document_completeness=s.document_completeness,
        supplier_name=s.supplier.name if s.supplier else None,
        customer_name=s.customer.name if s.customer else None,
        created_at=s.created_at,
    )


@router.get("/shipments", response_model=list[ShipmentOut])
def list_shipments(
    q: str | None = None,
    auth: AuthContext = Depends(get_current),
    db: Session = Depends(get_db),
):
    query = select(Shipment).where(Shipment.organization_id == auth.organization_id).order_by(Shipment.created_at.desc())
    if q:
        query = query.where(Shipment.reference_number.ilike(f"%{q}%"))
    return [_shipment_out(s) for s in db.scalars(query).all()]


@router.post("/shipments", response_model=ShipmentOut)
def create_shipment(
    payload: ShipmentCreate,
    auth: AuthContext = Depends(require_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
):
    s = Shipment(id=uid(), organization_id=auth.organization_id, **payload.model_dump())
    db.add(s)
    write_audit(
        db,
        organization_id=auth.organization_id,
        event_type="shipment_created",
        description=f"Created shipment {s.reference_number}",
        shipment_id=s.id,
        actor_id=auth.user.id,
        actor_type="user",
    )
    db.commit()
    db.refresh(s)
    return _shipment_out(s)


@router.get("/shipments/{shipment_id}", response_model=ShipmentOut)
def get_shipment(shipment_id: str, auth: AuthContext = Depends(get_current), db: Session = Depends(get_db)):
    s = db.get(Shipment, shipment_id)
    if not s:
        raise HTTPException(404, "Not found")
    org_owned(s, auth)
    return _shipment_out(s)


@router.put("/shipments/{shipment_id}", response_model=ShipmentOut)
def update_shipment(
    shipment_id: str,
    payload: ShipmentUpdate,
    auth: AuthContext = Depends(require_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
):
    s = db.get(Shipment, shipment_id)
    if not s:
        raise HTTPException(404, "Not found")
    org_owned(s, auth)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(s, key, value)
    db.commit()
    db.refresh(s)
    return _shipment_out(s)


@router.post("/shipments/{shipment_id}/documents")
def upload_document(
    shipment_id: str,
    file: UploadFile = File(...),
    replace_document_id: str | None = Form(None),
    reason: str | None = Form(None),
    auth: AuthContext = Depends(require_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
):
    s = db.get(Shipment, shipment_id)
    if not s:
        raise HTTPException(404, "Not found")
    org_owned(s, auth)
    data = file.file.read()
    if not data:
        raise HTTPException(400, "Empty file")
    if len(data) > 15 * 1024 * 1024:
        raise HTTPException(400, "File exceeds 15MB limit")
    name = file.filename or "document.pdf"
    if not name.lower().endswith((".pdf", ".txt", ".png", ".jpg", ".jpeg")):
        raise HTTPException(400, "Unsupported file type")
    digest = file_hash(data)
    existing = db.scalars(
        select(ShipmentDocument).where(
            ShipmentDocument.organization_id == auth.organization_id,
            ShipmentDocument.shipment_id == shipment_id,
            ShipmentDocument.file_hash == digest,
        )
    ).first()
    if existing and not replace_document_id:
        return {"id": existing.id, "status": "duplicate", "detail": "Identical file already stored for this shipment."}

    storage = get_storage()
    if replace_document_id:
        document = db.get(ShipmentDocument, replace_document_id)
        if not document:
            raise HTTPException(404, "Document not found")
        org_owned(document, auth)
        version_no = document.current_version + 1
        prev = db.scalars(
            select(DocumentVersion)
            .where(DocumentVersion.document_id == document.id)
            .order_by(DocumentVersion.version.desc())
        ).first()
        key = f"{auth.organization_id}/{shipment_id}/{document.id}/v{version_no}-{digest[:10]}"
        storage.put(key, data, file.content_type or "application/pdf")
        version = DocumentVersion(
            id=uid(),
            organization_id=auth.organization_id,
            document_id=document.id,
            version=version_no,
            storage_key=key,
            file_hash=digest,
            mime_type=file.content_type or "application/pdf",
            uploaded_by=auth.user.id,
            replace_reason=reason or "Replacement upload",
            previous_version_id=prev.id if prev else None,
        )
        document.current_version = version_no
        document.file_hash = digest
        document.name = name
        document.processing_status = ProcessingStatus.PENDING.value
        db.add(version)
        write_audit(
            db,
            organization_id=auth.organization_id,
            event_type="document_version_replaced",
            description=f"{document.name} replaced with version {version_no}",
            shipment_id=s.id,
            actor_id=auth.user.id,
            actor_type="user",
            entity_id=document.id,
            entity_type="document",
        )
    else:
        document = ShipmentDocument(
            id=uid(),
            organization_id=auth.organization_id,
            shipment_id=s.id,
            name=name,
            file_hash=digest,
            uploaded_by=auth.user.id,
        )
        db.add(document)
        db.flush()
        key = f"{auth.organization_id}/{shipment_id}/{document.id}/v1-{digest[:10]}"
        storage.put(key, data, file.content_type or "application/pdf")
        version = DocumentVersion(
            id=uid(),
            organization_id=auth.organization_id,
            document_id=document.id,
            version=1,
            storage_key=key,
            file_hash=digest,
            mime_type=file.content_type or "application/pdf",
            uploaded_by=auth.user.id,
        )
        db.add(version)
        write_audit(
            db,
            organization_id=auth.organization_id,
            event_type="document_uploaded",
            description=f"Uploaded {name}",
            shipment_id=s.id,
            actor_id=auth.user.id,
            actor_type="user",
            entity_id=document.id,
            entity_type="document",
        )
    db.commit()
    enqueue_document_processing(version.id)
    return {"id": document.id, "version_id": version.id, "status": "queued"}


@router.get("/shipments/{shipment_id}/documents")
def list_documents(shipment_id: str, auth: AuthContext = Depends(get_current), db: Session = Depends(get_db)):
    s = db.get(Shipment, shipment_id)
    if not s:
        raise HTTPException(404, "Not found")
    org_owned(s, auth)
    docs = db.scalars(select(ShipmentDocument).where(ShipmentDocument.shipment_id == shipment_id)).all()
    result = []
    for doc in docs:
        versions = db.scalars(
            select(DocumentVersion).where(DocumentVersion.document_id == doc.id).order_by(DocumentVersion.version)
        ).all()
        result.append(
            {
                "id": doc.id,
                "name": doc.name,
                "type": doc.document_type,
                "version": doc.current_version,
                "processing_status": doc.processing_status,
                "file_hash": doc.file_hash,
                "confidence": versions[-1].confidence if versions else None,
                "uploaded_by": doc.uploaded_by,
                "created_at": doc.created_at,
                "versions": [
                    {
                        "id": v.id,
                        "version": v.version,
                        "status": v.processing_status,
                        "steps": v.processing_steps,
                        "confidence": v.confidence,
                        "reason": v.replace_reason,
                        "created_at": v.created_at,
                    }
                    for v in versions
                ],
            }
        )
    return result


@router.get("/documents/{document_id}")
def get_document(document_id: str, auth: AuthContext = Depends(get_current), db: Session = Depends(get_db)):
    doc = db.get(ShipmentDocument, document_id)
    if not doc:
        raise HTTPException(404, "Not found")
    org_owned(doc, auth)
    versions = db.scalars(select(DocumentVersion).where(DocumentVersion.document_id == doc.id)).all()
    evidence = db.scalars(
        select(Evidence).where(Evidence.document_id == doc.id).order_by(Evidence.created_at.desc())
    ).all()
    latest_version = max((v.version for v in versions), default=1)
    latest_evidence = [e for e in evidence if any(v.id == e.document_version_id and v.version == latest_version for v in versions)]
    return {
        "id": doc.id,
        "name": doc.name,
        "type": doc.document_type,
        "processing_status": doc.processing_status,
        "versions": [{"id": v.id, "version": v.version, "steps": v.processing_steps, "status": v.processing_status} for v in versions],
        "fields": [
            {
                "id": e.id,
                "field": e.field,
                "raw_value": e.raw_value,
                "normalized_value": e.normalized_value,
                "page": e.page,
                "confidence": e.confidence,
            }
            for e in latest_evidence
        ],
    }


@router.get("/documents/{document_id}/file")
def download_document(
    document_id: str,
    version: int | None = None,
    auth: AuthContext = Depends(get_current),
    db: Session = Depends(get_db),
):
    doc = db.get(ShipmentDocument, document_id)
    if not doc:
        raise HTTPException(404, "Not found")
    org_owned(doc, auth)
    q = select(DocumentVersion).where(DocumentVersion.document_id == doc.id)
    if version:
        q = q.where(DocumentVersion.version == version)
    else:
        q = q.order_by(DocumentVersion.version.desc())
    ver = db.scalars(q).first()
    if not ver:
        raise HTTPException(404, "Version not found")
    data = get_storage().get(ver.storage_key)
    return Response(content=data, media_type=ver.mime_type)


@router.get("/documents/{document_id}/versions")
def document_versions(document_id: str, auth: AuthContext = Depends(get_current), db: Session = Depends(get_db)):
    doc = db.get(ShipmentDocument, document_id)
    if not doc:
        raise HTTPException(404, "Not found")
    org_owned(doc, auth)
    versions = db.scalars(
        select(DocumentVersion).where(DocumentVersion.document_id == doc.id).order_by(DocumentVersion.version)
    ).all()
    compared = []
    for v in versions:
        fields = {e.field: e.normalized_value for e in db.scalars(select(Evidence).where(Evidence.document_version_id == v.id)).all()}
        compared.append({"id": v.id, "version": v.version, "fields": fields, "reason": v.replace_reason})
    return compared


@router.get("/shipments/{shipment_id}/compliance")
def shipment_compliance(shipment_id: str, auth: AuthContext = Depends(get_current), db: Session = Depends(get_db)):
    s = db.get(Shipment, shipment_id)
    if not s:
        raise HTTPException(404, "Not found")
    org_owned(s, auth)
    issues = db.scalars(select(ComplianceIssue).where(ComplianceIssue.shipment_id == shipment_id)).all()
    evals = db.scalars(
        select(ComplianceEvaluation)
        .where(ComplianceEvaluation.shipment_id == shipment_id)
        .order_by(ComplianceEvaluation.evaluated_at.desc())
    ).all()
    rules = {r.id: r for r in db.scalars(select(ComplianceRule)).all()}
    return {
        "disclaimer": "Demo compliance rules. Configure according to applicable jurisdiction and organizational policy.",
        "state": s.compliance_status,
        "document_completeness": s.document_completeness,
        "rules_passed": sum(1 for e in evals if e.result == "passed"),
        "warnings": sum(1 for i in issues if i.status == "OPEN" and i.severity != "CRITICAL"),
        "critical_issues": sum(1 for i in issues if i.status == "OPEN" and i.severity == "CRITICAL"),
        "issues": [
            IssueOut(
                id=i.id,
                title=i.title,
                description=i.description,
                severity=i.severity,
                status=i.status,
                recommended_action=i.recommended_action,
                risk_contribution=i.risk_contribution,
                evidence_ids=i.evidence_ids or [],
                rule_id=i.rule_id,
                shipment_id=i.shipment_id,
                created_at=i.created_at,
            ).model_dump()
            | {"rule_code": rules.get(i.rule_id).rule_code if rules.get(i.rule_id) else None}
            for i in issues
        ],
        "evaluations": [
            {
                "id": e.id,
                "result": e.result,
                "message": e.message,
                "rule": rules.get(e.rule_id).rule_code if rules.get(e.rule_id) else None,
                "rule_version_id": e.rule_version_id,
                "evaluated_at": e.evaluated_at,
            }
            for e in evals[:50]
        ],
    }


@router.post("/shipments/{shipment_id}/compliance/run")
def rerun_compliance(
    shipment_id: str,
    auth: AuthContext = Depends(require_roles("Admin", "Compliance Manager", "Operations Manager")),
    db: Session = Depends(get_db),
):
    s = db.get(Shipment, shipment_id)
    if not s:
        raise HTTPException(404, "Not found")
    org_owned(s, auth)
    run_compliance(db, s, changed_fields=None)
    recalculate_risk(db, s)
    db.commit()
    return {"detail": "Configured compliance checks re-run"}


@router.get("/compliance/issues/{issue_id}")
def get_issue(issue_id: str, auth: AuthContext = Depends(get_current), db: Session = Depends(get_db)):
    issue = db.get(ComplianceIssue, issue_id)
    if not issue:
        raise HTTPException(404, "Not found")
    org_owned(issue, auth)
    rule = db.get(ComplianceRule, issue.rule_id)
    return {
        **IssueOut.model_validate(issue, from_attributes=True).model_dump(),
        "rule_code": rule.rule_code if rule else None,
        "rule_name": rule.name if rule else None,
        "rule_source": rule.source if rule else None,
    }


@router.post("/compliance/issues/{issue_id}/resolve")
def resolve_issue(
    issue_id: str,
    payload: ReviewRequest,
    auth: AuthContext = Depends(require_roles("Admin", "Compliance Manager", "Reviewer")),
    db: Session = Depends(get_db),
):
    issue = db.get(ComplianceIssue, issue_id)
    if not issue:
        raise HTTPException(404, "Not found")
    org_owned(issue, auth)
    if payload.decision.lower() not in {"approve", "reject", "request_more_information", "override"}:
        raise HTTPException(400, "Unknown decision")
    if payload.decision.lower() == "override":
        issue.status = IssueStatus.OVERRIDDEN.value
    elif payload.decision.lower() == "approve":
        issue.status = IssueStatus.RESOLVED.value
    review = Review(
        id=uid(),
        organization_id=auth.organization_id,
        shipment_id=issue.shipment_id,
        issue_id=issue.id,
        reviewer_id=auth.user.id,
        decision=payload.decision,
        comment=payload.comment,
    )
    db.add(review)
    write_audit(
        db,
        organization_id=auth.organization_id,
        event_type="human_reviewed",
        description=f"Issue {issue.title}: {payload.decision}",
        shipment_id=issue.shipment_id,
        actor_id=auth.user.id,
        actor_type="user",
        entity_id=issue.id,
        entity_type="issue",
    )
    shipment = db.get(Shipment, issue.shipment_id)
    recalculate_risk(db, shipment)
    db.commit()
    return {"detail": "Review recorded"}


@router.get("/compliance/issues/{issue_id}/evidence")
def issue_evidence(issue_id: str, auth: AuthContext = Depends(get_current), db: Session = Depends(get_db)):
    issue = db.get(ComplianceIssue, issue_id)
    if not issue:
        raise HTTPException(404, "Not found")
    org_owned(issue, auth)
    evidence = []
    for eid in issue.evidence_ids or []:
        e = db.get(Evidence, eid)
        if e:
            evidence.append(
                {
                    "id": e.id,
                    "field": e.field,
                    "raw_value": e.raw_value,
                    "normalized_value": e.normalized_value,
                    "document_id": e.document_id,
                    "document_name": e.document_name,
                    "page": e.page,
                    "confidence": e.confidence,
                    "extraction_method": e.extraction_method,
                }
            )
    rule = db.get(ComplianceRule, issue.rule_id)
    return {
        "issue": issue.title,
        "rule": rule.rule_code if rule else None,
        "rule_version_needed": True,
        "risk_contribution": issue.risk_contribution,
        "recommended_action": issue.recommended_action,
        "evidence": evidence,
        "disclaimer": "Demo compliance rules. Configure according to applicable jurisdiction and organizational policy.",
    }


@router.get("/shipments/{shipment_id}/risk")
def get_risk(shipment_id: str, auth: AuthContext = Depends(get_current), db: Session = Depends(get_db)):
    s = db.get(Shipment, shipment_id)
    if not s:
        raise HTTPException(404, "Not found")
    org_owned(s, auth)
    latest = db.scalars(
        select(RiskAssessment).where(RiskAssessment.shipment_id == shipment_id).order_by(RiskAssessment.created_at.desc())
    ).first()
    factors = []
    if latest:
        factors = [{"label": f.label, "points": f.points, "category": f.category} for f in latest.factors]
    return {"score": s.risk_score, "level": s.risk_level, "previous_score": latest.previous_score if latest else None, "factors": factors}


@router.get("/shipments/{shipment_id}/risk/history")
def risk_history(shipment_id: str, auth: AuthContext = Depends(get_current), db: Session = Depends(get_db)):
    s = db.get(Shipment, shipment_id)
    if not s:
        raise HTTPException(404, "Not found")
    org_owned(s, auth)
    rows = db.scalars(
        select(RiskAssessment).where(RiskAssessment.shipment_id == shipment_id).order_by(RiskAssessment.created_at)
    ).all()
    return [
        {"id": r.id, "score": r.score, "previous_score": r.previous_score, "level": r.level, "reason": r.reason, "created_at": r.created_at}
        for r in rows
    ]


@router.post("/shipments/{shipment_id}/risk/recalculate")
def risk_recalc(
    shipment_id: str,
    auth: AuthContext = Depends(require_roles("Admin", "Compliance Manager")),
    db: Session = Depends(get_db),
):
    s = db.get(Shipment, shipment_id)
    if not s:
        raise HTTPException(404, "Not found")
    org_owned(s, auth)
    recalculate_risk(db, s)
    db.commit()
    return {"score": s.risk_score, "level": s.risk_level}


@router.get("/shipments/{shipment_id}/agent/activity")
def agent_activity(shipment_id: str, auth: AuthContext = Depends(get_current), db: Session = Depends(get_db)):
    s = db.get(Shipment, shipment_id)
    if not s:
        raise HTTPException(404, "Not found")
    org_owned(s, auth)
    runs = db.scalars(select(AgentRun).where(AgentRun.shipment_id == shipment_id).order_by(AgentRun.created_at)).all()
    actions = db.scalars(select(AgentAction).where(AgentAction.shipment_id == shipment_id).order_by(AgentAction.created_at)).all()
    return {
        "runs": [{"id": r.id, "trigger": r.trigger, "decision": r.decision, "summary": r.summary, "created_at": r.created_at} for r in runs],
        "actions": [{"id": a.id, "type": a.action_type, "detail": a.detail, "created_at": a.created_at} for a in actions],
    }


@router.post("/shipments/{shipment_id}/agent/run")
def agent_run(
    shipment_id: str,
    auth: AuthContext = Depends(require_roles("Admin", "Compliance Manager", "Operations Manager")),
    db: Session = Depends(get_db),
):
    from app.agent.orchestrator import run_agent

    s = db.get(Shipment, shipment_id)
    if not s:
        raise HTTPException(404, "Not found")
    org_owned(s, auth)
    run = run_agent(db, s, trigger="MANUAL")
    db.commit()
    return {"id": run.id, "decision": run.decision, "summary": run.summary}


@router.get("/shipments/{shipment_id}/traceability")
def traceability(shipment_id: str, auth: AuthContext = Depends(get_current), db: Session = Depends(get_db)):
    s = db.get(Shipment, shipment_id)
    if not s:
        raise HTTPException(404, "Not found")
    org_owned(s, auth)
    nodes = db.scalars(select(TraceabilityNode).where(TraceabilityNode.shipment_id == shipment_id)).all()
    edges = db.scalars(select(TraceabilityEdge).where(TraceabilityEdge.shipment_id == shipment_id)).all()
    return {
        "nodes": [
            {"id": n.id, "label": n.label, "kind": n.kind, "location": n.location, "details": n.details, "risk": n.risk}
            for n in nodes
        ],
        "edges": [
            {
                "id": e.id,
                "from": e.from_node_id,
                "to": e.to_node_id,
                "relationship": e.relationship,
                "occurred_on": e.occurred_on,
                "source": e.source,
            }
            for e in edges
        ],
    }


@router.get("/shipments/{shipment_id}/audit")
def audit_trail(
    shipment_id: str,
    category: str | None = None,
    auth: AuthContext = Depends(get_current),
    db: Session = Depends(get_db),
):
    s = db.get(Shipment, shipment_id)
    if not s:
        raise HTTPException(404, "Not found")
    org_owned(s, auth)
    q = select(AuditEvent).where(AuditEvent.shipment_id == shipment_id).order_by(AuditEvent.timestamp.desc())
    if category and category != "All":
        mapping = {
            "Documents": "document",
            "Compliance": "rule",
            "Risk": "risk",
            "Agent": "agent",
            "Human Review": "human",
            "Tasks": "task",
            "Status": "shipment_state",
        }
        key = mapping.get(category, category.lower())
        q = q.where(AuditEvent.event_type.ilike(f"%{key}%"))
    events = db.scalars(q).all()
    return [
        {
            "id": e.id,
            "timestamp": e.timestamp,
            "event_type": e.event_type,
            "description": e.description,
            "actor_type": e.actor_type,
            "previous_state": e.previous_state,
            "new_state": e.new_state,
            "metadata": e.metadata_json,
        }
        for e in events
    ]


@router.get("/shipments/{shipment_id}/overview")
def overview(shipment_id: str, auth: AuthContext = Depends(get_current), db: Session = Depends(get_db)):
    s = db.get(Shipment, shipment_id)
    if not s:
        raise HTTPException(404, "Not found")
    org_owned(s, auth)
    issues = db.scalars(
        select(ComplianceIssue).where(ComplianceIssue.shipment_id == shipment_id, ComplianceIssue.status == "OPEN")
    ).all()
    tasks = db.scalars(select(Task).where(Task.shipment_id == shipment_id, Task.status != "COMPLETED")).all()
    next_action = issues[0].recommended_action if issues else "Configured compliance checks passed. Human clearance still required."
    from app.ai.rag import retrieve_regulation

    rag = retrieve_regulation(
        db,
        f"origin destination {s.destination_country} product compliance documentation",
        s.destination_country,
    )
    return {
        "shipment": _shipment_out(s),
        "open_issues": len(issues),
        "critical_issues": [i.title for i in issues if i.severity == "CRITICAL"],
        "open_tasks": len(tasks),
        "next_recommended_action": next_action,
        "disclaimer": "Demo compliance rules. Configure according to applicable jurisdiction and organizational policy.",
        "regulatory": rag,
    }


@router.post("/shipments/{shipment_id}/reviews")
def shipment_review(
    shipment_id: str,
    payload: ReviewRequest,
    auth: AuthContext = Depends(require_roles("Admin", "Compliance Manager", "Reviewer")),
    db: Session = Depends(get_db),
):
    s = db.get(Shipment, shipment_id)
    if not s:
        raise HTTPException(404, "Not found")
    org_owned(s, auth)
    if payload.decision.lower() == "approve":
        if any(
            i.severity == "CRITICAL" and i.status == "OPEN"
            for i in db.scalars(select(ComplianceIssue).where(ComplianceIssue.shipment_id == s.id)).all()
        ):
            raise HTTPException(400, "Cannot clear a shipment with open critical configured-rule failures")
        s.compliance_status = "CLEARED"
        s.under_review = False
    elif payload.decision.lower() == "reject":
        s.under_review = False
    elif payload.decision.lower() == "request_more_information":
        s.under_review = True
        s.compliance_status = "UNDER_REVIEW"
    review = Review(
        id=uid(),
        organization_id=auth.organization_id,
        shipment_id=s.id,
        reviewer_id=auth.user.id,
        decision=payload.decision,
        comment=payload.comment,
    )
    db.add(review)
    write_audit(
        db,
        organization_id=auth.organization_id,
        event_type="human_reviewed",
        description=f"Shipment review: {payload.decision}",
        shipment_id=s.id,
        actor_id=auth.user.id,
        actor_type="user",
        previous_state=None,
        new_state=s.compliance_status,
    )
    db.commit()
    return {"detail": "Human decision recorded", "compliance_status": s.compliance_status}


@router.get("/tasks")
def list_tasks(
    shipment_id: str | None = None,
    auth: AuthContext = Depends(get_current),
    db: Session = Depends(get_db),
):
    q = select(Task).where(Task.organization_id == auth.organization_id)
    if shipment_id:
        q = q.where(Task.shipment_id == shipment_id)
    tasks = db.scalars(q.order_by(Task.created_at.desc())).all()
    return [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "shipment_id": t.shipment_id,
            "issue_id": t.issue_id,
            "priority": t.priority,
            "status": t.status,
            "due_date": t.due_date,
            "created_at": t.created_at,
            "supplier_id": t.supplier_id,
        }
        for t in tasks
    ]


@router.post("/tasks")
def create_task(
    payload: TaskCreate,
    auth: AuthContext = Depends(require_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
):
    t = Task(
        id=uid(),
        organization_id=auth.organization_id,
        created_by=auth.user.id,
        **payload.model_dump(),
    )
    db.add(t)
    db.commit()
    return {"id": t.id}


@router.put("/tasks/{task_id}")
def update_task(
    task_id: str,
    payload: TaskUpdate,
    auth: AuthContext = Depends(require_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
):
    t = db.get(Task, task_id)
    if not t:
        raise HTTPException(404, "Not found")
    org_owned(t, auth)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(t, key, value)
    db.commit()
    return {"id": t.id, "status": t.status}


@router.get("/queue")
def operations_queue(
    severity: str | None = None,
    status: str | None = "OPEN",
    auth: AuthContext = Depends(get_current),
    db: Session = Depends(get_db),
):
    q = select(ComplianceIssue).where(ComplianceIssue.organization_id == auth.organization_id)
    if status:
        q = q.where(ComplianceIssue.status == status)
    if severity:
        q = q.where(ComplianceIssue.severity == severity)
    issues = db.scalars(q.order_by(ComplianceIssue.created_at)).all()
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    items = []
    for i in issues:
        counts[i.severity] = counts.get(i.severity, 0) + 1
        shipment = db.get(Shipment, i.shipment_id)
        items.append(
            {
                "id": i.id,
                "title": i.title,
                "severity": i.severity,
                "status": i.status,
                "shipment_id": i.shipment_id,
                "shipment_ref": shipment.reference_number if shipment else None,
                "destination": shipment.destination_country if shipment else None,
                "recommended_action": i.recommended_action,
                "created_at": i.created_at,
            }
        )
    return {"counts": counts, "items": items}


@router.get("/notifications")
def notifications(auth: AuthContext = Depends(get_current), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Notification)
        .where(Notification.organization_id == auth.organization_id)
        .order_by(Notification.created_at.desc())
        .limit(50)
    ).all()
    return [{"id": n.id, "title": n.title, "body": n.body, "kind": n.kind, "read": n.read, "created_at": n.created_at} for n in rows]


@router.get("/dashboard/summary")
def dashboard(auth: AuthContext = Depends(get_current), db: Session = Depends(get_db)):
    shipments = db.scalars(select(Shipment).where(Shipment.organization_id == auth.organization_id)).all()
    docs = db.scalars(select(ShipmentDocument).where(ShipmentDocument.organization_id == auth.organization_id)).all()
    issues = db.scalars(
        select(ComplianceIssue).where(
            ComplianceIssue.organization_id == auth.organization_id, ComplianceIssue.status == "OPEN"
        )
    ).all()
    by_state: dict[str, int] = {}
    by_risk: dict[str, int] = {}
    for s in shipments:
        by_state[s.compliance_status] = by_state.get(s.compliance_status, 0) + 1
        by_risk[s.risk_level] = by_risk.get(s.risk_level, 0) + 1
    by_issue = {}
    for i in issues:
        by_issue[i.title] = by_issue.get(i.title, 0) + 1
    return {
        "total_shipments": len(shipments),
        "needs_review": by_state.get("READY_FOR_REVIEW", 0) + by_state.get("WARNING", 0) + by_state.get("UNDER_REVIEW", 0),
        "blocked": by_state.get("BLOCKED", 0),
        "high_risk": by_risk.get("HIGH", 0) + by_risk.get("CRITICAL", 0),
        "documents_processed": len(docs),
        "open_issues": len(issues),
        "risk_distribution": by_risk,
        "state_distribution": by_state,
        "issue_categories": by_issue,
    }


@router.get("/search")
def search(q: str = Query(min_length=1), auth: AuthContext = Depends(get_current), db: Session = Depends(get_db)):
    like = f"%{q}%"
    shipments = db.scalars(
        select(Shipment).where(Shipment.organization_id == auth.organization_id, Shipment.reference_number.ilike(like))
    ).all()
    docs = db.scalars(
        select(ShipmentDocument).where(ShipmentDocument.organization_id == auth.organization_id, ShipmentDocument.name.ilike(like))
    ).all()
    issues = db.scalars(
        select(ComplianceIssue).where(ComplianceIssue.organization_id == auth.organization_id, ComplianceIssue.title.ilike(like))
    ).all()
    return {
        "shipments": [{"id": s.id, "reference_number": s.reference_number} for s in shipments],
        "documents": [{"id": d.id, "name": d.name, "shipment_id": d.shipment_id} for d in docs],
        "issues": [{"id": i.id, "title": i.title, "shipment_id": i.shipment_id} for i in issues],
    }
