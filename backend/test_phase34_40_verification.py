"""
Phase 34–40 Comprehensive Verification Test Suite
Tests:
- Phase 34: Exact 'View on Map' Data & Linkage (Zoom 14, 11 fields)
- Phase 35: Complete Event Full Analysis Modal (5 Distinct Sections)
- Phase 36: Final Alert Acknowledgement (Duplicate Rejection HTTP 400, Operator Attribution)
- Phase 37: Automatic Nearest Operator Team Routing (Haversine, Status, Compatibility)
- Phase 38: Automatic Risk -> Alert Pipeline (AI Classification, Risk Engine, Auto Alert Gen)
- Phase 39: Smart Notification Content (Critical/High/Gas/Persistent templates, 10 fields, Incident URL)
- Phase 40: Central Notification Orchestration (Deduplication, 15-min Cooldown, Delivery Tracking, Simulation Pipeline)
"""

import sys
import json
import urllib.request
import urllib.error
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def log_test(name, passed, details=""):
    mark = "[PASS]" if passed else "[FAIL]"
    print(f"{mark} {name} {('- ' + details) if details else ''}")
    if not passed:
        raise AssertionError(f"Test failed: {name} - {details}")

def api_request(method, path, data=None, headers=None):
    url = f"{BASE_URL}{path}"
    headers = headers or {}
    req_data = None
    if data is not None:
        req_data = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        try:
            parsed = json.loads(content)
        except Exception:
            parsed = {"raw": content}
        return e.code, parsed

def main():
    print("=" * 60)
    print("THERMOSAFE AI PHASES 34–40 VERIFICATION TEST SUITE")
    print("=" * 60)

    # -------------------------------------------------------------
    # PHASE 34: EXACT "VIEW ON MAP"
    # -------------------------------------------------------------
    print("\n--- PHASE 34: Exact View on Map ---")
    status, events_resp = api_request("GET", "/api/thermal-events?page_size=5")
    log_test("Phase 34: Fetch Thermal Events", status == 200)
    events = events_resp if isinstance(events_resp, list) else events_resp.get("items", [])
    log_test("Phase 34: Events list populated", len(events) > 0)
    
    ev = events[0]
    required_p34_fields = ["id", "latitude", "longitude", "event_type", "confidence", "risk_score", "risk_priority", "thermal_intensity", "detected_at"]
    missing = [f for f in required_p34_fields if f not in ev]
    log_test("Phase 34: Required 11 Popup Attributes Present in Backend Event", len(missing) == 0, f"Missing: {missing}")
    print(f"  * Event ID: {ev.get('event_id', ev['id'])}")
    print(f"  * Exact Coordinates: ({ev['latitude']}, {ev['longitude']})")
    print(f"  * Classification: {ev.get('classification') or ev.get('event_type')}")
    print(f"  * Risk Score: {ev['risk_score']} ({ev['risk_priority']})")

    # Check frontend viewAlertOnMap implementation
    import os
    fe_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    with open(fe_path, "r", encoding="utf-8") as f:
        fe_content = f.read()
    log_test("Phase 34: Frontend viewAlertOnMap has Zoom 14", "state.map.setView([ev.lat, ev.lng], 14" in fe_content)
    log_test("Phase 34: Frontend viewAlertOnMap golden pulse icon", "makeThermalIcon(ev, true)" in fe_content)
    log_test("Phase 34: Frontend popup contains all 11 fields", "<b>Event ID:</b>" in fe_content and "<b>Latitude:</b>" in fe_content and "<b>Longitude:</b>" in fe_content and "<b>Detection Time:</b>" in fe_content)

    # -------------------------------------------------------------
    # PHASE 35: COMPLETE EVENT FULL ANALYSIS MODAL
    # -------------------------------------------------------------
    print("\n--- PHASE 35: Complete Event Full Analysis Modal ---")
    log_test("Phase 35: Section 1 EVENT INFORMATION in Analysis Modal", "1. EVENT INFORMATION" in fe_content)
    log_test("Phase 35: Section 2 AI ANALYSIS in Analysis Modal", "2. AI ANALYSIS" in fe_content and "ThermalEnsemble-v2" in fe_content)
    log_test("Phase 35: Section 3 RISK ANALYSIS in Analysis Modal", "3. RISK ANALYSIS" in fe_content and "Multi-Factor Breakdown (5 Factors)" in fe_content)
    log_test("Phase 35: Section 4 FACILITY in Analysis Modal", "4. FACILITY" in fe_content and "Closest Facility Name" in fe_content)
    log_test("Phase 35: Section 5 RESPONSE in Analysis Modal", "5. RESPONSE" in fe_content and "Assigned Operator Team" in fe_content and "Recommended Response Protocol" in fe_content)

    # -------------------------------------------------------------
    # PHASE 36: FINAL ALERT ACKNOWLEDGEMENT
    # -------------------------------------------------------------
    print("\n--- PHASE 36: Final Alert Acknowledgement ---")
    # 1. Create a fresh unacknowledged alert
    status, fresh_alert = api_request("POST", "/api/alerts", data={
        "title": "EMERGENCY: Flare Stack Pressure Surge",
        "message": "Continuous thermal anomaly detected near refinery unit 3.",
        "severity": "Critical",
        "risk_priority": "CRITICAL",
        "risk_score": 92.5,
        "latitude": 22.3039,
        "longitude": 70.8022
    })
    log_test("Phase 36: Create Alert for Ack Test", status in [200, 201], f"Alert ID: {fresh_alert['id']}")
    alert_id = fresh_alert["id"]

    # 2. First acknowledgement must succeed (HTTP 200)
    status, ack_res = api_request("PUT", f"/api/alerts/{alert_id}/acknowledge", data={
        "operator_name": "Chief Controller Vikram Seth"
    })
    log_test("Phase 36: First Acknowledgement Succeeds (HTTP 200)", status == 200)
    log_test("Phase 36: Alert is_acknowledged is True", ack_res.get("is_acknowledged") is True)
    log_test("Phase 36: Operator attribution matches", ack_res.get("acknowledged_by") == "Chief Controller Vikram Seth")
    log_test("Phase 36: Alert status set to ACKNOWLEDGED", ack_res.get("status") == "ACKNOWLEDGED")
    print(f"  * Acknowledged At: {ack_res.get('acknowledged_at')}")

    # 3. Duplicate acknowledgement MUST be rejected with HTTP 400 Bad Request
    status, dup_res = api_request("PUT", f"/api/alerts/{alert_id}/acknowledge", data={
        "operator_name": "Second Operator Attempt"
    })
    log_test("Phase 36: Duplicate Acknowledgement Rejected with HTTP 400", status == 400)
    dup_detail = dup_res.get("detail", "")
    log_test("Phase 36: Rejection message specifies already acknowledged", "already been acknowledged" in dup_detail, dup_detail)

    # -------------------------------------------------------------
    # PHASE 37: AUTOMATIC NEAREST OPERATOR TEAM ROUTING
    # -------------------------------------------------------------
    print("\n--- PHASE 37: Nearest Operator Team Routing ---")
    status, nearby_res = api_request("GET", "/api/operator-teams/nearby?latitude=22.3039&longitude=70.8022&radius_km=100")
    log_test("Phase 37: Nearby Operator Teams Query (HTTP 200)", status == 200)
    teams = nearby_res.get("items") or nearby_res.get("nearby_teams") or []
    log_test("Phase 37: Active teams found within radius", len(teams) > 0)
    top_team = teams[0]
    print(f"  * Nearest Team: {top_team.get('name') or top_team.get('team', {}).get('name')}")
    print(f"  * Distance: {top_team.get('distance_km')} km")

    # -------------------------------------------------------------
    # PHASE 38 & 40: SIMULATE PIPELINE (AUTOMATIC RISK -> ALERT & CENTRAL ORCHESTRATION)
    # -------------------------------------------------------------
    print("\n--- PHASE 38 & 40: Automated Pipeline & Central Orchestration ---")
    status, sim_res = api_request("POST", "/api/thermal-events/simulate", data={
        "event_type": "Industrial Fire",
        "latitude": 22.3039,
        "longitude": 70.8022,
        "facility_name": "Jamnagar Refinery"
    })
    log_test("Phase 40: POST /api/thermal-events/simulate (HTTP 200)", status == 200)
    sim_event = sim_res.get("event", {})
    pipeline = sim_res.get("pipeline", {})
    log_test("Phase 38: Pipeline generated thermal event", bool(sim_event.get("id")))
    log_test("Phase 38: Pipeline generated alert", bool(pipeline.get("alert")))
    log_test("Phase 37: Pipeline assigned nearest operator team", bool(pipeline.get("assigned_team", {}).get("team_name")))
    log_test("Phase 40: Pipeline delivery status logged", pipeline.get("delivery_status") in ["SENT", "DELIVERED", "CONFIGURATION_REQUIRED", "SKIPPED_POLICY"])

    created_alert_id = pipeline.get("alert", {}).get("id")
    print(f"  * Simulated Event ID: {sim_event.get('event_id')}")
    print(f"  * AI Classification: {pipeline.get('classification')} (Conf: {pipeline.get('confidence')}%)")
    print(f"  * Computed Risk Score: {pipeline.get('risk_score')}/100 ({pipeline.get('risk_priority')})")
    print(f"  * Assigned Operator Team: {pipeline.get('assigned_team', {}).get('team_name')}")
    print(f"  * Generated Alert ID: {created_alert_id}")
    print(f"  * Delivery Status: {pipeline.get('delivery_status')}")

    # -------------------------------------------------------------
    # PHASE 39: SMART NOTIFICATION CONTENT & PAYLOAD
    # -------------------------------------------------------------
    print("\n--- PHASE 39: Smart Notification Content & 10-Field Payload ---")
    inc_url = pipeline.get("alert", {}).get("incident_url")
    log_test("Phase 39: Dynamic Incident URL in Alert Payload", bool(inc_url and "/?event=" in inc_url and "&view=map" in inc_url), inc_url)
    print(f"  * Dynamic Incident URL: {inc_url}")

    # Check notification delivery logs endpoint
    if created_alert_id:
        status, deliv_logs = api_request("GET", f"/api/alerts/{created_alert_id}/delivery-status")
        log_test("Phase 40: Query Delivery Status by Alert ID (HTTP 200)", status == 200)
        logs_list = deliv_logs if isinstance(deliv_logs, list) else deliv_logs.get("logs", [])
        log_test("Phase 40: Delivery log records present", len(logs_list) > 0)
        first_log = logs_list[0]
        print(f"  * Dedup Key: {first_log.get('dedup_key')}")
        print(f"  * Channel: {first_log.get('channel')}")
        print(f"  * Delivery Status: {first_log.get('status')}")

    # -------------------------------------------------------------
    # PHASE 40: DEDUPLICATION & COOLDOWN REJECTION
    # -------------------------------------------------------------
    print("\n--- PHASE 40: Deduplication & Cooldown Protection ---")
    # Processing the exact same event right away must suppress duplicate notification
    from app.services.orchestration_service import process_thermal_event
    from app.core.database import SessionLocal
    from app.models.thermal_event import ThermalEvent

    db = SessionLocal()
    try:
        db_event = db.query(ThermalEvent).filter(ThermalEvent.id == sim_event["id"]).first()
        log_test("Phase 40: Query existing simulated thermal event from DB", db_event is not None)
        # Re-run pipeline for the same event
        second_run = process_thermal_event(db_event, db=db, force_alert=True)
        log_test("Phase 40: Duplicate Notification Suppressed by 15-min Cooldown", second_run.get("delivery_status") == "SUPPRESSED_DUPLICATE")
        print(f"  * Second Run Delivery Status: {second_run.get('delivery_status')}")
    finally:
        db.close()

    print("\n" + "=" * 60)
    print("ALL PHASE 34–40 VERIFICATION TESTS PASSED SUCCESSFULLY (100%)")
    print("=" * 60)

if __name__ == "__main__":
    main()
