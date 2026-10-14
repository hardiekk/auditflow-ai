from __future__ import annotations

from app.ai.provider import AIProvider, ClassificationResult, ExtractedField, ExtractionResult, ExplanationResult
from app.models.entities import DocumentType

TYPE_BY_KEYWORD = [
    ("invoice", DocumentType.COMMERCIAL_INVOICE.value),
    ("packing", DocumentType.PACKING_LIST.value),
    ("bill_of_lading", DocumentType.BILL_OF_LADING.value),
    ("bl_", DocumentType.BILL_OF_LADING.value),
    ("certificate_of_origin", DocumentType.CERTIFICATE_OF_ORIGIN.value),
    ("coo", DocumentType.CERTIFICATE_OF_ORIGIN.value),
    ("origin", DocumentType.CERTIFICATE_OF_ORIGIN.value),
    ("insurance", DocumentType.INSURANCE_CERTIFICATE.value),
    ("product_cert", DocumentType.PRODUCT_CERTIFICATE.value),
    ("product certificate", DocumentType.PRODUCT_CERTIFICATE.value),
    ("declaration", DocumentType.SUPPLIER_DECLARATION.value),
]


def _filename_type(filename: str) -> str:
    lower = filename.lower()
    for key, dtype in TYPE_BY_KEYWORD:
        if key in lower:
            return dtype
    return DocumentType.OTHER.value


HERO_FIELDS = {
    "commercial_invoice": [
        ExtractedField(field="invoice_number", raw_value="INV-2048", page=1, confidence=0.99),
        ExtractedField(field="invoice_date", raw_value="2026-08-01", page=1, confidence=0.98),
        ExtractedField(field="seller", raw_value="Acme Industrial Supplies", page=1, confidence=0.97),
        ExtractedField(field="buyer", raw_value="Meridian Imports Pvt Ltd", page=1, confidence=0.97),
        ExtractedField(field="product_description", raw_value="Lithium-ion battery packs", page=1, confidence=0.95),
        ExtractedField(field="hs_code", raw_value="8507.60", page=1, confidence=0.93),
        ExtractedField(field="quantity", raw_value="1000", page=1, confidence=0.99),
        ExtractedField(field="unit_price", raw_value="120", page=1, confidence=0.96),
        ExtractedField(field="total_value", raw_value="120000", page=1, confidence=0.96),
        ExtractedField(field="currency", raw_value="EUR", page=1, confidence=0.99),
        ExtractedField(field="country_of_origin", raw_value="Germany", page=1, confidence=0.98),
        ExtractedField(field="incoterms", raw_value="CIF Mumbai", page=1, confidence=0.9),
    ],
    "packing_list": [
        ExtractedField(field="packing_list_number", raw_value="PL-2048", page=1, confidence=0.98),
        ExtractedField(field="package_count", raw_value="40", page=1, confidence=0.95),
        ExtractedField(field="quantity", raw_value="950", page=1, confidence=0.97),
        ExtractedField(field="product_description", raw_value="Lithium-ion battery packs", page=1, confidence=0.94),
        ExtractedField(field="gross_weight", raw_value="12500 kg", page=1, confidence=0.96),
        ExtractedField(field="net_weight", raw_value="11800 kg", page=1, confidence=0.96),
        ExtractedField(field="dimensions", raw_value="40x20x20 ft", page=1, confidence=0.9),
    ],
    "bill_of_lading": [
        ExtractedField(field="bl_number", raw_value="MAEU2048HAM", page=1, confidence=0.99),
        ExtractedField(field="shipper", raw_value="Acme Industrial Supplies", page=1, confidence=0.95),
        ExtractedField(field="consignee", raw_value="Meridian Imports Pvt Ltd", page=1, confidence=0.95),
        ExtractedField(field="carrier", raw_value="Maersk", page=1, confidence=0.99),
        ExtractedField(field="vessel", raw_value="Nordic Star", page=1, confidence=0.92),
        ExtractedField(field="origin_port", raw_value="Hamburg", page=1, confidence=0.97),
        ExtractedField(field="destination_port", raw_value="Nhava Sheva", page=1, confidence=0.97),
        ExtractedField(field="container_numbers", raw_value="MSKU1234567", page=1, confidence=0.94),
        ExtractedField(field="package_count", raw_value="40", page=1, confidence=0.93),
        ExtractedField(field="weight", raw_value="12500 kg", page=1, confidence=0.95),
        ExtractedField(field="product_description", raw_value="Lithium-ion battery packs", page=1, confidence=0.9),
    ],
    "certificate_of_origin": [
        ExtractedField(field="certificate_number", raw_value="COO-VN-8891", page=2, confidence=0.97),
        ExtractedField(field="issuing_authority", raw_value="Vietnam Chamber of Commerce", page=1, confidence=0.9),
        ExtractedField(field="exporter", raw_value="Acme Industrial Supplies", page=1, confidence=0.94),
        ExtractedField(field="importer", raw_value="Meridian Imports Pvt Ltd", page=1, confidence=0.94),
        ExtractedField(field="product", raw_value="Lithium-ion battery packs", page=1, confidence=0.92),
        ExtractedField(field="country_of_origin", raw_value="Vietnam", page=2, confidence=0.96),
        ExtractedField(field="issue_date", raw_value="2026-07-28", page=1, confidence=0.95),
        ExtractedField(field="expiry_date", raw_value="2027-07-28", page=1, confidence=0.95),
    ],
    "certificate_of_origin_v2": [
        ExtractedField(field="certificate_number", raw_value="COO-DE-2048", page=1, confidence=0.98),
        ExtractedField(field="issuing_authority", raw_value="IHK Hamburg", page=1, confidence=0.94),
        ExtractedField(field="exporter", raw_value="Acme Industrial Supplies", page=1, confidence=0.97),
        ExtractedField(field="importer", raw_value="Meridian Imports Pvt Ltd", page=1, confidence=0.97),
        ExtractedField(field="product", raw_value="Lithium-ion battery packs", page=1, confidence=0.93),
        ExtractedField(field="country_of_origin", raw_value="Germany", page=1, confidence=0.99),
        ExtractedField(field="issue_date", raw_value="2026-09-01", page=1, confidence=0.97),
        ExtractedField(field="expiry_date", raw_value="2027-09-01", page=1, confidence=0.97),
    ],
    "product_certificate": [
        ExtractedField(field="certificate_number", raw_value="PC-EXP-110", page=1, confidence=0.96),
        ExtractedField(field="product", raw_value="Lithium-ion battery packs", page=1, confidence=0.93),
        ExtractedField(field="issuer", raw_value="TUV Demo Labs", page=1, confidence=0.9),
        ExtractedField(field="issue_date", raw_value="2023-01-10", page=1, confidence=0.95),
        ExtractedField(field="expiry_date", raw_value="2025-01-10", page=1, confidence=0.98),
        ExtractedField(field="certification_type", raw_value="UN38.3", page=1, confidence=0.88),
        ExtractedField(field="status", raw_value="expired", page=1, confidence=0.9),
    ],
}


from app.ai.heuristic_extractor import classify_from_text_and_name, extract_fields_from_pages


class MockAIProvider(AIProvider):
    name = "mock"

    def classify(self, filename: str, text: str) -> ClassificationResult:
        result = classify_from_text_and_name(filename, text)
        if result.document_type == DocumentType.OTHER.value:
            dtype = _filename_type(filename)
            if dtype != DocumentType.OTHER.value:
                return ClassificationResult(document_type=dtype, confidence=0.85, reason="filename_keyword_fallback")
        return result

    def extract(
        self,
        document_type: str,
        filename: str,
        text: str,
        pages: list[tuple[int, str]] | None = None,
    ) -> ExtractionResult:
        lower = filename.lower()
        effective_pages = pages or ([(1, text)] if text else [])

        # 1. First attempt: Real heuristic extraction from actual page text
        real_fields = extract_fields_from_pages(document_type, effective_pages)
        if real_fields:
            overall_conf = min((f.confidence for f in real_fields), default=0.9)
            return ExtractionResult(fields=real_fields, raw_text=text, overall_confidence=overall_conf)

        # 2. Demo fallback: Hero scenario support only for seeded demo files
        is_demo_file = any(
            token in lower
            for token in [
                "inv-2048", "pl-2048", "maeu2048ham", "coo-vn-8891",
                "germany_v2", "coo-de-2048", "pc-exp-110", "v2", "corrected",
                "nc-7718", "pl-7718", "hl-7718", "pc-exp-7718", "inv-5512", "inv-9901"
            ]
        )

        if is_demo_file:
            if "v2" in lower or "corrected" in lower or "germany" in lower:
                fields = HERO_FIELDS["certificate_of_origin_v2"]
            elif document_type in HERO_FIELDS:
                fields = HERO_FIELDS[document_type]
            else:
                fields = []
            if fields:
                return ExtractionResult(fields=fields, raw_text=text, overall_confidence=min((f.confidence for f in fields), default=0.9))

        # 3. Low confidence test simulation if requested in filename
        if "lowconf" in lower:
            fields = [
                ExtractedField(field="hs_code", raw_value="8507", page=1, confidence=0.41),
                ExtractedField(field="quantity", raw_value="unknown", page=1, confidence=0.3),
            ]
            return ExtractionResult(fields=fields, raw_text=text, overall_confidence=0.35)

        # 4. Fallback for non-demo text with no matched trade fields
        if text.strip():
            first_line = text.strip().split("\n")[0][:120]
            fields = [
                ExtractedField(field="document_description", raw_value=first_line, page=1, confidence=0.6)
            ]
            return ExtractionResult(fields=fields, raw_text=text, overall_confidence=0.6)

        # 5. Empty document: return zero fields
        return ExtractionResult(fields=[], raw_text="", overall_confidence=0.0)

    def explain(self, prompt: str) -> ExplanationResult:
        return ExplanationResult(
            text="Configured compliance checks identified inconsistencies in extracted evidence. Human review is required before clearance.",
            citations=[],
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            seed = sum(ord(c) for c in text) % 97
            vectors.append([((seed + i) % 13) / 13.0 for i in range(8)])
        return vectors
