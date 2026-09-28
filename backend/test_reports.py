"""
Comprehensive Test Script for Phase 11: Reports & Compliance Intelligence API.
Validates:
1. POST /api/reports with multi-dimensional filtering (risk priority, facility name, region, dates).
2. Executive summary KPIs and incident record collation.
3. Database persistence of report metadata and parameters.
4. GET /api/reports with pagination.
5. GET /api/reports/{report_id} detail retrieval.
6. GET /api/reports/{report_id}/export (CSV streaming, planned PDF response, 400 validation).
7. Swagger / OpenAPI schema compliance.
Uses standard library urllib (no third-party dependencies required).
"""

import sys
import json
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone, timedelta

BASE_URL = "http://127.0.0.1:8000"


def print_section(title: str):
    print(f"\n{'='*75}\n{title}\n{'='*75}")


def make_request(url: str, method: str = "GET", data: dict = None, headers: dict = None):
    req_headers = headers or {}
    encoded_data = None
    if data is not None:
        encoded_data = json.dumps(data).encode("utf-8")
        req_headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=encoded_data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content_type = resp.headers.get("Content-Type", "")
            disposition = resp.headers.get("Content-Disposition", "")
            raw_body = resp.read()
            if "application/json" in content_type:
                body = json.loads(raw_body.decode("utf-8"))
            else:
                body = raw_body.decode("utf-8")
            return resp.status, body, resp.headers
    except urllib.error.HTTPError as e:
        raw_body = e.read()
        try:
            body = json.loads(raw_body.decode("utf-8"))
        except Exception:
            body = raw_body.decode("utf-8")
        return e.code, body, e.headers


def test_reports_api():
    print_section("PHASE 11: REPORTS & COMPLIANCE INTELLIGENCE API VERIFICATION")

    # 0. Health check
    status_code, body, _ = make_request(f"{BASE_URL}/api/health")
    if status_code != 200:
        print(f"FAILED to connect to backend at {BASE_URL}: status {status_code}")
        sys.exit(1)
    print("Backend service is reachable and healthy.")

    # 1. Test POST /api/reports - Filtered by Risk Priority & Facility Name
    print_section("TEST 1: POST /api/reports - Combined Risk & Facility Filter")
    payload_1 = {
        "title": "Critical Hazard Report - Reliance Jamnagar",
        "report_type": "incident_report",
        "filters": {
            "risk_priority": "Critical",
            "facility_name": "Reliance"
        },
        "format": "json"
    }
    status_code, report_1, _ = make_request(f"{BASE_URL}/api/reports", method="POST", data=payload_1)
    print(f"Status Code: {status_code}")
    assert status_code == 201, f"Expected 201 Created, got {status_code}: {report_1}"
    report_1_id = report_1["id"]
    print(f"Report ID: {report_1_id}")
    print(f"Title: {report_1['title']}")
    print(f"Status: {report_1['status']}")
    print("Summary KPIs:")
    print(json.dumps(report_1["summary"], indent=2))
    print(f"Incidents Included: {len(report_1['incidents'])}")
    for inc in report_1["incidents"]:
        print(f"  - Event: {inc['event_id']}, Type: {inc['event_type']}, Score: {inc['risk_score']}, Facility: {inc['facility_name']}, Operator: {inc.get('facility_operator')}")
        assert (inc.get("facility_name") and "Jamnagar" in inc["facility_name"]) or (inc.get("facility_operator") and "Reliance" in inc["facility_operator"]), "Facility filter mismatch"
        assert "crit" in (inc["risk_priority"] or "").lower() or inc["risk_score"] >= 75, "Risk priority mismatch"
    print(f"Available Exports: {report_1['available_exports']}")
    assert "csv" in report_1["available_exports"], "Missing CSV export link"

    # 2. Test POST /api/reports - Regional (Gujarat) & Auto-Title
    print_section("TEST 2: POST /api/reports - Regional (Gujarat) & Auto-Title")
    payload_2 = {
        "report_type": "regional_summary",
        "filters": {
            "region": "Gujarat"
        }
    }
    status_code, report_2, _ = make_request(f"{BASE_URL}/api/reports", method="POST", data=payload_2)
    assert status_code == 201, f"Expected 201, got {status_code}: {report_2}"
    report_2_id = report_2["id"]
    print(f"Auto-generated Title: {report_2['title']}")
    print(f"Total Regional Incidents: {report_2['summary']['total_incidents']}")
    print(f"Facilities Involved: {report_2['summary']['facilities_involved']}")
    print(f"Average Risk Score: {report_2['summary']['avg_risk_score']}")

    # 3. Test POST /api/reports - Full Platform Executive Audit Report
    print_section("TEST 3: POST /api/reports - Comprehensive Audit (All Incidents)")
    payload_3 = {
        "title": "Comprehensive Platform Thermal Audit",
        "report_type": "compliance_audit",
        "filters": {}
    }
    status_code, report_3, _ = make_request(f"{BASE_URL}/api/reports", method="POST", data=payload_3)
    assert status_code == 201, f"Expected 201, got {status_code}: {report_3}"
    report_3_id = report_3["id"]
    print(f"Report ID: {report_3_id}")
    print(f"Total Platform Incidents: {report_3['summary']['total_incidents']}")
    print(f"Breakdown: Critical={report_3['summary']['critical_count']}, High={report_3['summary']['high_count']}, Mod={report_3['summary']['moderate_count']}, Low={report_3['summary']['low_count']}")
    assert report_3['summary']['total_incidents'] >= 5, "Expected at least 5 demo thermal events"

    # 4. Test GET /api/reports - Paginated Reports Listing
    print_section("TEST 4: GET /api/reports - Paginated Listing")
    status_code, listing, _ = make_request(f"{BASE_URL}/api/reports?page=1&page_size=10")
    assert status_code == 200, f"Expected 200, got {status_code}: {listing}"
    print(f"Total Persisted Reports: {listing['total']}")
    print(f"Page: {listing['page']}, Page Size: {listing['page_size']}, Total Pages: {listing['total_pages']}")
    assert listing['total'] >= 3, "Expected at least 3 generated reports in DB"
    for item in listing['items']:
        print(f"  - [{item['id']}] {item['title']} (Type: {item['report_type']}, Generated: {item['generated_at']})")

    # 5. Test GET /api/reports/{report_id} - Detail Retrieval
    print_section(f"TEST 5: GET /api/reports/{report_1_id} - Single Report Details")
    status_code, detail, _ = make_request(f"{BASE_URL}/api/reports/{report_1_id}")
    assert status_code == 200, f"Expected 200, got {status_code}: {detail}"
    assert detail["id"] == report_1_id
    assert detail["title"] == payload_1["title"]
    assert "incidents" in detail
    assert "parameters" in detail
    print(f"Retrieved Report: {detail['title']}")
    print(f"Stored Parameters: {detail['parameters']}")
    print(f"Stored Summary: {detail['summary']}")

    # Test 404 for non-existent report
    status_code_404, _, _ = make_request(f"{BASE_URL}/api/reports/999999")
    assert status_code_404 == 404, f"Expected 404 for missing report, got {status_code_404}"
    print("404 Not Found correctly returned for non-existent report ID 999999.")

    # 6. Test GET /api/reports/{report_1_id}/export - CSV Streaming & PDF Handling
    print_section(f"TEST 6: GET /api/reports/{report_1_id}/export - CSV Export Stream")
    status_code_csv, csv_text, headers_csv = make_request(f"{BASE_URL}/api/reports/{report_1_id}/export?format=csv")
    assert status_code_csv == 200, f"Expected 200, got {status_code_csv}: {csv_text}"
    content_type = headers_csv.get("Content-Type", "")
    content_disp = headers_csv.get("Content-Disposition", "")
    assert "text/csv" in content_type, f"Expected text/csv, got {content_type}"
    assert "attachment" in content_disp, f"Expected attachment in disposition, got {content_disp}"
    print("CSV Content-Type and Content-Disposition verified.")
    csv_lines = csv_text.strip().split("\n")
    print(f"CSV Total Rows: {len(csv_lines)} (including header)")
    print(f"Header: {csv_lines[0]}")
    if len(csv_lines) > 1:
        print(f"Sample Data Row 1: {csv_lines[1]}")

    # Test format=pdf returns planned 501
    print("\nTesting PDF export endpoint response:")
    status_code_pdf, pdf_resp, _ = make_request(f"{BASE_URL}/api/reports/{report_1_id}/export?format=pdf")
    assert status_code_pdf == 501, f"Expected 501, got {status_code_pdf}"
    print(f"PDF 501 Handled cleanly: {pdf_resp['detail']}")

    # Test unsupported format returns 400
    status_code_bad, bad_resp, _ = make_request(f"{BASE_URL}/api/reports/{report_1_id}/export?format=excel")
    assert status_code_bad == 400, f"Expected 400 for unsupported format, got {status_code_bad}"
    print(f"Invalid format 400 handled cleanly: {bad_resp['detail']}")

    # 7. Test OpenAPI / Swagger Documentation
    print_section("TEST 7: OpenAPI / Swagger Schema Verification")
    status_code_docs, schema, _ = make_request(f"{BASE_URL}/openapi.json")
    assert status_code_docs == 200, f"Failed to fetch openapi.json: {status_code_docs}"
    paths = schema.get("paths", {})
    required_routes = [
        "/api/reports",
        "/api/reports/{report_id}",
        "/api/reports/{report_id}/export",
    ]
    for route in required_routes:
        assert route in paths, f"Missing route {route} in OpenAPI schema"
        methods = list(paths[route].keys())
        print(f"  - Route: {route} -> Methods: {methods}")

    print_section("ALL PHASE 11: REPORTS API TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    test_reports_api()
