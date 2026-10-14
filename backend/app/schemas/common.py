from __future__ import annotations
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str
    organization_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    organization_id: str
    organization_name: str
    role: str
    is_demo: bool = False


class ShipmentCreate(BaseModel):
    reference_number: str
    origin_country: str | None = None
    destination_country: str | None = None
    origin_port: str | None = None
    destination_port: str | None = None
    shipment_date: date | None = None
    estimated_arrival: date | None = None
    carrier: str | None = None
    supplier_id: str | None = None
    customer_id: str | None = None


class ShipmentUpdate(BaseModel):
    origin_country: str | None = None
    destination_country: str | None = None
    origin_port: str | None = None
    destination_port: str | None = None
    shipment_date: date | None = None
    estimated_arrival: date | None = None
    carrier: str | None = None
    status: str | None = None


class ShipmentOut(BaseModel):
    id: str
    reference_number: str
    origin_country: str | None
    destination_country: str | None
    origin_port: str | None
    destination_port: str | None
    shipment_date: date | None
    estimated_arrival: date | None
    carrier: str | None
    status: str
    compliance_status: str
    risk_score: int
    risk_level: str
    document_completeness: float
    supplier_name: str | None = None
    customer_name: str | None = None
    created_at: datetime | None = None


class IssueOut(BaseModel):
    id: str
    title: str
    description: str
    severity: str
    status: str
    recommended_action: str | None
    risk_contribution: int
    evidence_ids: list
    rule_id: str
    shipment_id: str
    created_at: datetime | None = None


class EvidenceOut(BaseModel):
    id: str
    field: str
    raw_value: str | None
    normalized_value: str | None
    document_id: str
    document_version_id: str
    document_name: str | None
    page: int | None
    confidence: float | None
    extraction_method: str
    normalization_method: str | None


class TaskCreate(BaseModel):
    title: str
    description: str
    shipment_id: str | None = None
    issue_id: str | None = None
    priority: str = "MEDIUM"
    assignee_id: str | None = None


class TaskUpdate(BaseModel):
    status: str | None = None
    assignee_id: str | None = None
    description: str | None = None


class ReviewRequest(BaseModel):
    decision: str
    comment: str | None = None
    issue_id: str | None = None


class MessageOut(BaseModel):
    detail: str
