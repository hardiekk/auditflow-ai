from __future__ import annotations

import re
from typing import Optional
from app.ai.provider import ClassificationResult, ExtractedField, ExtractionResult
from app.models.entities import DocumentType

DOCUMENT_KEYWORDS = [
    (DocumentType.COMMERCIAL_INVOICE.value, [r'commercial\s+invoice', r'invoice\s+no', r'tax\s+invoice', r'bill\s+to']),
    (DocumentType.PACKING_LIST.value, [r'packing\s+list', r'package\s+count', r'net\s+weight', r'case\s+no']),
    (DocumentType.BILL_OF_LADING.value, [r'bill\s+of\s+lading', r'ocean\s+bill', r'port\s+of\s+loading', r'b/?l\s+no']),
    (DocumentType.CERTIFICATE_OF_ORIGIN.value, [r'certificate\s+of\s+origin', r'chamber\s+of\s+commerce', r'country\s+of\s+origin']),
    (DocumentType.PRODUCT_CERTIFICATE.value, [r'product\s+certificate', r'test\s+report', r'un\s*38\.3', r'compliance\s+certificate']),
    (DocumentType.SUPPLIER_DECLARATION.value, [r'supplier\s+declaration', r'manufacturer\s+declaration']),
]


def classify_from_text_and_name(filename: str, text: str) -> ClassificationResult:
    text_lower = text.lower() if text else ""
    filename_lower = filename.lower()

    # 1. Check text content
    for doc_type, patterns in DOCUMENT_KEYWORDS:
        for pat in patterns:
            if re.search(pat, text_lower):
                return ClassificationResult(
                    document_type=doc_type,
                    confidence=0.95,
                    reason=f"Matched pattern '{pat}' in document text.",
                )

    # 2. Check filename
    for doc_type, patterns in DOCUMENT_KEYWORDS:
        for pat in patterns:
            if re.search(pat, filename_lower):
                return ClassificationResult(
                    document_type=doc_type,
                    confidence=0.85,
                    reason=f"Matched filename pattern '{pat}'.",
                )

    return ClassificationResult(
        document_type=DocumentType.OTHER.value,
        confidence=0.5,
        reason="Document type could not be confidently identified from text or filename.",
    )


def extract_fields_from_pages(document_type: str, pages: list[tuple[int, str]]) -> list[ExtractedField]:
    """
    Extracts real trade fields from page-by-page text.
    Each page is a tuple of (page_number, text).
    """
    fields: list[ExtractedField] = []
    found_fields: set[str] = set()

    for page_num, text in pages:
        if not text:
            continue

        # --- Commercial Invoice Fields ---
        if document_type == DocumentType.COMMERCIAL_INVOICE.value:
            if 'invoice_number' not in found_fields:
                m = re.search(r'(?:Invoice|INV|Bill)[\s\-_]*(?:No|Number|#)[\s.:]*([A-Za-z0-9\-_]+)', text, re.IGNORECASE)
                if m:
                    fields.append(ExtractedField(field='invoice_number', raw_value=m.group(1).strip(), page=page_num, confidence=0.95))
                    found_fields.add('invoice_number')

            if 'invoice_date' not in found_fields:
                m = re.search(r'(?:Invoice\s+)?Date[\s.:]*([0-9]{4}[-/][0-9]{2}[-/][0-9]{2}|[0-9]{2}[-/][0-9]{2}[-/][0-9]{4}|[A-Za-z]+\s+[0-9]{1,2},?\s+[0-9]{4})', text, re.IGNORECASE)
                if m:
                    fields.append(ExtractedField(field='invoice_date', raw_value=m.group(1).strip(), page=page_num, confidence=0.92))
                    found_fields.add('invoice_date')

            if 'seller' not in found_fields:
                m = re.search(r'(?:Seller|Exporter|Vendor|Shipper)[\s.:]+([^\n\r,]+)', text, re.IGNORECASE)
                if m:
                    fields.append(ExtractedField(field='seller', raw_value=m.group(1).strip(), page=page_num, confidence=0.90))
                    found_fields.add('seller')

            if 'buyer' not in found_fields:
                m = re.search(r'(?:Buyer|Consignee|Sold\s+To|To)[\s.:]+([^\n\r,]+)', text, re.IGNORECASE)
                if m:
                    fields.append(ExtractedField(field='buyer', raw_value=m.group(1).strip(), page=page_num, confidence=0.90))
                    found_fields.add('buyer')

            if 'country_of_origin' not in found_fields:
                m = re.search(r'(?:Country\s+of\s+Origin|Origin)[\s.:]+([A-Za-z\s]+?)(?:[\n\r,.]|$)', text, re.IGNORECASE)
                if m:
                    val = m.group(1).strip()
                    if len(val) > 1 and len(val) < 40:
                        fields.append(ExtractedField(field='country_of_origin', raw_value=val, page=page_num, confidence=0.94))
                        found_fields.add('country_of_origin')

            if 'hs_code' not in found_fields:
                m = re.search(r'(?:HS|Tariff|HTS)[\s\-_]*(?:Code|No|Number)?[\s.:]*([0-9\.]+)', text, re.IGNORECASE)
                if m:
                    fields.append(ExtractedField(field='hs_code', raw_value=m.group(1).strip(), page=page_num, confidence=0.92))
                    found_fields.add('hs_code')

            if 'quantity' not in found_fields:
                m = re.search(r'(?:Quantity|Qty|Units)[\s.:]*([0-9,]+)', text, re.IGNORECASE)
                if m:
                    fields.append(ExtractedField(field='quantity', raw_value=m.group(1).strip().replace(',', ''), page=page_num, confidence=0.93))
                    found_fields.add('quantity')

            if 'unit_price' not in found_fields:
                m = re.search(r'(?:Unit\s+Price|Price)[\s.:]*([0-9,.]+)', text, re.IGNORECASE)
                if m:
                    fields.append(ExtractedField(field='unit_price', raw_value=m.group(1).strip().replace(',', ''), page=page_num, confidence=0.88))
                    found_fields.add('unit_price')

            if 'total_value' not in found_fields:
                m = re.search(r'(?:Total\s+Amount|Total\s+Value|Invoice\s+Value|Total)[\s.:]*([0-9,.]+)', text, re.IGNORECASE)
                if m:
                    fields.append(ExtractedField(field='total_value', raw_value=m.group(1).strip().replace(',', ''), page=page_num, confidence=0.92))
                    found_fields.add('total_value')

            if 'currency' not in found_fields:
                m = re.search(r'(?:Currency)[\s.:]*([A-Z]{3})', text, re.IGNORECASE)
                if m:
                    fields.append(ExtractedField(field='currency', raw_value=m.group(1).strip().upper(), page=page_num, confidence=0.95))
                    found_fields.add('currency')
                elif '€' in text or 'EUR' in text:
                    fields.append(ExtractedField(field='currency', raw_value='EUR', page=page_num, confidence=0.90))
                    found_fields.add('currency')
                elif '$' in text or 'USD' in text:
                    fields.append(ExtractedField(field='currency', raw_value='USD', page=page_num, confidence=0.90))
                    found_fields.add('currency')

        # --- Packing List Fields ---
        elif document_type == DocumentType.PACKING_LIST.value:
            if 'packing_list_number' not in found_fields:
                m = re.search(r'(?:Packing\s+List|PL)[\s\-_]*(?:No|Number|#)[\s.:]*([A-Za-z0-9\-_]+)', text, re.IGNORECASE)
                if m:
                    fields.append(ExtractedField(field='packing_list_number', raw_value=m.group(1).strip(), page=page_num, confidence=0.95))
                    found_fields.add('packing_list_number')

            if 'package_count' not in found_fields:
                m = re.search(r'(?:Package\s+Count|Packages|Total\s+Packages|Boxes|Crates)[\s.:]*([0-9,]+)', text, re.IGNORECASE)
                if m:
                    fields.append(ExtractedField(field='package_count', raw_value=m.group(1).strip().replace(',', ''), page=page_num, confidence=0.90))
                    found_fields.add('package_count')

            if 'quantity' not in found_fields:
                m = re.search(r'(?:Packed\s+Quantity|Quantity|Qty|Total\s+Units)[\s.:]*([0-9,]+)', text, re.IGNORECASE)
                if m:
                    fields.append(ExtractedField(field='quantity', raw_value=m.group(1).strip().replace(',', ''), page=page_num, confidence=0.93))
                    found_fields.add('quantity')

            if 'gross_weight' not in found_fields:
                m = re.search(r'(?:Gross\s+Weight|G\.?W\.?)[\s.:]*([0-9,.]+\s*(?:kg|kgs|lb|lbs|mt|ton)?)', text, re.IGNORECASE)
                if m:
                    fields.append(ExtractedField(field='gross_weight', raw_value=m.group(1).strip(), page=page_num, confidence=0.94))
                    found_fields.add('gross_weight')

            if 'net_weight' not in found_fields:
                m = re.search(r'(?:Net\s+Weight|N\.?W\.?)[\s.:]*([0-9,.]+\s*(?:kg|kgs|lb|lbs)?)', text, re.IGNORECASE)
                if m:
                    fields.append(ExtractedField(field='net_weight', raw_value=m.group(1).strip(), page=page_num, confidence=0.90))
                    found_fields.add('net_weight')

        # --- Bill of Lading Fields ---
        elif document_type == DocumentType.BILL_OF_LADING.value:
            if 'bl_number' not in found_fields:
                m = re.search(r'(?:Bill\s+of\s+Lading|B/?L)[\s\-_]*(?:No|Number|#)[\s.:]*([A-Za-z0-9\-_]+)', text, re.IGNORECASE)
                if m:
                    fields.append(ExtractedField(field='bl_number', raw_value=m.group(1).strip(), page=page_num, confidence=0.95))
                    found_fields.add('bl_number')

            if 'carrier' not in found_fields:
                m = re.search(r'(?:Carrier|Shipping\s+Line|Line)[\s.:]+([^\n\r,]+)', text, re.IGNORECASE)
                if m:
                    fields.append(ExtractedField(field='carrier', raw_value=m.group(1).strip(), page=page_num, confidence=0.90))
                    found_fields.add('carrier')

            if 'shipper' not in found_fields:
                m = re.search(r'(?:Shipper)[\s.:]+([^\n\r,]+)', text, re.IGNORECASE)
                if m:
                    fields.append(ExtractedField(field='shipper', raw_value=m.group(1).strip(), page=page_num, confidence=0.90))
                    found_fields.add('shipper')

            if 'consignee' not in found_fields:
                m = re.search(r'(?:Consignee)[\s.:]+([^\n\r,]+)', text, re.IGNORECASE)
                if m:
                    fields.append(ExtractedField(field='consignee', raw_value=m.group(1).strip(), page=page_num, confidence=0.90))
                    found_fields.add('consignee')

            if 'origin_port' not in found_fields:
                m = re.search(r'(?:Port\s+of\s+Loading|Loading\s+Port|POL)[\s.:]+([^\n\r,]+)', text, re.IGNORECASE)
                if m:
                    fields.append(ExtractedField(field='origin_port', raw_value=m.group(1).strip(), page=page_num, confidence=0.92))
                    found_fields.add('origin_port')

            if 'destination_port' not in found_fields:
                m = re.search(r'(?:Port\s+of\s+Discharge|Discharge\s+Port|POD)[\s.:]+([^\n\r,]+)', text, re.IGNORECASE)
                if m:
                    fields.append(ExtractedField(field='destination_port', raw_value=m.group(1).strip(), page=page_num, confidence=0.92))
                    found_fields.add('destination_port')

            if 'weight' not in found_fields:
                m = re.search(r'(?:Cargo\s+Weight|Weight|Declared\s+Cargo\s+Weight)[\s.:]*([0-9,.]+\s*(?:kg|kgs|lb|lbs|mt|ton)?)', text, re.IGNORECASE)
                if m:
                    fields.append(ExtractedField(field='weight', raw_value=m.group(1).strip(), page=page_num, confidence=0.92))
                    found_fields.add('weight')

        # --- Certificate of Origin Fields ---
        elif document_type == DocumentType.CERTIFICATE_OF_ORIGIN.value:
            if 'certificate_number' not in found_fields:
                m = re.search(r'(?:Certificate|COO)[\s\-_]*(?:No|Number|#)[\s.:]*([A-Za-z0-9\-_]+)', text, re.IGNORECASE)
                if m:
                    fields.append(ExtractedField(field='certificate_number', raw_value=m.group(1).strip(), page=page_num, confidence=0.95))
                    found_fields.add('certificate_number')

            if 'issuing_authority' not in found_fields:
                m = re.search(r'(?:Issuing\s+Authority|Chamber\s+of\s+Commerce|Issued\s+By)[\s.:]+([^\n\r,]+)', text, re.IGNORECASE)
                if m:
                    fields.append(ExtractedField(field='issuing_authority', raw_value=m.group(1).strip(), page=page_num, confidence=0.90))
                    found_fields.add('issuing_authority')

            if 'exporter' not in found_fields:
                m = re.search(r'(?:Exporter)[\s.:]+([^\n\r,]+)', text, re.IGNORECASE)
                if m:
                    fields.append(ExtractedField(field='exporter', raw_value=m.group(1).strip(), page=page_num, confidence=0.90))
                    found_fields.add('exporter')

            if 'country_of_origin' not in found_fields:
                m = re.search(r'(?:Certified\s+Country\s+of\s+Origin|Country\s+of\s+Origin|Origin)[\s.:]+([A-Za-z\s]+?)(?:[\n\r,.]|$)', text, re.IGNORECASE)
                if m:
                    val = m.group(1).strip()
                    if len(val) > 1 and len(val) < 40:
                        fields.append(ExtractedField(field='country_of_origin', raw_value=val, page=page_num, confidence=0.96))
                        found_fields.add('country_of_origin')

            if 'expiry_date' not in found_fields:
                m = re.search(r'(?:Expiry\s+Date|Expires|Valid\s+Until)[\s.:]*([0-9]{4}[-/][0-9]{2}[-/][0-9]{2}|[0-9]{2}[-/][0-9]{2}[-/][0-9]{4})', text, re.IGNORECASE)
                if m:
                    fields.append(ExtractedField(field='expiry_date', raw_value=m.group(1).strip(), page=page_num, confidence=0.92))
                    found_fields.add('expiry_date')

            if 'issue_date' not in found_fields:
                m = re.search(r'(?:Issue\s+Date|Issued\s+On|Date)[\s.:]*([0-9]{4}[-/][0-9]{2}[-/][0-9]{2}|[0-9]{2}[-/][0-9]{2}[-/][0-9]{4})', text, re.IGNORECASE)
                if m:
                    fields.append(ExtractedField(field='issue_date', raw_value=m.group(1).strip(), page=page_num, confidence=0.90))
                    found_fields.add('issue_date')

        # --- Product Certificate Fields ---
        elif document_type == DocumentType.PRODUCT_CERTIFICATE.value:
            if 'certificate_number' not in found_fields:
                m = re.search(r'(?:Report|Certificate)[\s\-_]*(?:Number|No|#)[\s.:]*([A-Za-z0-9\-_]+)', text, re.IGNORECASE)
                if m:
                    fields.append(ExtractedField(field='certificate_number', raw_value=m.group(1).strip(), page=page_num, confidence=0.95))
                    found_fields.add('certificate_number')

            if 'expiry_date' not in found_fields:
                m = re.search(r'(?:Expiry\s+Date|Expires|Valid\s+Until)[\s.:]*([0-9]{4}[-/][0-9]{2}[-/][0-9]{2}|[0-9]{2}[-/][0-9]{2}[-/][0-9]{4})', text, re.IGNORECASE)
                if m:
                    fields.append(ExtractedField(field='expiry_date', raw_value=m.group(1).strip(), page=page_num, confidence=0.94))
                    found_fields.add('expiry_date')

    # Common fallback if nothing found
    if not fields and text.strip():
        first_line = text.strip().split('\n')[0][:100]
        fields.append(ExtractedField(field='document_description', raw_value=first_line, page=1, confidence=0.6))

    return fields
