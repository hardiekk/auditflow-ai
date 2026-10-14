import io
import json
import sys
import httpx
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

BASE_URL = "http://localhost:8000"

def create_pdf(title, lines):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, 750, title)
    c.setFont("Helvetica", 11)
    y = 710
    for line in lines:
        c.drawString(72, y, line)
        y -= 22
    c.save()
    buf.seek(0)
    return buf.getvalue()

def main():
    client = httpx.Client(timeout=30.0)

    print("=== Step 1: Verify Seeded Demo Persona & Flag ===")
    r = client.post(f"{BASE_URL}/auth/login", json={"email": "admin@auditflow.demo", "password": "AuditFlow!demo"})
    assert r.status_code == 200, f"Demo login failed: {r.text}"
    demo_token = r.json()["access_token"]
    demo_headers = {"Authorization": f"Bearer {demo_token}"}
    
    r = client.get(f"{BASE_URL}/auth/me", headers=demo_headers)
    assert r.status_code == 200
    me_demo = r.json()
    print("Demo /auth/me:", me_demo)
    assert me_demo["is_demo"] is True, "Expected is_demo=True for Northwind Logistics"
    assert me_demo["organization_name"] == "Northwind Logistics"
    print("✓ Demo Persona and is_demo flag verified!")

    print("\n=== Step 2: Register New Live Enterprise Organization ===")
    reg_payload = {
        "email": "auditor@zenith-logistics.io",
        "password": "SecurePassword!2026",
        "full_name": "Sarah Jenkins",
        "organization_name": "Zenith Global Freight Corp"
    }
    r = client.post(f"{BASE_URL}/auth/register", json=reg_payload)
    if r.status_code == 400 and "already registered" in r.text:
        r = client.post(f"{BASE_URL}/auth/login", json={"email": reg_payload["email"], "password": reg_payload["password"]})
    assert r.status_code == 200, f"Live org auth failed: {r.text}"
    live_token = r.json()["access_token"]
    live_headers = {"Authorization": f"Bearer {live_token}"}

    r = client.get(f"{BASE_URL}/auth/me", headers=live_headers)
    assert r.status_code == 200
    me_live = r.json()
    print("Live /auth/me:", me_live)
    assert me_live["is_demo"] is False, "Expected is_demo=False for new live organization"
    assert me_live["organization_name"] == "Zenith Global Freight Corp"
    print("✓ Live Enterprise Organization verified with is_demo=False!")

    print("\n=== Step 3: Create Live Consignment ===")
    shipment_payload = {
        "reference_number": "SHP-ZENITH-9944",
        "origin_country": "JP",
        "destination_country": "US",
        "origin_port": "Port of Tokyo, Japan",
        "destination_port": "Port of Long Beach, USA",
        "carrier": "ONE Ocean Network Express",
    }
    r = client.post(f"{BASE_URL}/shipments", json=shipment_payload, headers=live_headers)
    assert r.status_code == 200, f"Shipment creation failed: {r.text}"
    shipment = r.json()
    shipment_id = shipment["id"]
    print(f"Created live shipment: {shipment['reference_number']} (ID: {shipment_id})")

    print("\n=== Step 4: Generate and Upload Real Custom Commercial Invoice ===")
    invoice_pdf = create_pdf("COMMERCIAL INVOICE #INV-TK-9944", [
        "Invoice No: INV-TK-9944",
        "Invoice Date: 2026-09-12",
        "Seller: Tokyo Precision Instruments Ltd, Tokyo, Japan",
        "Buyer: Zenith Global Freight Corp, Long Beach, USA",
        "Country of Origin: Japan",
        "Product Description: High-Precision Laser Optical Sensors",
        "HS Code: 9031.80",
        "Quantity: 750",
        "Unit Price: 250.00",
        "Total Amount: 187500.00",
        "Currency: USD",
    ])

    files = {"file": ("commercial_invoice_INV-TK-9944.pdf", invoice_pdf, "application/pdf")}
    r = client.post(f"{BASE_URL}/shipments/{shipment_id}/documents", files=files, headers=live_headers)
    assert r.status_code == 200, f"Document upload failed: {r.text}"
    doc_res = r.json()
    doc_id = doc_res["id"]
    print(f"Uploaded real invoice, doc_id: {doc_id}")

    import time
    time.sleep(1.0)

    print("\n=== Step 5: Verify Extracted Evidence Has REAL Values (Not Hero Mock) ===")
    r = client.get(f"{BASE_URL}/shipments/{shipment_id}/documents", headers=live_headers)
    assert r.status_code == 200
    docs = r.json()
    print(f"Shipment has {len(docs)} documents.")

    # Check evidence directly from SQLite to confirm exact values extracted
    import sqlite3
    conn = sqlite3.connect("auditflow.db")
    cur = conn.cursor()
    cur.execute("SELECT field, raw_value, normalized_value, page, confidence FROM evidence WHERE shipment_id = ?", (shipment_id,))
    rows = cur.fetchall()
    print("Database evidence rows for live shipment:")
    extracted_map = {}
    for f, raw, norm, pg, conf in rows:
        print(f"  {f}: raw='{raw}', norm='{norm}', page={pg}, conf={conf}")
        extracted_map[f] = raw

    assert extracted_map.get("invoice_number") == "INV-TK-9944", f"Expected INV-TK-9944, got {extracted_map.get('invoice_number')}"
    assert extracted_map.get("country_of_origin") == "Japan", f"Expected Japan, got {extracted_map.get('country_of_origin')}"
    assert extracted_map.get("quantity") == "750", f"Expected 750, got {extracted_map.get('quantity')}"
    assert extracted_map.get("hs_code") == "9031.80", f"Expected 9031.80, got {extracted_map.get('hs_code')}"
    print("✓ Real PDF field extractions verified! Zero mock substitution.")

    print("\n=== Step 6: Verify Empty / No-Text PDF Fails Gracefully ===")
    empty_pdf = io.BytesIO()
    c = canvas.Canvas(empty_pdf, pagesize=letter)
    c.line(100, 100, 200, 200) # vector line only, no text
    c.save()
    empty_pdf.seek(0)
    
    files = {"file": ("scanned_blank_document.pdf", empty_pdf.getvalue(), "application/pdf")}
    r = client.post(f"{BASE_URL}/shipments/{shipment_id}/documents", files=files, headers=live_headers)
    assert r.status_code == 200
    blank_doc_id = r.json()["id"]

    time.sleep(1.0)
    r = client.get(f"{BASE_URL}/shipments/{shipment_id}/documents", headers=live_headers)
    all_docs = {d["name"]: d for d in r.json()}
    blank_doc = all_docs.get("scanned_blank_document.pdf")
    print("Blank document processing status:", blank_doc.get("processing_status"))
    assert blank_doc.get("processing_status") == "failed", f"Expected blank document to fail, got {blank_doc.get('processing_status')}"
    print("✓ Scanned / blank document failed gracefully without fabricating data!")

    print("\n=======================================================")
    print("ALL REAL-USER END-TO-END VERIFICATION CHECKS PASSED! ✓")
    print("=======================================================")

if __name__ == "__main__":
    main()
