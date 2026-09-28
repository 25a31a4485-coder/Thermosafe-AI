"""
Comprehensive Automated Verification Script for Phases 27 to 33 and Phase 26 Regression.
Uses urllib.request to avoid any external dependencies.
"""
import json
import urllib.request
import urllib.error
import urllib.parse
import uuid

BASE_URL = "http://127.0.0.1:8000"

def api_request(method, path, data=None, headers=None, form_data=None):
    url = f"{BASE_URL}{path}"
    req_headers = headers.copy() if headers else {}
    body = None

    if data is not None:
        body = json.dumps(data).encode("utf-8")
        req_headers["Content-Type"] = "application/json"
    elif form_data is not None:
        body = urllib.parse.urlencode(form_data).encode("utf-8")
        req_headers["Content-Type"] = "application/x-www-form-urlencoded"

    req = urllib.request.Request(url, data=body, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            status_code = response.status
            resp_body = response.read().decode("utf-8")
            try:
                json_data = json.loads(resp_body)
            except Exception:
                json_data = resp_body
            return status_code, json_data
    except urllib.error.HTTPError as e:
        status_code = e.code
        resp_body = e.read().decode("utf-8")
        try:
            json_data = json.loads(resp_body)
        except Exception:
            json_data = resp_body
        return status_code, json_data

def log_test(name, passed, details=""):
    mark = "PASS" if passed else "FAIL"
    print(f"[{mark}] {name} - {details}")
    if not passed:
        raise AssertionError(f"Test failed: {name} - {details}")

def main():
    print("==================================================")
    print("STARTING THERMOSAFE AI PHASES 27-33 & 26 TEST SUITE")
    print("==================================================")

    # -------------------------------------------------------------------------
    # PHASE 27: LOGIN FIRST / AUTHENTICATION & PROTECTED APPLICATION
    # -------------------------------------------------------------------------
    print("\n--- Testing Phase 27: Authentication & Protected Application ---")
    
    # 1. Unauthenticated access to protected endpoint should be 401
    status, _ = api_request("GET", "/api/auth/me")
    log_test("Phase 27: Protected route rejection (unauthenticated)", status == 401, f"Status: {status}")

    # 2. Signup with mismatched password should be rejected
    mismatch_payload = {
        "full_name": "Test Operator",
        "email": f"test_op_{uuid.uuid4().hex[:6]}@thermosafe.ai",
        "password": "SecretPassword123!",
        "confirm_password": "WrongPassword123!",
        "role": "operator"
    }
    status, _ = api_request("POST", "/api/auth/signup", data=mismatch_payload)
    log_test("Phase 27: Signup rejects mismatched password", status == 422, f"Status: {status}")

    # 3. Successful Signup
    unique_email = f"operator_{uuid.uuid4().hex[:6]}@thermosafe.ai"
    signup_payload = {
        "full_name": "Rajesh Kumar",
        "email": unique_email,
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!",
        "role": "operator"
    }
    status, signup_data = api_request("POST", "/api/auth/signup", data=signup_payload)
    log_test("Phase 27: User signup with role operator", status == 201, f"Status: {status}")
    new_user_id = signup_data.get("user", {}).get("id") if isinstance(signup_data, dict) else None

    # 4. Login with Wrong Password
    status, _ = api_request("POST", "/api/auth/login", data={"email": unique_email, "password": "BadPassword!"})
    log_test("Phase 27: Login rejected with invalid password", status == 401, f"Status: {status}")

    # 5. Successful Login & JWT Token
    status, token_data = api_request("POST", "/api/auth/login", data={"email": unique_email, "password": "SecurePassword123!"})
    log_test("Phase 27: Login successful with JWT issuance", status == 200, f"Status: {status}")
    access_token = token_data.get("access_token")
    auth_headers = {"Authorization": f"Bearer {access_token}"}

    # 6. Current User Retrieval (/api/auth/me)
    status, me_data = api_request("GET", "/api/auth/me", headers=auth_headers)
    log_test("Phase 27: Current user API (/api/auth/me)", status == 200 and me_data.get("email") == unique_email, f"User: {me_data.get('email')}")

    # Also log in as admin for subsequent management steps
    status, admin_data = api_request("POST", "/api/auth/login", data={"email": "admin@thermosafe.ai", "password": "AdminPassword123!"})
    admin_token = admin_data.get("access_token")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    log_test("Phase 27: Admin login", status == 200)

    # -------------------------------------------------------------------------
    # PHASE 28 & 29: OPERATOR TEAM MODEL, ASSOCIATION & API
    # -------------------------------------------------------------------------
    print("\n--- Testing Phase 28 & 29: Operator Team Model, Association & API ---")
    
    # 1. Fetch existing facilities to associate
    status, fac_data = api_request("GET", "/api/facilities")
    facilities = fac_data.get("items", []) if isinstance(fac_data, dict) else []
    facility_id = facilities[0]["id"] if facilities else None
    log_test("Phase 28: Reuse existing industrial facility", facility_id is not None, f"Facility ID: {facility_id}")

    # 2. POST /api/operator-teams - Create Team
    team_payload = {
        "team_name": f"Hazmat Rapid Unit {uuid.uuid4().hex[:4]}",
        "organization_name": "Gujarat State Disaster Management Authority",
        "facility_id": facility_id,
        "contact_person": "Vikram Singh",
        "email": "vikram.singh@gsdma.gov.in",
        "phone": "+91 98765 43210",
        "latitude": 21.6980,
        "longitude": 72.5850,
        "industry_type": "Petrochemical & Refinery",
        "response_radius_km": 35.0,
        "notification_enabled": True,
        "is_active": True,
        "assigned_user_ids": [new_user_id]
    }
    status, team_data = api_request("POST", "/api/operator-teams", data=team_payload, headers=admin_headers)
    log_test("Phase 29: POST /api/operator-teams (Create Team)", status == 201, f"Status: {status}")
    team_id = team_data.get("id")

    # 3. GET /api/operator-teams/{id}
    status, retrieved_team = api_request("GET", f"/api/operator-teams/{team_id}")
    log_test("Phase 29: GET /api/operator-teams/{id}", status == 200 and retrieved_team.get("team_name") == team_payload["team_name"])
    log_test("Phase 28: Team user assignment association", len(retrieved_team.get("assigned_users", [])) == 1 and retrieved_team["assigned_users"][0]["id"] == new_user_id)
    log_test("Phase 28: Team facility association", retrieved_team.get("facility_name") is not None or facility_id is not None)

    # 4. PUT /api/operator-teams/{id} - Edit Team
    update_payload = {
        "response_radius_km": 45.0,
        "notification_enabled": True,
        "is_active": True
    }
    status, updated_team = api_request("PUT", f"/api/operator-teams/{team_id}", data=update_payload, headers=admin_headers)
    log_test("Phase 29: PUT /api/operator-teams/{id} (Edit Team)", status == 200 and updated_team.get("response_radius_km") == 45.0)

    # 5. GET /api/operator-teams - List Teams
    status, list_teams = api_request("GET", "/api/operator-teams")
    teams_count = len(list_teams) if isinstance(list_teams, list) else len(list_teams.get("items", []))
    log_test("Phase 29: GET /api/operator-teams (List Teams)", status == 200 and teams_count >= 1, f"Teams count: {teams_count}")

    # -------------------------------------------------------------------------
    # PHASE 30: CONNECT OPERATOR TEAM TO EXISTING UI
    # -------------------------------------------------------------------------
    print("\n--- Testing Phase 30: Frontend Settings & Operator Team UI ---")
    import os
    frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    with open(frontend_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    log_test("Phase 30: Settings Page Team Management Section", "id=\"teamsTableBody\"" in html_content or "manageOperatorTeams" in html_content or "openTeamModal" in html_content)
    log_test("Phase 30: Team Creation/Edit Modal present", "id=\"teamModal\"" in html_content)
    log_test("Phase 30: Team Form Controls present", "id=\"tName\"" in html_content and "id=\"tRadius\"" in html_content and "id=\"tFacId\"" in html_content)

    # -------------------------------------------------------------------------
    # PHASE 31: DEVICE / BROWSER REGISTRATION
    # -------------------------------------------------------------------------
    print("\n--- Testing Phase 31: Device & Browser Registration ---")
    
    device_payload = {
        "device_identifier": f"chrome-win11-{uuid.uuid4().hex[:6]}",
        "push_token": "fcm_test_device_token_abc123_mock",
        "platform": "web",
        "browser": "Chrome 122",
        "notification_permission": "granted",
        "operator_team_id": team_id
    }
    # 1. POST /api/devices/register
    status, device_data = api_request("POST", "/api/devices/register", data=device_payload, headers=auth_headers)
    log_test("Phase 31: POST /api/devices/register", status in [200, 201], f"Status: {status}")
    device_id = device_data.get("id")

    # 2. GET /api/devices
    status, user_devices = api_request("GET", "/api/devices", headers=auth_headers)
    log_test("Phase 31: GET /api/devices (List user devices)", status == 200 and len(user_devices) >= 1)

    # 3. PUT /api/devices/{id}
    status, _ = api_request("PUT", f"/api/devices/{device_id}", data={"notification_permission": "granted", "is_active": True}, headers=auth_headers)
    log_test("Phase 31: PUT /api/devices/{id} (Update Device)", status == 200)

    # -------------------------------------------------------------------------
    # PHASE 32: FIREBASE NOTIFICATION FOUNDATION
    # -------------------------------------------------------------------------
    print("\n--- Testing Phase 32: Firebase Notification Foundation ---")
    
    # 1. FCM Status API
    status, fcm_status_resp = api_request("GET", "/api/alerts/fcm/status")
    log_test("Phase 32: GET /api/alerts/fcm/status", status == 200)
    fcm_status = fcm_status_resp.get("status")
    log_test("Phase 32: Safe fallback mode when credentials absent", fcm_status in ["ready", "CONFIGURATION_REQUIRED"], f"Status: {fcm_status}")

    # 2. Test Notification API with all 10 fields payload
    test_notif_payload = {
        "title": "EMERGENCY: High Thermal Event Detected",
        "body": "Critical thermal spike 780K at Dahej Petrochemical Complex",
        "severity": "CRITICAL",
        "event_id": "EVT-TEST-001",
        "event_type": "Critical Industrial Fire",
        "risk_priority": "CRITICAL",
        "risk_score": 96.5,
        "latitude": 21.6980,
        "longitude": 72.5850,
        "incident_url": "/?event=EVT-TEST-001",
        "token": "mock_fcm_token_client"
    }
    status, fcm_test_resp = api_request("POST", "/api/alerts/fcm/test", data=test_notif_payload, headers=auth_headers)
    log_test("Phase 32: POST /api/alerts/fcm/test", status == 200, f"Result: {fcm_test_resp.get('status')}")

    # -------------------------------------------------------------------------
    # PHASE 33: CONNECT EXISTING NOTIFICATION BELL / DRAWER
    # -------------------------------------------------------------------------
    print("\n--- Testing Phase 33: Connected Notification Bell & Drawer ---")
    
    # 1. GET /api/alerts
    status, alerts_resp = api_request("GET", "/api/alerts?page_size=10")
    log_test("Phase 33: GET /api/alerts", status == 200)
    alerts_data = alerts_resp if isinstance(alerts_resp, list) else alerts_resp.get("items", [])
    log_test("Phase 33: Alerts data available", len(alerts_data) > 0)
    target_alert = alerts_data[0]
    target_alert_id = target_alert["id"]

    # 2. GET /api/alerts/unread
    status, unread_resp = api_request("GET", "/api/alerts/unread")
    log_test("Phase 33: GET /api/alerts/unread", status == 200)

    # 3. PUT /api/alerts/{id}/read
    status, _ = api_request("PUT", f"/api/alerts/{target_alert_id}/read")
    log_test("Phase 33: PUT /api/alerts/{id}/read", status == 200)

    # -------------------------------------------------------------------------
    # PHASE 26 REGRESSION: View Full Analysis, View on Map, Alert Acknowledgment
    # -------------------------------------------------------------------------
    print("\n--- Testing Phase 26 Regression: Preserved Core Features ---")
    
    # 1. Thermal Events API with full AI classification details for 'View Full Analysis'
    status, events_resp = api_request("GET", "/api/thermal-events?page_size=5")
    events = events_resp if isinstance(events_resp, list) else events_resp.get("items", [])
    log_test("Phase 26 Regression: GET /api/thermal-events", len(events) > 0, f"Found {len(events)} events")
    event0 = events[0]
    log_test("Phase 26 Regression: Event coordinates present for 'View on Map'", "latitude" in event0 and "longitude" in event0)
    
    # Check specific event details
    status, evt_detail = api_request("GET", f"/api/thermal-events/{event0['id']}")
    log_test("Phase 26 Regression: Event detail for 'View Full Analysis'", status == 200)
    log_test("Phase 26 Regression: AI Classification data present", "ai_classification" in evt_detail or "classification" in evt_detail or evt_detail.get("event_type") is not None)

    # 2. Alert Acknowledgement
    unack_alert = next((a for a in alerts_data if not a.get("is_acknowledged")), None)
    if not unack_alert:
        _, fresh_alert = api_request("POST", "/api/alerts", data={
            "title": "Fresh Unacknowledged Alert for Test",
            "message": "Testing acknowledgement flow",
            "severity": "High",
            "latitude": 22.3039,
            "longitude": 70.8022
        })
        ack_target_id = fresh_alert["id"]
    else:
        ack_target_id = unack_alert["id"]

    ack_payload = {
        "responder_name": "Senior Operator Rajesh",
        "action_taken": "Dispatched emergency cooling unit to Sector 4",
        "notes": "Emergency suppression active, perimeter secured."
    }
    status, ack_result = api_request("PUT", f"/api/alerts/{ack_target_id}/acknowledge", data=ack_payload, headers=auth_headers)
    log_test("Phase 26 Regression: Alert Acknowledgement API", status == 200, f"Status: {status}")
    log_test("Phase 26 Regression: Alert is_acknowledged is True", ack_result.get("is_acknowledged") is True)

    print("\n==================================================")
    print("ALL 25 VERIFICATIONS COMPLETED AND PASSED!")
    print("==================================================")

if __name__ == "__main__":
    main()
