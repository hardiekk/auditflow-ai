from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import write_audit
from app.models.entities import (
    ComplianceEvaluation,
    ComplianceIssue,
    ComplianceRule,
    DocumentType,
    Evidence,
    IssueStatus,
    RuleVersion,
    Severity,
    Shipment,
    ShipmentDocument,
    uid,
)

REQUIRED_DOCS = [
    DocumentType.COMMERCIAL_INVOICE.value,
    DocumentType.PACKING_LIST.value,
    DocumentType.BILL_OF_LADING.value,
    DocumentType.CERTIFICATE_OF_ORIGIN.value,
]

RISK_POINTS = {
    Severity.CRITICAL.value: 30,
    Severity.HIGH.value: 20,
    Severity.MEDIUM.value: 10,
    Severity.LOW.value: 5,
}

FIELD_RULE_MAP = {
    "country_of_origin": ["RULE-002"],
    "quantity": ["RULE-003"],
    "gross_weight": ["RULE-004"],
    "weight": ["RULE-004"],
    "expiry_date": ["RULE-005"],
    "hs_code": ["RULE-006", "RULE-007"],
    "seller": ["RULE-009"],
    "exporter": ["RULE-009"],
    "invoice_date": ["RULE-010"],
    "document_type": ["RULE-001", "RULE-008"],
}


def latest_evidence(db: Session, shipment_id: str, field: str, document_type: str | None = None) -> Evidence | None:
    q = (
        select(Evidence)
        .join(ShipmentDocument, ShipmentDocument.id == Evidence.document_id)
        .where(Evidence.shipment_id == shipment_id, Evidence.field == field)
        .order_by(Evidence.created_at.desc())
    )
    if document_type:
        q = q.where(ShipmentDocument.document_type == document_type)
    return db.scalars(q).first()


def _docs_by_type(db: Session, shipment_id: str) -> dict[str, ShipmentDocument]:
    docs = db.scalars(select(ShipmentDocument).where(ShipmentDocument.shipment_id == shipment_id)).all()
    current: dict[str, ShipmentDocument] = {}
    for doc in docs:
        current[doc.document_type] = doc
    return current


def _pass(rule: ComplianceRule, version: RuleVersion, shipment: Shipment, message: str, evidence_ids: list[str]) -> ComplianceEvaluation:
    return ComplianceEvaluation(
        id=uid(),
        organization_id=shipment.organization_id,
        shipment_id=shipment.id,
        rule_id=rule.id,
        rule_version_id=version.id,
        result="passed",
        message=message,
        evidence_ids=evidence_ids,
    )


def _fail(
    rule: ComplianceRule,
    version: RuleVersion,
    shipment: Shipment,
    message: str,
    evidence_ids: list[str],
    title: str,
    recommended: str,
) -> tuple[ComplianceEvaluation, ComplianceIssue]:
    ev = ComplianceEvaluation(
        id=uid(),
        organization_id=shipment.organization_id,
        shipment_id=shipment.id,
        rule_id=rule.id,
        rule_version_id=version.id,
        result="failed",
        message=message,
        evidence_ids=evidence_ids,
    )
    issue = ComplianceIssue(
        id=uid(),
        organization_id=shipment.organization_id,
        shipment_id=shipment.id,
        rule_id=rule.id,
        evaluation_id=ev.id,
        title=title,
        description=message,
        severity=rule.severity,
        status=IssueStatus.OPEN.value,
        recommended_action=recommended,
        evidence_ids=evidence_ids,
        risk_contribution=RISK_POINTS.get(rule.severity, 10),
    )
    return ev, issue


def evaluate_rule(db: Session, shipment: Shipment, rule: ComplianceRule, version: RuleVersion) -> tuple[ComplianceEvaluation, ComplianceIssue | None]:
    docs = _docs_by_type(db, shipment.id)
    code = rule.rule_code
    evidence_ids: list[str] = []

    if code == "RULE-001":
        present = [t for t in REQUIRED_DOCS if t in docs]
        missing = [t for t in REQUIRED_DOCS if t not in docs]
        if missing:
            ev, issue = _fail(
                rule,
                version,
                shipment,
                f"Missing required documents: {', '.join(missing)}. Present: {', '.join(present) or 'none'}.",
                [],
                "Required documents missing",
                "Upload the missing trade documents.",
            )
            return ev, issue
        return _pass(rule, version, shipment, "All required demo documents are present.", []), None

    if code == "RULE-002":
        inv = latest_evidence(db, shipment.id, "country_of_origin", DocumentType.COMMERCIAL_INVOICE.value)
        coo = latest_evidence(db, shipment.id, "country_of_origin", DocumentType.CERTIFICATE_OF_ORIGIN.value)
        if not inv or not coo:
            return _pass(rule, version, shipment, "Origin consistency skipped until both invoice and certificate exist.", []), None
        evidence_ids = [inv.id, coo.id]
        if inv.normalized_value != coo.normalized_value:
            ev, issue = _fail(
                rule,
                version,
                shipment,
                (
                    f"Configured origin consistency rule failed. Invoice: {inv.raw_value} "
                    f"({inv.normalized_value}); Certificate of Origin: {coo.raw_value} ({coo.normalized_value})."
                ),
                evidence_ids,
                "Country of Origin Conflict",
                "Request a corrected Certificate of Origin.",
            )
            return ev, issue
        return _pass(rule, version, shipment, "Invoice origin matches Certificate of Origin.", evidence_ids), None

    if code == "RULE-003":
        inv = latest_evidence(db, shipment.id, "quantity", DocumentType.COMMERCIAL_INVOICE.value)
        pl = latest_evidence(db, shipment.id, "quantity", DocumentType.PACKING_LIST.value)
        if not inv or not pl:
            return _pass(rule, version, shipment, "Quantity check skipped until invoice and packing list exist.", []), None
        evidence_ids = [inv.id, pl.id]
        try:
            delta = abs(float(inv.normalized_value or 0) - float(pl.normalized_value or 0))
        except ValueError:
            delta = 0
        if delta > 0:
            ev, issue = _fail(
                rule,
                version,
                shipment,
                f"Quantity mismatch: invoice {inv.raw_value} vs packing list {pl.raw_value} (delta {delta:g} units).",
                evidence_ids,
                "Quantity mismatch",
                "Reconcile packing quantities with the commercial invoice.",
            )
            return ev, issue
        return _pass(rule, version, shipment, "Invoice quantity matches packing list.", evidence_ids), None

    if code == "RULE-004":
        pl = latest_evidence(db, shipment.id, "gross_weight", DocumentType.PACKING_LIST.value)
        bl = latest_evidence(db, shipment.id, "weight", DocumentType.BILL_OF_LADING.value)
        if not pl or not bl:
            return _pass(rule, version, shipment, "Weight check skipped until packing list and bill of lading exist.", []), None
        evidence_ids = [pl.id, bl.id]
        try:
            delta = abs(float(pl.normalized_value or 0) - float(bl.normalized_value or 0))
        except ValueError:
            delta = 0
        if delta > 1:
            ev, issue = _fail(
                rule,
                version,
                shipment,
                f"Weight mismatch: packing list {pl.raw_value} vs bill of lading {bl.raw_value}.",
                evidence_ids,
                "Weight mismatch",
                "Confirm scale tickets and bill of lading weight.",
            )
            return ev, issue
        return _pass(rule, version, shipment, "Packing list weight matches bill of lading.", evidence_ids), None

    if code == "RULE-005":
        expired: list[Evidence] = []
        for dtype in (DocumentType.CERTIFICATE_OF_ORIGIN.value, DocumentType.PRODUCT_CERTIFICATE.value):
            evd = latest_evidence(db, shipment.id, "expiry_date", dtype)
            if evd and evd.normalized_value:
                try:
                    if date.fromisoformat(evd.normalized_value) < date.today():
                        expired.append(evd)
                except ValueError:
                    pass
        if expired:
            ev, issue = _fail(
                rule,
                version,
                shipment,
                "Certificate expiry check failed for: " + ", ".join(f"{e.document_name} ({e.raw_value})" for e in expired),
                [e.id for e in expired],
                "Expired certificate",
                "Request a current product or origin certificate.",
            )
            return ev, issue
        return _pass(rule, version, shipment, "No expired certificates detected among extracted dates.", []), None

    if code == "RULE-006":
        hs = latest_evidence(db, shipment.id, "hs_code", DocumentType.COMMERCIAL_INVOICE.value)
        if not hs or not hs.normalized_value:
            ev, issue = _fail(
                rule,
                version,
                shipment,
                "HS code is missing from the commercial invoice extraction.",
                [hs.id] if hs else [],
                "HS code missing",
                "Confirm product classification on the invoice.",
            )
            return ev, issue
        return _pass(rule, version, shipment, f"HS code present: {hs.raw_value}.", [hs.id]), None

    if code == "RULE-007":
        hs = latest_evidence(db, shipment.id, "hs_code", DocumentType.COMMERCIAL_INVOICE.value)
        if not hs:
            return _pass(rule, version, shipment, "HS format skipped; no code extracted.", []), None
        digits = hs.normalized_value or ""
        if not digits.isdigit() or len(digits) < 4:
            ev, issue = _fail(
                rule,
                version,
                shipment,
                f"HS code format check failed for value {hs.raw_value}.",
                [hs.id],
                "HS code format",
                "Verify the HS code format with classification.",
            )
            return ev, issue
        return _pass(rule, version, shipment, "HS code format is valid for demo rules.", [hs.id]), None

    if code == "RULE-008":
        if DocumentType.PRODUCT_CERTIFICATE.value not in docs:
            ev, issue = _fail(
                rule,
                version,
                shipment,
                "Mandatory product certificate is missing for this demo product scope.",
                [],
                "Mandatory certificate missing",
                "Upload a valid product certificate.",
            )
            return ev, issue
        return _pass(rule, version, shipment, "Product certificate is present.", []), None

    if code == "RULE-009":
        seller = latest_evidence(db, shipment.id, "seller", DocumentType.COMMERCIAL_INVOICE.value)
        exporter = latest_evidence(db, shipment.id, "exporter", DocumentType.CERTIFICATE_OF_ORIGIN.value)
        if not seller or not exporter:
            return _pass(rule, version, shipment, "Supplier identity check skipped until both names exist.", []), None
        if seller.normalized_value != exporter.normalized_value:
            ev, issue = _fail(
                rule,
                version,
                shipment,
                f"Supplier identity mismatch: invoice seller {seller.raw_value} vs certificate exporter {exporter.raw_value}.",
                [seller.id, exporter.id],
                "Supplier identity inconsistency",
                "Confirm the legal supplier name across documents.",
            )
            return ev, issue
        return _pass(rule, version, shipment, "Supplier identity is consistent across documents.", [seller.id, exporter.id]), None

    if code == "RULE-010":
        inv_date = latest_evidence(db, shipment.id, "invoice_date", DocumentType.COMMERCIAL_INVOICE.value)
        if inv_date and inv_date.normalized_value and shipment.estimated_arrival:
            try:
                if date.fromisoformat(inv_date.normalized_value) > shipment.estimated_arrival:
                    ev, issue = _fail(
                        rule,
                        version,
                        shipment,
                        "Invoice date is after estimated arrival.",
                        [inv_date.id],
                        "Shipment date validation",
                        "Confirm invoice and sailing dates.",
                    )
                    return ev, issue
            except ValueError:
                pass
        return _pass(rule, version, shipment, "Shipment date validation passed for configured demo rule.", []), None

    return _pass(rule, version, shipment, "Rule has no evaluator; treated as informational pass.", []), None


def active_rule_versions(db: Session) -> list[tuple[ComplianceRule, RuleVersion]]:
    rules = db.scalars(select(ComplianceRule).where(ComplianceRule.enabled.is_(True))).all()
    pairs = []
    for rule in rules:
        version = max(rule.versions, key=lambda v: v.version, default=None)
        if version:
            pairs.append((rule, version))
    return pairs


def rules_for_fields(db: Session, fields: set[str] | None) -> list[tuple[ComplianceRule, RuleVersion]]:
    pairs = active_rule_versions(db)
    if not fields:
        return pairs
    codes = set()
    for field in fields:
        codes.update(FIELD_RULE_MAP.get(field, []))
    codes.update(["RULE-001", "RULE-008"])
    return [(r, v) for r, v in pairs if r.rule_code in codes]


def run_compliance(db: Session, shipment: Shipment, changed_fields: set[str] | None = None) -> list[ComplianceIssue]:
    created: list[ComplianceIssue] = []
    for rule, version in rules_for_fields(db, changed_fields):
        open_issues = db.scalars(
            select(ComplianceIssue).where(
                ComplianceIssue.shipment_id == shipment.id,
                ComplianceIssue.rule_id == rule.id,
                ComplianceIssue.status == IssueStatus.OPEN.value,
            )
        ).all()
        evaluation, issue = evaluate_rule(db, shipment, rule, version)
        db.add(evaluation)
        write_audit(
            db,
            organization_id=shipment.organization_id,
            event_type="rule_executed",
            description=f"{rule.rule_code} v{version.version} {evaluation.result}",
            shipment_id=shipment.id,
            entity_type="rule",
            entity_id=rule.id,
            metadata={"rule_version": version.version, "result": evaluation.result},
        )
        if issue is None:
            for existing in open_issues:
                existing.status = IssueStatus.RESOLVED.value
                write_audit(
                    db,
                    organization_id=shipment.organization_id,
                    event_type="issue_resolved",
                    description=f"Issue resolved after re-evaluation of {rule.rule_code}",
                    shipment_id=shipment.id,
                    entity_type="issue",
                    entity_id=existing.id,
                    previous_state="OPEN",
                    new_state="RESOLVED",
                )
        else:
            if open_issues:
                existing = open_issues[0]
                existing.description = issue.description
                existing.evidence_ids = issue.evidence_ids
                existing.evaluation_id = evaluation.id
                existing.recommended_action = issue.recommended_action
            else:
                db.add(issue)
                created.append(issue)
                write_audit(
                    db,
                    organization_id=shipment.organization_id,
                    event_type="issue_created",
                    description=issue.title,
                    shipment_id=shipment.id,
                    entity_type="issue",
                    entity_id=issue.id,
                    metadata={"severity": issue.severity, "rule": rule.rule_code},
                )
    db.flush()
    return created
