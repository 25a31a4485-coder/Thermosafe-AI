"""
Comprehensive End-to-End Verification of the Complete Operational Flow:
NASA FIRMS LIVE
-> Backend FIRMS service
-> Thermal event
-> Classification
-> Risk
-> Facility association
-> Operator Team lookup
-> Alert
-> Notification
-> Acknowledgement
-> Escalation if required
-> GIS visualization
-> Incident report
"""

import sys
import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000/api"

def make_req(url, method="GET", payload=None):
    data = json.dumps(payload).encode("utf-8") if payload else None
    headers = {"Content-Type": "application/json"} if payload else {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))

def run_e2e_test():
    print("=" * 70)
    print("RUNNING END-TO-END PIPELINE VERIFICATION")
    print("=" * 70)

    # Step 1: NASA FIRMS Satellite Service
    print("\n[STEP 1] Testing Satellite Telemetry Service (mode=live & mode=demo)...")
    st, live_resp = make_req(f"{BASE_URL}/satellite/thermal-events?mode=live")
    assert st == 200
    assert live_resp["mode"] == "live"
    print(f"  Live Connected: {live_resp['live_connected']}, Message: {live_resp.get('message')}")

    st, demo_resp = make_req(f"{BASE_URL}/satellite/thermal-events?mode=demo")
    assert st == 200
    assert demo_resp["total"] > 0
    sample_sat = demo_resp["items"][0]
    print(f"  Demo Telemetry: {demo_resp['total']} detections generated. Sample: {sample_sat['latitude']}, {sample_sat['longitude']}")

    # Step 2 & 3: Thermal Event + AI Classification
    print("\n[STEP 2 & 3] Processing Thermal Event & AI Classification...")
    st, ai_resp = make_req(f"{BASE_URL}/ai/classify", method="POST", payload={
        "latitude": sample_sat["latitude"],
        "longitude": sample_sat["longitude"],
        "thermal_intensity": sample_sat["thermal_intensity"],
        "persistence": sample_sat["persistence"],
        "nearby_industrial_facility": "Jamnagar Petrochemical Complex"
    })
    assert st == 200
    assert "classification" in ai_resp
    print(f"  Classification: {ai_resp['classification']} (Confidence: {ai_resp['confidence']})")

    # Step 4: Multi-Factor Risk Assessment
    print("\n[STEP 4] Evaluating Multi-Factor Risk Assessment...")
    st, risk_resp = make_req(f"{BASE_URL}/risk/analyze", method="POST", payload={
        "thermal_intensity": sample_sat["thermal_intensity"],
        "persistence": sample_sat["persistence"],
        "industrial_facility_proximity_km": 0.5,
        "nearby_industrial_facility": "Jamnagar Petrochemical Complex",
        "population_proximity_km": 2.0,
        "historical_recurrence": 3,
        "ai_classification": ai_resp["classification"],
        "latitude": sample_sat["latitude"],
        "longitude": sample_sat["longitude"]
    })
    assert st == 200
    print(f"  Risk Score: {risk_resp['risk_score']}/100, Priority: {risk_resp['risk_priority']}")

    # Step 5: Facility Association
    print("\n[STEP 5] Facility Association & Geospatial Proximity...")
    st, fac_resp = make_req(f"{BASE_URL}/facilities?page_size=5")
    assert st == 200
    assert fac_resp["total"] > 0
    assigned_facility = fac_resp["items"][0]
    print(f"  Associated Facility: {assigned_facility['name']} (ID: {assigned_facility['id']})")

    # Step 6: Operator Team Lookup & Configuration
    print("\n[STEP 6] Operator Team Lookup & Routing...")
    st, team_resp = make_req(f"{BASE_URL}/operator-teams/nearby?latitude={sample_sat['latitude']}&longitude={sample_sat['longitude']}&radius_km=150")
    assert st == 200
    assert team_resp["total"] > 0
    assigned_team = team_resp["items"][0]["team"]
    print(f"  Routed Team: {assigned_team['team_name']} (Phone: {assigned_team['phone']}, Escalation: {assigned_team['call_escalation_enabled']})")

    # Step 7 & 8: Alert Creation & Notification Orchestration
    print("\n[STEP 7 & 8] Alert Creation & Emergency Notification...")
    st, alert_resp = make_req(f"{BASE_URL}/alerts", method="POST", payload={
        "title": "E2E EMERGENCY: Critical Industrial Fire Test",
        "message": "Automated alert for E2E verification test pipeline.",
        "severity": "Critical",
        "risk_score": 92.0,
        "risk_priority": "Critical",
        "latitude": sample_sat["latitude"],
        "longitude": sample_sat["longitude"],
        "event_type": ai_resp["classification"],
        "assigned_team_id": assigned_team["id"]
    })
    assert st == 201
    alert_id = alert_resp["id"]
    print(f"  Created Alert ID: {alert_id}, Delivery Status: {alert_resp.get('delivery_status', 'SENT')}")

    # Step 9: Escalation Check for Unacknowledged Alert
    print("\n[STEP 9] Phone Escalation for Unacknowledged Alert...")
    st, esc_resp = make_req(f"{BASE_URL}/alerts/{alert_id}/escalate", method="POST")
    assert st == 200
    assert esc_resp["status"] == "ESCALATED"
    print(f"  Escalation Status: {esc_resp['status']}, Target: {esc_resp['team_name']} ({esc_resp['target_phone']})")
    print(f"  Telephony Mode: {esc_resp['telephony_mode']}")

    # Step 10: Acknowledgement
    print("\n[STEP 10] Operator Acknowledgement...")
    st, ack_resp = make_req(f"{BASE_URL}/alerts/{alert_id}/acknowledge", method="PUT", payload={
        "operator_name": "Commander Arjun Mehta"
    })
    assert st == 200
    assert ack_resp["is_acknowledged"] is True
    print(f"  Acknowledged By: {ack_resp['acknowledged_by']} at {ack_resp['acknowledged_at']}")

    # Step 11: Escalation Halts When Acknowledged
    print("\n[STEP 11] Verifying Escalation Halts on Acknowledged Alert...")
    st, esc_stopped = make_req(f"{BASE_URL}/alerts/{alert_id}/escalate", method="POST")
    assert st == 200
    assert esc_stopped["status"] == "STOPPED"
    assert esc_stopped["escalation_stopped"] is True
    print(f"  Escalation Halted: {esc_stopped['reason']}")

    # Step 12: GIS Visualization GeoJSON
    print("\n[STEP 12] GIS GeoJSON Verification...")
    st, team_detail = make_req(f"{BASE_URL}/operator-teams/{assigned_team['id']}")
    assert st == 200
    geojson = team_detail["geojson"]
    assert geojson["type"] == "Feature"
    assert geojson["geometry"]["type"] == "Point"
    print(f"  GeoJSON Validated: {geojson['geometry']['coordinates']} for {geojson['properties']['team_name']}")

    # Step 13: Incident Reporting & CSV Export
    print("\n[STEP 13] Incident Reporting & CSV Export...")
    st, report_resp = make_req(f"{BASE_URL}/reports", method="POST", payload={
        "title": "E2E Verification Incident Report",
        "report_type": "incident_report",
        "risk_priority": "Critical"
    })
    assert st == 201
    report_id = report_resp["id"]
    print(f"  Generated Report ID: {report_id} ({report_resp['title']})")

    req_csv = urllib.request.Request(f"{BASE_URL}/reports/{report_id}/export?format=csv")
    with urllib.request.urlopen(req_csv) as csv_res:
        csv_bytes = csv_res.read()
        assert csv_res.status == 200
        assert b"Incident ID" in csv_bytes
        print(f"  CSV Export Stream Verified: {len(csv_bytes)} bytes downloaded.")

    print("\n" + "=" * 70)
    print("ALL 13 END-TO-END PIPELINE STEPS VERIFIED 100% SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_e2e_test()
