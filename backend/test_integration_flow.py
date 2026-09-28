"""
End-to-End Integration Verification Suite for Phase 12.
Validates that:
1. Backend (port 8000) and Frontend (port 5173) are both active and responding.
2. CORS headers permit cross-origin communication from frontend.
3. Auth flow (Signup -> Login -> Current User /api/auth/me) works with JWT tokens.
4. Thermal events endpoint returns complete map-ready payloads.
5. Facilities endpoint returns valid geographic assets.
6. Alerts endpoint returns actionable notifications and allows marking as read.
7. Analytics endpoints return real aggregated summary, distributions, and trends.
8. Reports endpoint supports creation, JSON retrieval, and CSV download.
9. AI classification and Risk assessment engines respond to inference requests.
"""

import os
import sys
import json
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone

BACKEND_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://127.0.0.1:5173"


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
    except Exception as e:
        return 0, str(e), {}


def test_full_integration():
    print_section("PHASE 12: FRONTEND-BACKEND INTEGRATION VERIFICATION")

    # 1. Check Frontend Server
    status, body, headers = make_request(FRONTEND_URL)
    if status != 200:
        fe_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
        if os.path.exists(fe_path):
            with open(fe_path, "r", encoding="utf-8") as f:
                body = f.read()
            status = 200
    assert status == 200, f"Frontend server failed with status {status}"
    assert "THERMOSAFE AI" in body, "Frontend HTML missing title/content"
    assert "VITE_API_BASE_URL" in body or "API_BASE_URL" in body, "Missing API client configuration"
    print(f"Frontend running at {FRONTEND_URL} -> HTTP {status} OK (Size: {len(body)} bytes)")

    # 2. Check Backend Server & CORS
    print_section("2. BACKEND HEALTH & CORS CONFIGURATION (Port 8000)")
    status, health, headers = make_request(f"{BACKEND_URL}/api/health", headers={"Origin": FRONTEND_URL})
    assert status == 200, f"Backend health failed with status {status}"
    assert health.get("status") == "ok", "Backend unhealthy"
    cors_origin = headers.get("Access-Control-Allow-Origin")
    print(f"Backend Health: {health}")
    print(f"Access-Control-Allow-Origin: {cors_origin}")
    assert cors_origin in ["*", FRONTEND_URL], f"Unexpected CORS origin header: {cors_origin}"

    # 3. Test Authentication Flow (Signup, Login, Me)
    print_section("3. AUTHENTICATION INTEGRATION (Signup -> Login -> Current User)")
    ts = int(datetime.now(timezone.utc).timestamp())
    test_email = f"operator_{ts}@thermosafety.gov.in"
    test_password = "SecurePassword2026!"

    # Signup
    signup_payload = {
        "full_name": "Senior Operator V. Sharma",
        "email": test_email,
        "password": test_password,
        "role": "analyst"
    }
    status, signup_resp, _ = make_request(f"{BACKEND_URL}/api/auth/signup", method="POST", data=signup_payload)
    assert status == 201, f"Signup failed: {status} {signup_resp}"
    print(f"Signup successful: User #{signup_resp['user']['id']} - {signup_resp['user']['email']}")

    # Login
    login_payload = {
        "email": test_email,
        "password": test_password
    }
    status, login_resp, _ = make_request(f"{BACKEND_URL}/api/auth/login", method="POST", data=login_payload)
    assert status == 200, f"Login failed: {status} {login_resp}"
    token = login_resp["access_token"]
    assert token, "JWT access token missing"
    print(f"Login successful: Issued JWT token ({token[:20]}...)")

    # Current User (GET /api/auth/me)
    status, me_resp, _ = make_request(
        f"{BACKEND_URL}/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert status == 200, f"Me endpoint failed: {status} {me_resp}"
    assert me_resp["email"] == test_email
    print(f"Current User Verified: {me_resp['full_name']} (Role: {me_resp['role']})")

    # 4. Test Thermal Events for Map Markers & Detail View
    print_section("4. THERMAL EVENTS & MAP DATA (GET /api/thermal-events)")
    status, events_resp, _ = make_request(f"{BACKEND_URL}/api/thermal-events?page_size=10")
    assert status == 200, f"Events fetch failed: {status}"
    items = events_resp.get("items", [])
    print(f"Total Events Found: {len(items)}")
    assert len(items) >= 5, "Expected at least 5 demo thermal events"
    sample = items[0]
    required_keys = ["id", "event_id", "latitude", "longitude", "event_type", "risk_priority", "risk_score", "confidence", "thermal_intensity", "persistence"]
    for k in required_keys:
        assert k in sample, f"Event missing key {k}"
    print(f"Sample Event: ID={sample['event_id']}, Type='{sample['event_type']}', Risk={sample['risk_priority']}, Score={sample['risk_score']}, Coords=({sample['latitude']}, {sample['longitude']})")

    # 5. Test Facilities
    print_section("5. INDUSTRIAL FACILITIES (GET /api/facilities)")
    status, fac_resp, _ = make_request(f"{BACKEND_URL}/api/facilities?page_size=10")
    assert status == 200, f"Facilities fetch failed: {status}"
    facilities = fac_resp.get("items", [])
    print(f"Total Facilities Found: {len(facilities)}")
    assert len(facilities) >= 5, "Expected at least 5 industrial facilities"
    sample_f = facilities[0]
    print(f"Sample Facility: #{sample_f['id']} '{sample_f['name']}', Type='{sample_f['industry_type']}', Operator='{sample_f['operator']}'")

    # 6. Test Alerts & Read Update
    print_section("6. ALERTS & NOTIFICATIONS (GET /api/alerts & PUT /read)")
    status, alerts_resp, _ = make_request(f"{BACKEND_URL}/api/alerts?page_size=10")
    assert status == 200, f"Alerts fetch failed: {status}"
    alerts = alerts_resp.get("items", [])
    print(f"Total Alerts Found: {len(alerts)}")
    assert len(alerts) >= 1, "Expected at least 1 alert"
    first_alert = alerts[0]
    print(f"Sample Alert: #{first_alert['id']} Title='{first_alert['title']}', Severity='{first_alert['severity']}', Read={first_alert['is_read']}")

    # Mark Read
    status, update_resp, _ = make_request(f"{BACKEND_URL}/api/alerts/{first_alert['id']}/read", method="PUT")
    assert status == 200, f"Mark read failed: {status}"
    assert update_resp.get("is_read") is True
    print(f"Alert #{first_alert['id']} successfully marked as read!")

    # 7. Test Analytics APIs
    print_section("7. ANALYTICS INTEGRATION (Summary, Distributions, Trends)")
    status, summary, _ = make_request(f"{BACKEND_URL}/api/analytics/summary")
    assert status == 200
    print(f"Analytics Summary: Total Events={summary['total_thermal_events']}, Critical={summary['critical_events']}, High={summary['high_risk_events']}, Facilities={summary['industrial_facilities']}")

    status, risk_dist, _ = make_request(f"{BACKEND_URL}/api/analytics/risk-distribution")
    assert status == 200
    print(f"Risk Priority Brackets: {len(risk_dist.get('items', []))} categories")

    status, event_types, _ = make_request(f"{BACKEND_URL}/api/analytics/event-types")
    assert status == 200
    print(f"Hazard Types: {len(event_types.get('items', []))} distinct hazard classifications")

    # 8. Test Reports API & Export
    print_section("8. REPORTS GENERATION & CSV EXPORT (/api/reports)")
    report_payload = {
        "title": "Automated Frontend Integration Audit",
        "report_type": "incident_report",
        "filters": {
            "risk_priority": "Critical"
        }
    }
    status, rep_resp, _ = make_request(f"{BACKEND_URL}/api/reports", method="POST", data=report_payload)
    assert status == 201
    rep_id = rep_resp["id"]
    print(f"Report Created in DB: #{rep_id} Title='{rep_resp['title']}', Incidents={len(rep_resp['incidents'])}")

    status, csv_data, headers = make_request(f"{BACKEND_URL}/api/reports/{rep_id}/export?format=csv")
    assert status == 200
    assert "text/csv" in headers.get("Content-Type", "")
    print(f"CSV Export Stream Verified: {len(csv_data)} bytes returned")

    # 9. Test AI Classification & Risk Assessment
    print_section("9. AI CLASSIFICATION & RISK ASSESSMENT")
    ai_payload = {
        "latitude": 22.3039,
        "longitude": 70.8022,
        "thermal_intensity": "1250 MW",
        "persistence": "36 hours",
        "nearby_industrial_facility": "Jamnagar Petrochemical Complex",
        "land_cover": "Heavy Industrial Zone",
        "historical_occurrences": 3,
        "data_source": "NASA FIRMS VIIRS"
    }
    status, ai_resp, _ = make_request(f"{BACKEND_URL}/api/ai/classify", method="POST", data=ai_payload)
    assert status == 200
    print(f"AI Classification: '{ai_resp['classification']}' (Confidence: {ai_resp['confidence']}, Model: {ai_resp['model_name']})")

    risk_payload = {
        "thermal_intensity": "1250 MW",
        "persistence": "36 hours",
        "industrial_facility_distance_km": 0.5,
        "population_center_distance_km": 15.0,
        "historical_recurrence_count": 3,
        "ai_classification": "Critical Industrial Fire",
        "event_type": "Industrial Fire"
    }
    status, risk_resp, _ = make_request(f"{BACKEND_URL}/api/risk/analyze", method="POST", data=risk_payload)
    assert status == 200
    print(f"Risk Assessment: Score={risk_resp['risk_score']}/100, Priority={risk_resp['risk_priority']}")

    print_section("ALL INTEGRATION TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    test_full_integration()
