from __future__ import annotations

import io
import logging
from datetime import date, datetime, timedelta, timezone

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import write_audit
from app.compliance.engine import evaluate_rule, run_compliance
from app.core.config import get_settings
from app.core.db import Base, engine, SessionLocal
from app.core.security import hash_password
from app.documents.normalize import normalize_field
from app.documents.pipeline import file_hash
from app.documents.storage import get_storage
from app.models.entities import (
    AgentAction,
    AgentDecision,
    AgentRun,
    AuditEvent,
    ComplianceEvaluation,
    ComplianceIssue,
    ComplianceRule,
    Customer,
    DocumentExtraction,
    DocumentType,
    DocumentVersion,
    Evidence,
    IssueStatus,
    Notification,
    Organization,
    OrganizationMember,
    ProcessingStatus,
    RegulationChunk,
    RegulatoryDocument,
    RegulatorySource,
    Review,
    RiskAssessment,
    RiskFactor,
    Role,
    RoleName,
    RuleVersion,
    Severity,
    Shipment,
    ShipmentDocument,
    Supplier,
    Task,
    TaskPriority,
    TaskStatus,
    TraceabilityEdge,
    TraceabilityNode,
    User,
    uid,
)
from app.risk.engine import recalculate_risk

log = logging.getLogger(__name__)


def create_sample_pdf(title: str, lines: list[str]) -> bytes:
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 750, title)
    p.setFont("Helvetica", 10)
    p.drawString(50, 735, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    p.line(50, 725, 550, 725)
    
    y = 700
    p.setFont("Helvetica", 11)
    for line in lines:
        p.drawString(50, y, line)
        y -= 22
        if y < 50:
            p.showPage()
            y = 750
            p.setFont("Helvetica", 11)
    p.save()
    buffer.seek(0)
    return buffer.getvalue()


def _ensure_roles(db: Session) -> dict[str, Role]:
    existing = {r.name: r for r in db.scalars(select(Role)).all()}
    for role_enum in RoleName:
        if role_enum.value not in existing:
            role = Role(id=uid(), name=role_enum.value)
            db.add(role)
            existing[role_enum.value] = role
    db.flush()
    return existing


def seed_rules(db: Session, org_id: str) -> dict[str, ComplianceRule]:
    rule_definitions = [
        {
            "code": "RULE-001",
            "name": "Mandatory Trade Documentation Completeness",
            "description": "Verifies that all mandatory customs documents (Commercial Invoice, Packing List, Bill of Lading, Certificate of Origin) are submitted and present.",
            "severity": Severity.CRITICAL.value,
            "action": "Hold customs clearance and request missing documents from supplier or freight forwarder.",
            "source": "[STATUTORY REGULATORY MANDATE] WCO Revised Kyoto Convention & National Customs Regulations",
            "required_docs": ["commercial_invoice", "packing_list", "bill_of_lading", "certificate_of_origin"],
        },
        {
            "code": "RULE-002",
            "name": "Country of Origin Cross-Verification",
            "description": "Checks consistency between origin declared on the Commercial Invoice and the issuing country on the Certificate of Origin to prevent tariff fraud.",
            "severity": Severity.CRITICAL.value,
            "action": "Flag critical origin contradiction; halt clearance and demand authenticated issuing chamber verification.",
            "source": "[STATUTORY REGULATORY MANDATE] WTO Agreement on Rules of Origin, Article 4",
            "required_docs": ["commercial_invoice", "certificate_of_origin"],
        },
        {
            "code": "RULE-003",
            "name": "Quantity Reconciliation",
            "description": "Verifies that item quantities on the Commercial Invoice exactly match the packed quantities stated on the Packing List.",
            "severity": Severity.MEDIUM.value,
            "action": "Request revised packing declaration or amended commercial invoice.",
            "source": "[CONFIGURED ORGANIZATIONAL RULE] Enterprise Tolerance Policy: Unit Quantity Equivalence",
            "required_docs": ["commercial_invoice", "packing_list"],
        },
        {
            "code": "RULE-004",
            "name": "Gross Weight Reconciliation",
            "description": "Cross-references cargo gross weight on the Packing List against gross freight weight recorded on the Carrier Bill of Lading (tolerance <= 1kg).",
            "severity": Severity.MEDIUM.value,
            "action": "Request scale weight tickets and carrier tare adjustment confirmation.",
            "source": "[CONFIGURED ORGANIZATIONAL RULE] Enterprise Operational Tolerance: SOLAS Container Weight Margin (<=1kg)",
            "required_docs": ["packing_list", "bill_of_lading"],
        },
        {
            "code": "RULE-005",
            "name": "Certificate Validity & Expiry Verification",
            "description": "Ensures that Certificate of Origin, Product Conformity, and Health/Phyto certificates have not lapsed prior to entry date.",
            "severity": Severity.HIGH.value,
            "action": "Reject expired certificate and require expedited re-issuance from authorized testing laboratory or chamber.",
            "source": "[STATUTORY REGULATORY MANDATE] ISO/IEC 17025 Conformity Assessment & Trade Licensing Guidelines",
            "required_docs": ["certificate_of_origin", "product_certificate"],
        },
        {
            "code": "RULE-006",
            "name": "Harmonized System (HS) Code Presence",
            "description": "Verifies that Commercial Invoice clearly identifies the standardized 6-8 digit tariff classification code for all line items.",
            "severity": Severity.HIGH.value,
            "action": "Require supplier to provide verified tariff classification number.",
            "source": "[STATUTORY REGULATORY MANDATE] Harmonized Commodity Description and Coding System (WCO HS 2026)",
            "required_docs": ["commercial_invoice"],
        },
        {
            "code": "RULE-007",
            "name": "HS Tariff Code Digit Format Validation",
            "description": "Validates that extracted HS code adheres to international 4 to 10-digit numerical formatting standard.",
            "severity": Severity.LOW.value,
            "action": "Notify customs broker for HS classification precision correction.",
            "source": "[CONFIGURED ORGANIZATIONAL RULE] Enterprise Policy: Tariff Numerical Format Validation",
            "required_docs": ["commercial_invoice"],
        },
        {
            "code": "RULE-008",
            "name": "Regulated Goods Conformity Certificate Mandate",
            "description": "Demands technical product safety certificates (e.g. UN38.3 for Lithium batteries, CE/UL for electronics) for sensitive goods.",
            "severity": Severity.MEDIUM.value,
            "action": "Upload accredited laboratory test report or safety declaration.",
            "source": "[STATUTORY REGULATORY MANDATE] UN Manual of Tests and Criteria (UN 38.3) / IATA DGR",
            "required_docs": ["product_certificate"],
        },
        {
            "code": "RULE-009",
            "name": "Supplier Legal Entity Consistency",
            "description": "Cross-verifies exporter/seller legal registered business name across commercial invoice and official certificates.",
            "severity": Severity.HIGH.value,
            "action": "Confirm legal entity relationships or subsidiary trading authorizations.",
            "source": "[CONFIGURED ORGANIZATIONAL RULE] Enterprise Compliance Policy: Legal Entity Cross-Verification",
            "required_docs": ["commercial_invoice", "certificate_of_origin"],
        },
        {
            "code": "RULE-010",
            "name": "Chronological Invoice & Transit Timeline Check",
            "description": "Ensures invoice issue date precedes or aligns with vessel departure and arrival schedule.",
            "severity": Severity.LOW.value,
            "action": "Clarify bill date sequence discrepancies.",
            "source": "[CONFIGURED ORGANIZATIONAL RULE] Enterprise Logistics Heuristic: Chronological Timeline Validation",
            "required_docs": ["commercial_invoice"],
        },

    ]

    rules: dict[str, ComplianceRule] = {}
    for rdef in rule_definitions:
        existing = db.scalars(select(ComplianceRule).where(ComplianceRule.rule_code == rdef["code"])).first()
        if not existing:
            rule = ComplianceRule(
                id=uid(),
                organization_id=org_id,
                rule_code=rdef["code"],
                name=rdef["name"],
                description=rdef["description"],
                jurisdiction="GLOBAL",
                severity=rdef["severity"],
                required_documents=rdef["required_docs"],
                action=rdef["action"],
                source=rdef["source"],
                enabled=True,
            )
            db.add(rule)
            db.flush()
            version = RuleVersion(
                id=uid(),
                rule_id=rule.id,
                version=1,
                conditions={"active": True, "strict_mode": True},
                effective_from=date(2026, 1, 1),
            )
            db.add(version)
            rules[rdef["code"]] = rule
        else:
            rules[rdef["code"]] = existing

    db.flush()
    return rules


def seed_regulatory_rag(db: Session) -> None:
    sources = [
        {
            "title": "EU Battery & Critical Mineral Harmonized Regulation 2026",
            "jurisdiction": "EU",
            "version": "2026.1",
            "url": "https://eur-lex.europa.eu/battery-regs-2026",
            "sections": [
                ("Article 12 - Origin Traceability", "All imported industrial lithium-ion energy storage systems and components entering European Union ports must provide unequivocal proof of origin verified by an accredited chamber of commerce in the manufacturing nation. Discrepancies between invoice origin and declaration mandate customs retention."),
                ("Article 19 - Dangerous Goods Conformity", "Mandatory submission of UN 38.3 lithium battery test summary and active hazardous materials carriage declaration. Certificates older than 24 months from test date are void."),
            ]
        },
        {
            "title": "US CBP Customs Modernization & Tariff Enforcement Act",
            "jurisdiction": "US",
            "version": "US-CBP-2026",
            "url": "https://www.cbp.gov/trade/compliance-guidance",
            "sections": [
                ("Section 404 - Documented Reconciliation", "Importers of record must reconcile commercial invoices, scale weight tickets, and ocean bills of lading. Weight variances exceeding 0.5% require supplemental manifest disclosures prior to cargo release."),
                ("Section 811 - Transshipment Origin Integrity", "Cargo claiming origin preferences must document chain of custody across all transshipment hubs. Conflicting certificates of origin trigger immediate Level 3 border examination."),
            ]
        },
        {
            "title": "India CBIC Electronic Customs Clearance & Port Safety Code",
            "jurisdiction": "IN",
            "version": "CBIC-2026-NSICT",
            "url": "https://www.cbic.gov.in/trade-regulations",
            "sections": [
                ("Regulation 7 - Nhava Sheva Inbound Inspection", "All containerized sea freight arriving at Nhava Sheva (JNPT) must present matching commercial invoice, packing declaration, and bill of lading prior to bill of entry assessment. Discrepant origin certificates will block customs assessment status to BLOCKED."),
                ("Regulation 14 - HS Code Classification", "Every invoice line item must state valid 6-digit WCO tariff heading. Generic classifications without tariff numbers will result in automated system rejection."),
            ]
        }
    ]

    for sdef in sources:
        existing = db.scalars(select(RegulatorySource).where(RegulatorySource.title == sdef["title"])).first()
        if not existing:
            source = RegulatorySource(
                id=uid(),
                title=sdef["title"],
                jurisdiction=sdef["jurisdiction"],
                version=sdef["version"],
                source_url=sdef["url"],
                demo=True,
            )
            db.add(source)
            db.flush()

            doc = RegulatoryDocument(
                id=uid(),
                source_id=source.id,
                title=sdef["title"] + " - Primary Digest",
                effective_date=date(2026, 1, 1),
                body="Complete regulatory compliance directive text.",
            )
            db.add(doc)
            db.flush()

            for sec_title, sec_text in sdef["sections"]:
                chunk = RegulationChunk(
                    id=uid(),
                    document_id=doc.id,
                    section=sec_title,
                    text=sec_text,
                    embedding=None,
                )
                db.add(chunk)
    db.flush()


def run_seed(db: Session) -> None:
    settings = get_settings()
    storage = get_storage()

    # 1. Roles
    roles = _ensure_roles(db)

    # 2. Organization
    org = db.scalars(select(Organization).where(Organization.name == settings.demo_org_name)).first()
    if not org:
        org = Organization(id=uid(), name=settings.demo_org_name)
        db.add(org)
        db.flush()

    # 3. Users
    admin_user = db.scalars(select(User).where(User.email == settings.demo_admin_email.lower())).first()
    if not admin_user:
        admin_user = User(
            id=uid(),
            email=settings.demo_admin_email.lower(),
            full_name="Elena Vance (Chief Compliance Officer)",
            hashed_password=hash_password(settings.demo_admin_password),
            is_active=True,
        )
        db.add(admin_user)
        db.flush()
        db.add(OrganizationMember(
            id=uid(),
            organization_id=org.id,
            user_id=admin_user.id,
            role_id=roles[RoleName.ADMIN.value].id,
        ))

    reviewer_user = db.scalars(select(User).where(User.email == "reviewer@auditflow.demo")).first()
    if not reviewer_user:
        reviewer_user = User(
            id=uid(),
            email="reviewer@auditflow.demo",
            full_name="Marcus Chen (Senior Trade Auditor)",
            hashed_password=hash_password(settings.demo_admin_password),
            is_active=True,
        )
        db.add(reviewer_user)
        db.flush()
        db.add(OrganizationMember(
            id=uid(),
            organization_id=org.id,
            user_id=reviewer_user.id,
            role_id=roles[RoleName.REVIEWER.value].id,
        ))

    db.flush()

    # 4. Rules & Regulatory Knowledge Base
    rules = seed_rules(db, org.id)
    seed_regulatory_rag(db)

    # 5. Suppliers & Customers
    suppliers = {
        "acme": Supplier(id=uid(), organization_id=org.id, name="Acme Industrial Supplies GmbH", country="DE", risk_note="Tier-1 German industrial components exporter. Clean track record."),
        "apex": Supplier(id=uid(), organization_id=org.id, name="Apex Precision Machinery Co", country="JP", risk_note="AEO certified Japanese high-precision parts manufacturer."),
        "nordic": Supplier(id=uid(), organization_id=org.id, name="Nordic Chemical Innovations", country="BE", risk_note="Specialty chemicals and laboratory solvent supplier."),
        "solar": Supplier(id=uid(), organization_id=org.id, name="Shanghai Micro-Optics Corp", country="CN", risk_note="Photovoltaic and optical components producer."),
    }
    for s in suppliers.values():
        if not db.scalars(select(Supplier).where(Supplier.name == s.name, Supplier.organization_id == org.id)).first():
            db.add(s)

    customers = {
        "meridian": Customer(id=uid(), organization_id=org.id, name="Meridian Imports Pvt Ltd", country="IN"),
        "eurologix": Customer(id=uid(), organization_id=org.id, name="EuroLogix Distribution BV", country="NL"),
        "atlantic": Customer(id=uid(), organization_id=org.id, name="Atlantic BioPharma Inc", country="US"),
        "helios": Customer(id=uid(), organization_id=org.id, name="Helios Clean Energy LLC", country="US"),
    }
    for c in customers.values():
        if not db.scalars(select(Customer).where(Customer.name == c.name, Customer.organization_id == org.id)).first():
            db.add(c)
    db.flush()

    # Refresh pointers
    supp_acme = db.scalars(select(Supplier).where(Supplier.name == suppliers["acme"].name)).first()
    supp_apex = db.scalars(select(Supplier).where(Supplier.name == suppliers["apex"].name)).first()
    supp_nordic = db.scalars(select(Supplier).where(Supplier.name == suppliers["nordic"].name)).first()
    supp_solar = db.scalars(select(Supplier).where(Supplier.name == suppliers["solar"].name)).first()

    cust_meridian = db.scalars(select(Customer).where(Customer.name == customers["meridian"].name)).first()
    cust_eurologix = db.scalars(select(Customer).where(Customer.name == customers["eurologix"].name)).first()
    cust_atlantic = db.scalars(select(Customer).where(Customer.name == customers["atlantic"].name)).first()
    cust_helios = db.scalars(select(Customer).where(Customer.name == customers["helios"].name)).first()

    # =========================================================================
    # SHIPMENT 1: HERO DEMO SCENARIO (SHP-2026-0842) - Has Critical Conflict
    # Origin: DE (Hamburg) -> Destination: IN (Nhava Sheva)
    # Contradiction: Invoice says Germany, but Certificate of Origin says Vietnam!
    # Packing list quantity (950) vs Invoice (1000)
    # =========================================================================
    s1 = db.scalars(select(Shipment).where(Shipment.reference_number == "SHP-2026-0842")).first()
    if not s1:
        s1 = Shipment(
            id=uid(),
            organization_id=org.id,
            reference_number="SHP-2026-0842",
            origin_country="DE",
            destination_country="IN",
            origin_port="Port of Hamburg",
            destination_port="Nhava Sheva (JNPT), Mumbai",
            shipment_date=date.today() - timedelta(days=12),
            estimated_arrival=date.today() + timedelta(days=6),
            carrier="Maersk Line (Vessel: Nordic Star)",
            supplier_id=supp_acme.id if supp_acme else None,
            customer_id=cust_meridian.id if cust_meridian else None,
            status="in_transit",
            compliance_status="BLOCKED",
            risk_score=85,
            risk_level="CRITICAL",
            document_completeness=100.0,
            under_review=False,
        )
        db.add(s1)
        db.flush()

        # Generate sample document files and records
        docs_to_create = [
            (
                "commercial_invoice",
                "invoice_INV-2048.pdf",
                "COMMERCIAL INVOICE #INV-2048",
                [
                    "Seller / Exporter: Acme Industrial Supplies GmbH, Stuttgart, Germany",
                    "Buyer / Consignee: Meridian Imports Pvt Ltd, Mumbai, India",
                    "Invoice Date: 2026-08-01",
                    "Country of Origin: Germany",
                    "HS Tariff Code: 8507.60 (Lithium-ion accumulators)",
                    "Description: Industrial Lithium-Ion Battery Storage Modules Model XL-400",
                    "Quantity: 1000 Units",
                    "Unit Price: 120.00 EUR",
                    "Total Invoice Value: 120,000.00 EUR (Incoterms: CIF Nhava Sheva)",
                    "Payment Terms: Irrevocable Letter of Credit at Sight",
                ],
                [
                    ("invoice_number", "INV-2048"),
                    ("invoice_date", "2026-08-01"),
                    ("seller", "Acme Industrial Supplies"),
                    ("buyer", "Meridian Imports Pvt Ltd"),
                    ("product_description", "Lithium-ion battery packs"),
                    ("hs_code", "8507.60"),
                    ("quantity", "1000"),
                    ("unit_price", "120"),
                    ("total_value", "120000"),
                    ("currency", "EUR"),
                    ("country_of_origin", "Germany"),
                ]
            ),
            (
                "packing_list",
                "packing_list_PL-2048.pdf",
                "OCEAN FREIGHT PACKING LIST #PL-2048",
                [
                    "Shipper: Acme Industrial Supplies GmbH",
                    "Consignee: Meridian Imports Pvt Ltd",
                    "Invoice Reference: INV-2048",
                    "Container: MSKU1234567 (40ft High Cube)",
                    "Package Count: 40 Wooden Crates",
                    "Packed Quantity: 950 Units",
                    "Gross Weight: 12500 kg",
                    "Net Weight: 11800 kg",
                    "Dimensions: 40 x 20 x 20 ft",
                ],
                [
                    ("packing_list_number", "PL-2048"),
                    ("package_count", "40"),
                    ("quantity", "950"),
                    ("product_description", "Lithium-ion battery packs"),
                    ("gross_weight", "12500 kg"),
                    ("net_weight", "11800 kg"),
                ]
            ),
            (
                "bill_of_lading",
                "bill_of_lading_MAEU2048HAM.pdf",
                "OCEAN BILL OF LADING #MAEU2048HAM",
                [
                    "Carrier: Maersk Line A/S",
                    "Vessel & Voyage: Nordic Star / 402E",
                    "Shipper: Acme Industrial Supplies GmbH",
                    "Consignee: Meridian Imports Pvt Ltd",
                    "Port of Loading: Hamburg, Germany (DEHAM)",
                    "Port of Discharge: Nhava Sheva, India (INNSA)",
                    "Container No: MSKU1234567 / Seal No: 998124",
                    "Declared Cargo Weight: 12500 kg",
                    "Description: 40 Crates Lithium-ion Battery Packs UN 3480 Class 9",
                    "Freight: Prepaid",
                ],
                [
                    ("bl_number", "MAEU2048HAM"),
                    ("shipper", "Acme Industrial Supplies"),
                    ("consignee", "Meridian Imports Pvt Ltd"),
                    ("carrier", "Maersk"),
                    ("origin_port", "Hamburg"),
                    ("destination_port", "Nhava Sheva"),
                    ("weight", "12500 kg"),
                ]
            ),
            (
                "certificate_of_origin",
                "certificate_of_origin_COO-VN-8891.pdf",
                "CERTIFICATE OF ORIGIN #COO-VN-8891",
                [
                    "Issuing Authority: Vietnam Chamber of Commerce and Industry (VCCI)",
                    "Exporter: Acme Industrial Supplies GmbH (Hanoi Liaison)",
                    "Importer: Meridian Imports Pvt Ltd",
                    "Goods: Lithium-ion battery packs Model XL-400",
                    "Certified Country of Origin: Vietnam",
                    "Issue Date: 2026-07-28",
                    "Expiry Date: 2027-07-28",
                    "Declaration: Goods declared above satisfy origin criteria under Chapter 4.",
                ],
                [
                    ("certificate_number", "COO-VN-8891"),
                    ("exporter", "Acme Industrial Supplies"),
                    ("importer", "Meridian Imports Pvt Ltd"),
                    ("country_of_origin", "Vietnam"),
                    ("issue_date", "2026-07-28"),
                    ("expiry_date", "2027-07-28"),
                ]
            ),
            (
                "product_certificate",
                "product_certificate_UN383.pdf",
                "UN 38.3 LITHIUM BATTERY TRANSPORT TEST SUMMARY",
                [
                    "Testing Body: TÜV Rheinland Industrial Services",
                    "Report Number: TR-2024-BATT-9912",
                    "Product: Rechargeable Lithium-ion Cells Model XL-400",
                    "Standard: UN Manual of Tests and Criteria Part III, Subsection 38.3",
                    "Issue Date: 2024-03-15",
                    "Expiry Date: 2027-03-15",
                    "Status: FULLY COMPLIANT & CERTIFIED",
                ],
                [
                    ("certificate_number", "TR-2024-BATT-9912"),
                    ("issuer", "TÜV Rheinland"),
                    ("status", "valid"),
                    ("issue_date", "2024-03-15"),
                    ("expiry_date", "2027-03-15"),
                ]
            ),
        ]

        stored_evidence_ids = []
        for doc_type, filename, pdf_title, pdf_lines, fields in docs_to_create:
            pdf_data = create_sample_pdf(pdf_title, pdf_lines)
            digest = file_hash(pdf_data)
            
            doc_rec = ShipmentDocument(
                id=uid(),
                organization_id=org.id,
                shipment_id=s1.id,
                name=filename,
                document_type=doc_type,
                file_hash=digest,
                current_version=1,
                processing_status=ProcessingStatus.COMPLETED.value,
                uploaded_by=admin_user.id,
            )
            db.add(doc_rec)
            db.flush()

            storage_key = f"{org.id}/{s1.id}/{doc_rec.id}/v1-{digest[:10]}"
            storage.put(storage_key, pdf_data, "application/pdf")

            ver_rec = DocumentVersion(
                id=uid(),
                organization_id=org.id,
                document_id=doc_rec.id,
                version=1,
                storage_key=storage_key,
                file_hash=digest,
                mime_type="application/pdf",
                uploaded_by=admin_user.id,
                processing_status=ProcessingStatus.COMPLETED.value,
                confidence=0.98,
            )
            db.add(ver_rec)
            db.flush()

            for f_name, f_raw in fields:
                norm_val, method = normalize_field(f_name, f_raw)
                ev = Evidence(
                    id=uid(),
                    organization_id=org.id,
                    shipment_id=s1.id,
                    document_id=doc_rec.id,
                    document_version_id=ver_rec.id,
                    field=f_name,
                    raw_value=f_raw,
                    normalized_value=norm_val,
                    normalization_method=method,
                    page=1,
                    confidence=0.96,
                    extraction_method="mock",
                    document_name=filename,
                )
                db.add(ev)
                db.flush()
                stored_evidence_ids.append(ev.id)

        # Run compliance rules on s1
        run_compliance(db, s1)
        recalculate_risk(db, s1)

        # Create Agent run
        agent_run = AgentRun(
            id=uid(),
            organization_id=org.id,
            shipment_id=s1.id,
            trigger="DOCUMENT_PROCESSED",
            decision=AgentDecision.REQUEST_CORRECTION.value,
            summary="Autonomous Analysis: Critical origin mismatch detected between Commercial Invoice (Germany) and Certificate of Origin (Vietnam). Automated supplier correction task generated.",
        )
        db.add(agent_run)
        db.flush()

        db.add(AgentAction(
            id=uid(),
            run_id=agent_run.id,
            organization_id=org.id,
            shipment_id=s1.id,
            action_type="REQUEST_CORRECTION",
            detail="Dispatched formal origin declaration reconciliation request to Acme Industrial Supplies GmbH.",
            requires_approval=False,
        ))

        # Create Open Task for Supplier
        issue_orig = db.scalars(
            select(ComplianceIssue).where(ComplianceIssue.shipment_id == s1.id, ComplianceIssue.severity == "CRITICAL")
        ).first()

        db.add(Task(
            id=uid(),
            organization_id=org.id,
            shipment_id=s1.id,
            issue_id=issue_orig.id if issue_orig else None,
            title="Request Corrected Certificate of Origin (German IHK Chamber)",
            description="Commercial Invoice INV-2048 specifies origin as Germany, but uploaded Certificate of Origin COO-VN-8891 states Vietnam. Obtain authentic German chamber certificate.",
            priority=TaskPriority.CRITICAL.value,
            due_date=datetime.now(timezone.utc) + timedelta(days=2),
            status=TaskStatus.WAITING_FOR_SUPPLIER.value,
            created_by="agent",
            supplier_id=supp_acme.id if supp_acme else None,
        ))

        # Create Notification
        db.add(Notification(
            id=uid(),
            organization_id=org.id,
            user_id=admin_user.id,
            title="CRITICAL COMPLIANCE BLOCK: SHP-2026-0842",
            body="Origin conflict detected. Commercial Invoice (Germany) contradicts Certificate of Origin (Vietnam). Shipment flagged as BLOCKED.",
            kind="critical_issue",
            shipment_id=s1.id,
        ))

        # Traceability Graph for s1
        n1 = TraceabilityNode(id=uid(), organization_id=org.id, shipment_id=s1.id, label="Acme Manufacturing Gigafactory", kind="factory", location="Stuttgart, Germany", details={"facility_id": "DE-STU-04", "iso_9001": "Certified"}, risk="LOW")
        n2 = TraceabilityNode(id=uid(), organization_id=org.id, shipment_id=s1.id, label="Burchardkai Container Terminal", kind="port_of_loading", location="Port of Hamburg, Germany", details={"terminal": "CTB Berth 3", "gate_in": "2026-08-04"}, risk="LOW")
        n3 = TraceabilityNode(id=uid(), organization_id=org.id, shipment_id=s1.id, label="Nordic Star Ocean Transit", kind="vessel", location="Suez Canal / Red Sea Route", details={"vessel_imo": "9812401", "teu": "14500"}, risk="MEDIUM")
        n4 = TraceabilityNode(id=uid(), organization_id=org.id, shipment_id=s1.id, label="Nhava Sheva Port (JNPT)", kind="port_of_discharge", location="Mumbai, India", details={"customs_station": "INNSA1", "clearance_lane": "Red Channel Hold"}, risk="CRITICAL")
        n5 = TraceabilityNode(id=uid(), organization_id=org.id, shipment_id=s1.id, label="Meridian Central Logistics Depot", kind="warehouse", location="Bhiwandi, Maharashtra", details={"wh_code": "IN-BHW-01"}, risk="LOW")
        db.add_all([n1, n2, n3, n4, n5])
        db.flush()

        db.add(TraceabilityEdge(id=uid(), organization_id=org.id, shipment_id=s1.id, from_node_id=n1.id, to_node_id=n2.id, relationship="ROAD_TRANSPORT", occurred_on=date.today() - timedelta(days=14), source="Consignment Note CMR-881"))
        db.add(TraceabilityEdge(id=uid(), organization_id=org.id, shipment_id=s1.id, from_node_id=n2.id, to_node_id=n3.id, relationship="VESSEL_LOAD", occurred_on=date.today() - timedelta(days=12), source="Bill of Lading MAEU2048HAM"))
        db.add(TraceabilityEdge(id=uid(), organization_id=org.id, shipment_id=s1.id, from_node_id=n3.id, to_node_id=n4.id, relationship="OCEAN_PASSAGE", occurred_on=date.today() + timedelta(days=6), source="Imported Manifest Route (Simulated)"))
        db.add(TraceabilityEdge(id=uid(), organization_id=org.id, shipment_id=s1.id, from_node_id=n4.id, to_node_id=n5.id, relationship="CUSTOMS_CLEARANCE_DISPATCH", occurred_on=None, source="Projected Routing"))

        # Seed audit trail entries
        write_audit(db, organization_id=org.id, event_type="shipment_created", description="Shipment SHP-2026-0842 registered", shipment_id=s1.id, actor_id=admin_user.id, actor_type="user")
        write_audit(db, organization_id=org.id, event_type="document_uploaded", description="Uploaded commercial invoice and trade declarations", shipment_id=s1.id, actor_id=admin_user.id, actor_type="user")
        write_audit(db, organization_id=org.id, event_type="compliance_evaluated", description="Automated rule checks executed against trade evidence", shipment_id=s1.id, actor_type="system")

    # =========================================================================
    # SHIPMENT 2: READY FOR REVIEW (SHP-2026-0915)
    # Tokyo to Rotterdam - Clean, high completeness, low risk
    # =========================================================================
    s2 = db.scalars(select(Shipment).where(Shipment.reference_number == "SHP-2026-0915")).first()
    if not s2:
        s2 = Shipment(
            id=uid(),
            organization_id=org.id,
            reference_number="SHP-2026-0915",
            origin_country="JP",
            destination_country="NL",
            origin_port="Port of Yokohama, Japan",
            destination_port="Port of Rotterdam, Netherlands",
            shipment_date=date.today() - timedelta(days=8),
            estimated_arrival=date.today() + timedelta(days=18),
            carrier="ONE (Ocean Network Express)",
            supplier_id=supp_apex.id if supp_apex else None,
            customer_id=cust_eurologix.id if cust_eurologix else None,
            status="in_transit",
            compliance_status="READY_FOR_REVIEW",
            risk_score=8,
            risk_level="LOW",
            document_completeness=100.0,
            under_review=False,
        )
        db.add(s2)
        db.flush()

        pdf_inv = create_sample_pdf("COMMERCIAL INVOICE #APX-9150", [
            "Seller: Apex Precision Machinery Co, Tokyo, Japan",
            "Buyer: EuroLogix Distribution BV, Rotterdam, Netherlands",
            "Country of Origin: Japan",
            "HS Code: 8466.93",
            "Product: High Speed CNC Tooling Spindles",
            "Quantity: 250 Units",
            "Total Value: 85,000 EUR",
        ])
        dig_inv = file_hash(pdf_inv)
        d_rec = ShipmentDocument(
            id=uid(),
            organization_id=org.id,
            shipment_id=s2.id,
            name="invoice_APX-9150.pdf",
            document_type="commercial_invoice",
            file_hash=dig_inv,
            current_version=1,
            processing_status="completed",
        )
        db.add(d_rec)
        db.flush()
        key = f"{org.id}/{s2.id}/{d_rec.id}/v1-{dig_inv[:10]}"
        storage.put(key, pdf_inv, "application/pdf")
        v_rec = DocumentVersion(
            id=uid(),
            organization_id=org.id,
            document_id=d_rec.id,
            version=1,
            storage_key=key,
            file_hash=dig_inv,
            processing_status="completed",
            confidence=0.99,
        )
        db.add(v_rec)
        db.flush()

        # Evidence
        for fn, fv in [("country_of_origin", "Japan"), ("quantity", "250"), ("hs_code", "8466.93"), ("seller", "Apex Precision Machinery")]:
            nv, met = normalize_field(fn, fv)
            db.add(Evidence(
                id=uid(), organization_id=org.id, shipment_id=s2.id, document_id=d_rec.id,
                document_version_id=v_rec.id, field=fn, raw_value=fv, normalized_value=nv,
                normalization_method=met, confidence=0.98, extraction_method="mock", document_name=d_rec.name
            ))

        # Recalculate risk
        recalculate_risk(db, s2)
        write_audit(db, organization_id=org.id, event_type="shipment_created", description="Shipment SHP-2026-0915 created", shipment_id=s2.id, actor_type="system")

    # =========================================================================
    # SHIPMENT 3: WARNING (SHP-2026-0771)
    # Belgium to New York - Non-critical certificate expiry warning
    # =========================================================================
    s3 = db.scalars(select(Shipment).where(Shipment.reference_number == "SHP-2026-0771")).first()
    if not s3:
        s3 = Shipment(
            id=uid(),
            organization_id=org.id,
            reference_number="SHP-2026-0771",
            origin_country="BE",
            destination_country="US",
            origin_port="Port of Antwerp, Belgium",
            destination_port="Port of New York / New Jersey, USA",
            shipment_date=date.today() - timedelta(days=5),
            estimated_arrival=date.today() + timedelta(days=9),
            carrier="Hapag-Lloyd AG",
            supplier_id=supp_nordic.id if supp_nordic else None,
            customer_id=cust_atlantic.id if cust_atlantic else None,
            status="in_transit",
            compliance_status="WARNING",
            risk_score=35,
            risk_level="MEDIUM",
            document_completeness=80.0,
            under_review=False,
        )
        db.add(s3)
        db.flush()

        pdf_doc = create_sample_pdf("COMMERCIAL INVOICE #NC-7718", [
            "Seller: Nordic Chemical Innovations, Antwerp, Belgium",
            "Buyer: Atlantic BioPharma Inc, New York, USA",
            "Product: High-Purity Chromatography Solvents",
            "Country of Origin: Belgium",
            "HS Code: 2905.11",
            "Quantity: 500 Liters",
        ])
        dig = file_hash(pdf_doc)
        d_rec3 = ShipmentDocument(id=uid(), organization_id=org.id, shipment_id=s3.id, name="invoice_NC-7718.pdf", document_type="commercial_invoice", file_hash=dig, current_version=1, processing_status="completed")
        db.add(d_rec3)
        db.flush()
        key3 = f"{org.id}/{s3.id}/{d_rec3.id}/v1-{dig[:10]}"
        storage.put(key3, pdf_doc, "application/pdf")
        v3 = DocumentVersion(id=uid(), organization_id=org.id, document_id=d_rec3.id, version=1, storage_key=key3, file_hash=dig, processing_status="completed", confidence=0.97)
        db.add(v3)
        db.flush()

        # Add warning issue
        r5 = rules.get("RULE-005")
        if r5:
            db.add(ComplianceIssue(
                id=uid(),
                organization_id=org.id,
                shipment_id=s3.id,
                rule_id=r5.id,
                title="Conformity Certificate Expiration Warning",
                description="Laboratory analytical grade certificate PC-EXP-110 expires within 14 days of port arrival.",
                severity=Severity.HIGH.value,
                status=IssueStatus.OPEN.value,
                recommended_action="Contact Nordic Chemical for renewed certificate of analysis batch report.",
                risk_contribution=20,
            ))

        recalculate_risk(db, s3)

    # =========================================================================
    # SHIPMENT 4: CLEARED (SHP-2026-0620)
    # Shanghai to Long Beach - Fully audited and human-cleared
    # =========================================================================
    s4 = db.scalars(select(Shipment).where(Shipment.reference_number == "SHP-2026-0620")).first()
    if not s4:
        s4 = Shipment(
            id=uid(),
            organization_id=org.id,
            reference_number="SHP-2026-0620",
            origin_country="CN",
            destination_country="US",
            origin_port="Port of Shanghai, China",
            destination_port="Port of Long Beach, California, USA",
            shipment_date=date.today() - timedelta(days=22),
            estimated_arrival=date.today() - timedelta(days=2),
            carrier="COSCO Shipping",
            supplier_id=supp_solar.id if supp_solar else None,
            customer_id=cust_helios.id if cust_helios else None,
            status="delivered",
            compliance_status="CLEARED",
            risk_score=0,
            risk_level="LOW",
            document_completeness=100.0,
            under_review=False,
        )
        db.add(s4)
        db.flush()

        db.add(Review(
            id=uid(),
            organization_id=org.id,
            shipment_id=s4.id,
            reviewer_id=admin_user.id,
            decision="approve",
            comment="All trade documentation, origin certificates, and customs declarations verified against US CBP solar import quota guidelines. Fully cleared for domestic delivery.",
        ))

        write_audit(db, organization_id=org.id, event_type="human_reviewed", description="Shipment review: approve", shipment_id=s4.id, actor_id=admin_user.id, actor_type="user", previous_state="READY_FOR_REVIEW", new_state="CLEARED")

    db.commit()
    log.info("AuditFlow AI Seed successfully executed!")


def main():
    log.info("Initializing DB and running seed script...")
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        run_seed(db)
    print("✓ AuditFlow AI Database seeded successfully with demo organization, users, rules, and shipments!")


if __name__ == "__main__":
    main()
