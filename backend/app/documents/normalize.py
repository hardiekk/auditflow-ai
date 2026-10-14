from __future__ import annotations

import re
from datetime import datetime

COUNTRY_MAP = {
    "germany": "DE",
    "de": "DE",
    "deu": "DE",
    "federal republic of germany": "DE",
    "vietnam": "VN",
    "vn": "VN",
    "viet nam": "VN",
    "india": "IN",
    "in": "IN",
    "bharat": "IN",
    "united states": "US",
    "usa": "US",
    "us": "US",
    "china": "CN",
    "cn": "CN",
    "netherlands": "NL",
    "nl": "NL",
    "belgium": "BE",
    "be": "BE",
    "united kingdom": "GB",
    "uk": "GB",
    "gb": "GB",
}

CURRENCY_MAP = {"euro": "EUR", "€": "EUR", "eur": "EUR", "usd": "USD", "$": "USD", "inr": "INR"}


def normalize_country(raw: str | None) -> tuple[str | None, str]:
    if raw is None or str(raw).strip() == "":
        return None, "empty"
    key = re.sub(r"\s+", " ", str(raw).strip().lower())
    return COUNTRY_MAP.get(key, key.upper()[:2] if len(key) == 2 else key), "country_map"


def normalize_currency(raw: str | None) -> tuple[str | None, str]:
    if not raw:
        return None, "empty"
    key = str(raw).strip().lower()
    return CURRENCY_MAP.get(key, key.upper()), "currency_map"


def normalize_quantity(raw: str | int | float | None) -> tuple[str | None, str]:
    if raw is None or raw == "":
        return None, "empty"
    text = str(raw).replace(",", "").strip()
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return str(raw), "passthrough"
    value = match.group(0)
    if "." in value:
        value = str(float(value))
    else:
        value = str(int(value))
    return value, "numeric"


def normalize_weight(raw: str | None) -> tuple[str | None, str]:
    if raw is None or raw == "":
        return None, "empty"
    text = str(raw).lower().replace(",", "")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return str(raw), "passthrough"
    num = float(match.group(0))
    if "lb" in text:
        num = num * 0.453592
    return f"{num:.3f}", "kg"


def normalize_date(raw: str | None) -> tuple[str | None, str]:
    if not raw:
        return None, "empty"
    text = str(raw).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%d %b %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat(), "date_parse"
        except ValueError:
            continue
    return text, "passthrough"


def normalize_name(raw: str | None) -> tuple[str | None, str]:
    if not raw:
        return None, "empty"
    cleaned = re.sub(r"\s+", " ", str(raw).strip())
    return cleaned.upper(), "casefold"


def normalize_hs(raw: str | None) -> tuple[str | None, str]:
    if not raw:
        return None, "empty"
    digits = re.sub(r"\D", "", str(raw))
    return digits or str(raw), "digits"


def normalize_field(field: str, raw) -> tuple[str | None, str]:
    if field in {"country_of_origin", "origin_country", "destination_country"}:
        return normalize_country(None if raw is None else str(raw))
    if field in {"currency"}:
        return normalize_currency(None if raw is None else str(raw))
    if field in {"quantity", "package_count", "unit_price", "total_value"}:
        return normalize_quantity(raw)
    if field in {"gross_weight", "net_weight", "weight"}:
        return normalize_weight(None if raw is None else str(raw))
    if field in {"invoice_date", "issue_date", "expiry_date", "shipment_date"}:
        return normalize_date(None if raw is None else str(raw))
    if field in {"seller", "buyer", "shipper", "consignee", "exporter", "importer", "issuer", "issuing_authority"}:
        return normalize_name(None if raw is None else str(raw))
    if field in {"hs_code"}:
        return normalize_hs(None if raw is None else str(raw))
    if raw is None:
        return None, "empty"
    return str(raw).strip(), "passthrough"
