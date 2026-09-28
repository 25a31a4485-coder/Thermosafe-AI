"""
Verification script for Phase 26 fixes:
- View Full Analysis
- View on Map from Alerts
- Alert Acknowledgement with Operator Details
- Parity between frontend/index.html and index.html
"""
import urllib.request
import json
import os
import sys

BASE_URL = "http://127.0.0.1:8000"

def run_tests():
    print("=" * 70)
    print("PHASE 26 VERIFICATION TEST SUITE")
    print("=" * 70)

    # 1. Test Backend Health
    print("\n--- TEST 1: Backend Health Check ---")
    try:
        health_req = urllib.request.urlopen(f"{BASE_URL}/api/health")
        health = json.loads(health_req.read().decode())
        assert health["status"] == "ok"
        print("[PASS] Backend is running and healthy.")
    except Exception as e:
        print(f"[FAIL] Backend health failed: {e}")
        return False

    # 2. Test Thermal Events Data for "View Full Analysis"
    print("\n--- TEST 2: Thermal Events Full Analysis Data Attributes ---")
    try:
        events_req = urllib.request.urlopen(f"{BASE_URL}/api/thermal-events?page_size=10")
        events_data = json.loads(events_req.read().decode())
        items = events_data.get("items", [])
        assert len(items) > 0, "No thermal events found in backend"
        sample_ev = items[0]

        # Verify all 14 required analysis fields exist in event data
        required_fields = [
            "id", "latitude", "longitude", "event_type",
            "thermal_intensity", "persistence", "confidence",
            "risk_score", "risk_priority", "facility_id",
            "data_source", "detected_at"
        ]
        for field in required_fields:
            assert field in sample_ev, f"Missing required field: {field}"
            print(f"  * Field [{field}]: {sample_ev[field]}")

        print(f"[PASS] Thermal event {sample_ev.get('event_id', sample_ev['id'])} provides all required analysis attributes.")
    except Exception as e:
        print(f"[FAIL] Thermal events analysis data check failed: {e}")
        return False

    # 3. Test Alerts & "View on Map" Linkage
    print("\n--- TEST 3: Alerts -> Event Linking for 'View on Map' ---")
    try:
        alerts_req = urllib.request.urlopen(f"{BASE_URL}/api/alerts?page_size=10")
        alerts_data = json.loads(alerts_req.read().decode())
        alert_items = alerts_data.get("items", [])
        sample_alert = next((a for a in alert_items if a.get("event_id") or a.get("thermal_event_id")), alert_items[0])

        print(f"  * Alert ID: {sample_alert['id']}")
        print(f"  * Alert Title: {sample_alert['title']}")
        print(f"  * Associated Event ID: {sample_alert.get('event_id')}")
        print(f"  * Associated Thermal DB ID: {sample_alert.get('thermal_event_id')}")
        print(f"  * Coordinates: ({sample_alert.get('latitude')}, {sample_alert.get('longitude')})")

        # Verify that either event_id or thermal_event_id is present
        assert sample_alert.get("event_id") or sample_alert.get("thermal_event_id"), "Alert has no event reference"
        print("[PASS] Alert contains valid incident references for map navigation.")
    except Exception as e:
        print(f"[FAIL] Alerts event linking check failed: {e}")
        return False

    # 4. Test Alert Acknowledgement API
    print("\n--- TEST 4: Alert Acknowledgement Endpoint (PUT /api/alerts/{id}/acknowledge) ---")
    try:
        target_alert = next((a for a in alert_items if not a.get("is_acknowledged")), None)
        if not target_alert:
            create_payload = json.dumps({
                "title": "TEST: Fresh Acknowledgement Candidate",
                "message": "Testing acknowledgement flow",
                "severity": "High",
                "latitude": 22.3039,
                "longitude": 70.8022
            }).encode("utf-8")
            c_req = urllib.request.Request(
                f"{BASE_URL}/api/alerts",
                data=create_payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            target_alert = json.loads(urllib.request.urlopen(c_req).read().decode())
        target_alert_id = target_alert["id"]
        ack_payload = json.dumps({"operator_name": "Commander Rajesh V."}).encode("utf-8")
        req = urllib.request.Request(
            f"{BASE_URL}/api/alerts/{target_alert_id}/acknowledge",
            data=ack_payload,
            headers={"Content-Type": "application/json"},
            method="PUT"
        )
        ack_resp = json.loads(urllib.request.urlopen(req).read().decode())

        assert ack_resp["id"] == target_alert_id
        assert ack_resp["is_acknowledged"] is True
        assert ack_resp["is_read"] is True
        assert ack_resp["acknowledged_by"] == "Commander Rajesh V."
        assert ack_resp["acknowledged_at"] is not None

        print(f"  * Acknowledged ID: {ack_resp['id']}")
        print(f"  * Acknowledged By: {ack_resp['acknowledged_by']}")
        print(f"  * Acknowledged At: {ack_resp['acknowledged_at']}")
        print(f"  * Status: is_acknowledged={ack_resp['is_acknowledged']}, is_read={ack_resp['is_read']}")
        print(f"  * Severity: {ack_resp['severity']}")
        print(f"  * Risk Priority: {ack_resp['risk_priority']}")
        print(f"  * Risk Score: {ack_resp['risk_score']}")
        print(f"  * Coordinates: ({ack_resp['latitude']}, {ack_resp['longitude']})")
        print("[PASS] Alert acknowledgement successfully persisted and verified.")
    except Exception as e:
        print(f"[FAIL] Alert acknowledgement API test failed: {e}")
        return False

    # 5. Test Operator Teams Endpoint
    print("\n--- TEST 5: Operator Teams Proximity Endpoint (GET /api/operator-teams/nearby) ---")
    try:
        lat = sample_ev.get("latitude", 22.3039)
        lng = sample_ev.get("longitude", 70.8022)
        teams_req = urllib.request.urlopen(f"{BASE_URL}/api/operator-teams/nearby?latitude={lat}&longitude={lng}&radius_km=100")
        teams_data = json.loads(teams_req.read().decode())
        items = teams_data.get("items") or teams_data.get("nearby_teams") or []
        print(f"  * Found {len(items)} teams within 100km radius.")
        if items:
            match = items[0]
            t = match.get("team", match)
            dist = match.get("distance_km", 0)
            print(f"  * Closest Team: {t['name']} ({dist:.1f} km away)")
        print("[PASS] Nearby operator team proximity query successful.")
    except Exception as e:
        print(f"[FAIL] Operator teams endpoint failed: {e}")
        return False

    # 6. Verify Frontend Parity and Functions
    print("\n--- TEST 6: Frontend Parity & Handler Verification ---")
    frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html"))
    root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "index.html"))

    assert os.path.exists(frontend_path), f"frontend/index.html not found at {frontend_path}"
    assert os.path.exists(root_path), f"index.html not found at {root_path}"

    with open(frontend_path, "r", encoding="utf-8") as f:
        fe_content = f.read()
    with open(root_path, "r", encoding="utf-8") as f:
        root_content = f.read()

    assert fe_content == root_content, "frontend/index.html and root index.html must be identical in parity"
    print("[PASS] Exact parity verified between frontend/index.html and index.html.")

    # Check key functions in frontend script
    required_handlers = [
        "viewFullAnalysis",
        "openAnalysisModal",
        "closeAnalysisModal",
        "viewAlertOnMap",
        "openAcknowledgementModal",
        "closeAckModal",
        "showAckDetails",
        "acknowledge",
        "analysisModal",
        "ackModal"
    ]
    for handler in required_handlers:
        assert handler in fe_content, f"Missing handler {handler} in frontend script"
        print(f"  * Handler present: {handler}")

    print("[PASS] All required UI handlers and modals are present in the frontend.")

    print("\n" + "=" * 70)
    print("ALL PHASE 26 VERIFICATION CHECKS PASSED (100% SUCCESS)")
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
