from __future__ import annotations
from typing import Optional

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.core.db import Base


def uid() -> str:
    return str(uuid.uuid4())


class RoleName(str, enum.Enum):
    ADMIN = "Admin"
    COMPLIANCE_MANAGER = "Compliance Manager"
    OPERATIONS_MANAGER = "Operations Manager"
    REVIEWER = "Reviewer"
    VIEWER = "Viewer"


class ComplianceState(str, enum.Enum):
    DRAFT = "DRAFT"
    PROCESSING = "PROCESSING"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    WARNING = "WARNING"
    BLOCKED = "BLOCKED"
    UNDER_REVIEW = "UNDER_REVIEW"
    CLEARED = "CLEARED"


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DocumentType(str, enum.Enum):
    COMMERCIAL_INVOICE = "commercial_invoice"
    PACKING_LIST = "packing_list"
    BILL_OF_LADING = "bill_of_lading"
    CERTIFICATE_OF_ORIGIN = "certificate_of_origin"
    INSURANCE_CERTIFICATE = "insurance_certificate"
    PRODUCT_CERTIFICATE = "product_certificate"
    SUPPLIER_DECLARATION = "supplier_declaration"
    OTHER = "other"


class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DUPLICATE = "duplicate"


class Severity(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class IssueStatus(str, enum.Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    OVERRIDDEN = "OVERRIDDEN"


class TaskStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING_FOR_SUPPLIER = "WAITING_FOR_SUPPLIER"
    COMPLETED = "COMPLETED"
    ESCALATED = "ESCALATED"


class TaskPriority(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class AgentDecision(str, enum.Enum):
    NO_ACTION = "NO_ACTION"
    REQUEST_DOCUMENT = "REQUEST_DOCUMENT"
    REQUEST_CORRECTION = "REQUEST_CORRECTION"
    CREATE_REVIEW_TASK = "CREATE_REVIEW_TASK"
    ESCALATE = "ESCALATE"
    RE_RUN_CHECK = "RE_RUN_CHECK"
    NOTIFY_USER = "NOTIFY_USER"


class ActorType(str, enum.Enum):
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    members: Mapped[list[OrganizationMember]] = relationship(back_populates="organization")


class User(Base, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    memberships: Mapped[list[OrganizationMember]] = relationship(back_populates="user")


class Role(Base):
    __tablename__ = "roles"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(64), unique=True)


class OrganizationMember(Base, TimestampMixin):
    __tablename__ = "organization_members"
    __table_args__ = (UniqueConstraint("organization_id", "user_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    role_id: Mapped[str] = mapped_column(ForeignKey("roles.id"))
    organization: Mapped[Organization] = relationship(back_populates="members")
    user: Mapped[User] = relationship(back_populates="memberships")
    role: Mapped[Role] = relationship()


class Supplier(Base, TimestampMixin):
    __tablename__ = "suppliers"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    country: Mapped[Optional[str]] = mapped_column(String(8))
    risk_note: Mapped[Optional[str]] = mapped_column(Text)


class Customer(Base, TimestampMixin):
    __tablename__ = "customers"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    country: Mapped[Optional[str]] = mapped_column(String(8))


class Product(Base, TimestampMixin):
    __tablename__ = "products"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    sku: Mapped[str] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(Text)
    hs_code: Mapped[Optional[str]] = mapped_column(String(16))


class Shipment(Base, TimestampMixin):
    __tablename__ = "shipments"
    __table_args__ = (Index("ix_shipments_org_status", "organization_id", "compliance_status"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    reference_number: Mapped[str] = mapped_column(String(64), index=True)
    origin_country: Mapped[Optional[str]] = mapped_column(String(8))
    destination_country: Mapped[Optional[str]] = mapped_column(String(8))
    origin_port: Mapped[Optional[str]] = mapped_column(String(128))
    destination_port: Mapped[Optional[str]] = mapped_column(String(128))
    shipment_date: Mapped[Optional[datetime]] = mapped_column(Date)
    estimated_arrival: Mapped[Optional[datetime]] = mapped_column(Date)
    carrier: Mapped[Optional[str]] = mapped_column(String(128))
    supplier_id: Mapped[Optional[str]] = mapped_column(ForeignKey("suppliers.id"))
    customer_id: Mapped[Optional[str]] = mapped_column(ForeignKey("customers.id"))
    status: Mapped[str] = mapped_column(String(32), default="open")
    compliance_status: Mapped[str] = mapped_column(String(32), default=ComplianceState.DRAFT.value)
    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    risk_level: Mapped[str] = mapped_column(String(16), default=RiskLevel.LOW.value)
    document_completeness: Mapped[float] = mapped_column(Float, default=0)
    under_review: Mapped[bool] = mapped_column(Boolean, default=False)
    supplier: Mapped[Optional[Supplier]] = relationship()
    customer: Mapped[Optional[Customer]] = relationship()
    documents: Mapped[list[ShipmentDocument]] = relationship(back_populates="shipment")


class ShipmentParty(Base):
    __tablename__ = "shipment_parties"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    shipment_id: Mapped[str] = mapped_column(ForeignKey("shipments.id"), index=True)
    role: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(255))
    country: Mapped[Optional[str]] = mapped_column(String(8))


class ShipmentDocument(Base, TimestampMixin):
    __tablename__ = "shipment_documents"
    __table_args__ = (Index("ix_docs_hash", "organization_id", "file_hash"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    shipment_id: Mapped[str] = mapped_column(ForeignKey("shipments.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    document_type: Mapped[str] = mapped_column(String(64), default=DocumentType.OTHER.value)
    file_hash: Mapped[str] = mapped_column(String(64), index=True)
    current_version: Mapped[int] = mapped_column(Integer, default=1)
    processing_status: Mapped[str] = mapped_column(String(32), default=ProcessingStatus.PENDING.value)
    uploaded_by: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"))
    shipment: Mapped[Shipment] = relationship(back_populates="documents")
    versions: Mapped[list[DocumentVersion]] = relationship(back_populates="document")


class DocumentVersion(Base, TimestampMixin):
    __tablename__ = "document_versions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("shipment_documents.id"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    storage_key: Mapped[str] = mapped_column(String(512))
    file_hash: Mapped[str] = mapped_column(String(64))
    mime_type: Mapped[str] = mapped_column(String(128), default="application/pdf")
    uploaded_by: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"))
    replace_reason: Mapped[Optional[str]] = mapped_column(Text)
    previous_version_id: Mapped[Optional[str]] = mapped_column(ForeignKey("document_versions.id"))
    processing_status: Mapped[str] = mapped_column(String(32), default=ProcessingStatus.PENDING.value)
    processing_steps: Mapped[dict] = mapped_column(JSON, default=dict)
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    document: Mapped[ShipmentDocument] = relationship(back_populates="versions")


class DocumentExtraction(Base, TimestampMixin):
    __tablename__ = "document_extractions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    document_version_id: Mapped[str] = mapped_column(ForeignKey("document_versions.id"), index=True)
    fields: Mapped[dict] = mapped_column(JSON, default=dict)
    raw_text: Mapped[Optional[str]] = mapped_column(Text)
    classification: Mapped[Optional[str]] = mapped_column(String(64))
    classification_confidence: Mapped[Optional[float]] = mapped_column(Float)


class Evidence(Base, TimestampMixin):
    __tablename__ = "evidence"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    shipment_id: Mapped[str] = mapped_column(ForeignKey("shipments.id"), index=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("shipment_documents.id"), index=True)
    document_version_id: Mapped[str] = mapped_column(ForeignKey("document_versions.id"), index=True)
    field: Mapped[str] = mapped_column(String(128), index=True)
    raw_value: Mapped[Optional[str]] = mapped_column(Text)
    normalized_value: Mapped[Optional[str]] = mapped_column(Text)
    normalization_method: Mapped[Optional[str]] = mapped_column(String(64))
    page: Mapped[Optional[int]] = mapped_column(Integer)
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    extraction_method: Mapped[str] = mapped_column(String(64), default="mock")
    document_name: Mapped[Optional[str]] = mapped_column(String(255))


class ComplianceRule(Base, TimestampMixin):
    __tablename__ = "compliance_rules"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    organization_id: Mapped[Optional[str]] = mapped_column(String(36), index=True)
    rule_code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    jurisdiction: Mapped[str] = mapped_column(String(64), default="DEMO")
    product_scope: Mapped[str] = mapped_column(String(128), default="all")
    severity: Mapped[str] = mapped_column(String(16))
    required_documents: Mapped[list] = mapped_column(JSON, default=list)
    action: Mapped[str] = mapped_column(String(255))
    source: Mapped[str] = mapped_column(String(255), default="Demo compliance rules")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    field_dependencies: Mapped[list] = mapped_column(JSON, default=list)
    versions: Mapped[list[RuleVersion]] = relationship(back_populates="rule")


class RuleVersion(Base, TimestampMixin):
    __tablename__ = "rule_versions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    rule_id: Mapped[str] = mapped_column(ForeignKey("compliance_rules.id"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    conditions: Mapped[dict] = mapped_column(JSON, default=dict)
    effective_from: Mapped[Optional[datetime]] = mapped_column(Date)
    effective_until: Mapped[Optional[datetime]] = mapped_column(Date)
    rule: Mapped[ComplianceRule] = relationship(back_populates="versions")


class ComplianceEvaluation(Base, TimestampMixin):
    __tablename__ = "compliance_evaluations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    shipment_id: Mapped[str] = mapped_column(ForeignKey("shipments.id"), index=True)
    rule_id: Mapped[str] = mapped_column(ForeignKey("compliance_rules.id"))
    rule_version_id: Mapped[str] = mapped_column(ForeignKey("rule_versions.id"))
    result: Mapped[str] = mapped_column(String(32))
    message: Mapped[str] = mapped_column(Text)
    evidence_ids: Mapped[list] = mapped_column(JSON, default=list)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ComplianceIssue(Base, TimestampMixin):
    __tablename__ = "compliance_issues"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    shipment_id: Mapped[str] = mapped_column(ForeignKey("shipments.id"), index=True)
    rule_id: Mapped[str] = mapped_column(ForeignKey("compliance_rules.id"))
    evaluation_id: Mapped[Optional[str]] = mapped_column(ForeignKey("compliance_evaluations.id"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(32), default=IssueStatus.OPEN.value)
    recommended_action: Mapped[Optional[str]] = mapped_column(Text)
    owner_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"))
    evidence_ids: Mapped[list] = mapped_column(JSON, default=list)
    risk_contribution: Mapped[int] = mapped_column(Integer, default=0)


class RiskAssessment(Base, TimestampMixin):
    __tablename__ = "risk_assessments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    shipment_id: Mapped[str] = mapped_column(ForeignKey("shipments.id"), index=True)
    score: Mapped[int] = mapped_column(Integer)
    previous_score: Mapped[Optional[int]] = mapped_column(Integer)
    level: Mapped[str] = mapped_column(String(16))
    reason: Mapped[str] = mapped_column(Text)
    factors: Mapped[list[RiskFactor]] = relationship(back_populates="assessment")


class RiskFactor(Base):
    __tablename__ = "risk_factors"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    assessment_id: Mapped[str] = mapped_column(ForeignKey("risk_assessments.id"), index=True)
    label: Mapped[str] = mapped_column(String(255))
    points: Mapped[int] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(String(64))
    assessment: Mapped[RiskAssessment] = relationship(back_populates="factors")


class AgentRun(Base, TimestampMixin):
    __tablename__ = "agent_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    shipment_id: Mapped[str] = mapped_column(ForeignKey("shipments.id"), index=True)
    trigger: Mapped[str] = mapped_column(String(64))
    decision: Mapped[str] = mapped_column(String(64))
    summary: Mapped[str] = mapped_column(Text)
    actions: Mapped[list[AgentAction]] = relationship(back_populates="run")


class AgentAction(Base, TimestampMixin):
    __tablename__ = "agent_actions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    run_id: Mapped[str] = mapped_column(ForeignKey("agent_runs.id"), index=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    shipment_id: Mapped[str] = mapped_column(ForeignKey("shipments.id"), index=True)
    action_type: Mapped[str] = mapped_column(String(64))
    detail: Mapped[str] = mapped_column(Text)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    approved: Mapped[Optional[bool]] = mapped_column(Boolean)
    run: Mapped[AgentRun] = relationship(back_populates="actions")


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    shipment_id: Mapped[Optional[str]] = mapped_column(ForeignKey("shipments.id"), index=True)
    issue_id: Mapped[Optional[str]] = mapped_column(ForeignKey("compliance_issues.id"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    assignee_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"))
    priority: Mapped[str] = mapped_column(String(16), default=TaskPriority.MEDIUM.value)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), default=TaskStatus.OPEN.value)
    created_by: Mapped[Optional[str]] = mapped_column(String(36))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    supplier_id: Mapped[Optional[str]] = mapped_column(ForeignKey("suppliers.id"))


class Review(Base, TimestampMixin):
    __tablename__ = "reviews"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    shipment_id: Mapped[str] = mapped_column(ForeignKey("shipments.id"), index=True)
    issue_id: Mapped[Optional[str]] = mapped_column(ForeignKey("compliance_issues.id"))
    reviewer_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    decision: Mapped[str] = mapped_column(String(32))
    comment: Mapped[Optional[str]] = mapped_column(Text)


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(String(64))
    shipment_id: Mapped[Optional[str]] = mapped_column(ForeignKey("shipments.id"))
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    channel: Mapped[str] = mapped_column(String(32), default="in_app")


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (Index("ix_audit_shipment", "organization_id", "shipment_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    actor_id: Mapped[Optional[str]] = mapped_column(String(36))
    actor_type: Mapped[str] = mapped_column(String(16), default=ActorType.SYSTEM.value)
    organization_id: Mapped[str] = mapped_column(String(36), index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    shipment_id: Mapped[Optional[str]] = mapped_column(String(36), index=True)
    entity_type: Mapped[Optional[str]] = mapped_column(String(64))
    entity_id: Mapped[Optional[str]] = mapped_column(String(36))
    description: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    previous_state: Mapped[Optional[str]] = mapped_column(Text)
    new_state: Mapped[Optional[str]] = mapped_column(Text)


class TraceabilityNode(Base, TimestampMixin):
    __tablename__ = "traceability_nodes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    shipment_id: Mapped[str] = mapped_column(ForeignKey("shipments.id"), index=True)
    label: Mapped[str] = mapped_column(String(255))
    kind: Mapped[str] = mapped_column(String(64))
    location: Mapped[Optional[str]] = mapped_column(String(255))
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    risk: Mapped[Optional[str]] = mapped_column(String(16))


class TraceabilityEdge(Base, TimestampMixin):
    __tablename__ = "traceability_edges"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    shipment_id: Mapped[str] = mapped_column(ForeignKey("shipments.id"), index=True)
    from_node_id: Mapped[str] = mapped_column(ForeignKey("traceability_nodes.id"))
    to_node_id: Mapped[str] = mapped_column(ForeignKey("traceability_nodes.id"))
    relationship: Mapped[str] = mapped_column(String(64))
    occurred_on: Mapped[Optional[datetime]] = mapped_column(Date)
    source: Mapped[Optional[str]] = mapped_column(String(255))
    evidence_id: Mapped[Optional[str]] = mapped_column(ForeignKey("evidence.id"))


class RegulatorySource(Base, TimestampMixin):
    __tablename__ = "regulatory_sources"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    title: Mapped[str] = mapped_column(String(255))
    jurisdiction: Mapped[str] = mapped_column(String(64))
    version: Mapped[str] = mapped_column(String(32))
    source_url: Mapped[Optional[str]] = mapped_column(String(512))
    demo: Mapped[bool] = mapped_column(Boolean, default=True)


class RegulatoryDocument(Base, TimestampMixin):
    __tablename__ = "regulatory_documents"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    source_id: Mapped[str] = mapped_column(ForeignKey("regulatory_sources.id"))
    title: Mapped[str] = mapped_column(String(255))
    effective_date: Mapped[Optional[datetime]] = mapped_column(Date)
    body: Mapped[str] = mapped_column(Text)


class RegulationChunk(Base, TimestampMixin):
    __tablename__ = "regulation_chunks"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    document_id: Mapped[str] = mapped_column(ForeignKey("regulatory_documents.id"))
    section: Mapped[str] = mapped_column(String(64))
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[Optional[list]] = mapped_column(JSON)


class ModelExecution(Base):
    __tablename__ = "model_executions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    organization_id: Mapped[Optional[str]] = mapped_column(String(36), index=True)
    shipment_id: Mapped[Optional[str]] = mapped_column(String(36), index=True)
    document_id: Mapped[Optional[str]] = mapped_column(String(36))
    provider: Mapped[str] = mapped_column(String(64))
    model: Mapped[str] = mapped_column(String(128))
    operation: Mapped[str] = mapped_column(String(64))
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer)
    token_usage: Mapped[Optional[int]] = mapped_column(Integer)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    validation_ok: Mapped[bool] = mapped_column(Boolean, default=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[Optional[str]] = mapped_column(Text)


class WorkflowEvent(Base):
    __tablename__ = "workflow_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    organization_id: Mapped[str] = mapped_column(String(36), index=True)
    shipment_id: Mapped[Optional[str]] = mapped_column(String(36), index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
