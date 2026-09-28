"""
Comprehensive Test Suite for Phase 9: Alert System.
Tests:
1. Low-risk event (no alert created)
2. High-risk event (alert created)
3. Critical event (critical alert created)
4. Alert creation (all required fields present)
5. Unread alerts query
6. Mark alert as read (status lifecycle update)
7. Architecture channel transparency check
"""

import json
import sys
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000/api"

REQUIRED_ALERT_FIELDS = [
    "id",
    "event_id",
    "title",
    "message",
    "severity",
    "risk_score",
    "risk_priority",
    "latitude",
    "longitude",
    "event_type",
    "created_at",
    "is_read",
]


def test_low_risk_event_no_alert():
    print("\n--- TEST 1: Low-Risk Thermal Event (Threshold Not Met) ---")
    url = f"{BASE_URL}/alerts"
    payload = {
        "event_id": "TEST-EVT-LOW",
        "risk_priority": "Low",
        "risk_score": 14.5,
        "event_type": "Low-Risk Thermal Activity",
        "latitude": 22.3595,
        "longitude": 82.6801,
        "thermal_intensity": "25 MW",
        "facility_name": "Korba Buffer",
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST"
    )
    
    with urllib.request.urlopen(req, timeout=10) as resp:
        status = resp.status
        data = json.loads(resp.read().decode("utf-8"))
        
    assert status == 200, f"Expected 200, got {status}"
    assert data.get("alert_created") is False, "Low-risk event must NOT trigger an alert"
    assert data.get("alert") is None
    print(f"Status: {status} OK")
    print(f"Result: alert_created={data.get('alert_created')}")
    print(f"Message: {data.get('message')}")
    print("[PASS] Low-risk event correctly skipped alert creation.")


def test_high_risk_event_creates_alert():
    print("\n--- TEST 2: High-Risk Thermal Event (Alert Created) ---")
    url = f"{BASE_URL}/alerts"
    payload = {
        "event_id": "TEST-EVT-HIGH",
        "risk_priority": "High",
        "risk_score": 68.5,
        "event_type": "High-Risk Thermal Event",
        "latitude": 21.1124,
        "longitude": 72.6582,
        "thermal_intensity": "680 MW",
        "facility_name": "Hazira Chemical Hub",
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST"
    )
    
    with urllib.request.urlopen(req, timeout=10) as resp:
        status = resp.status
        data = json.loads(resp.read().decode("utf-8"))
        
    assert status == 201, f"Expected 201 Created, got {status}"
    assert data["severity"] == "High"
    assert data["risk_priority"] == "High"
    assert data["risk_score"] == 68.5
    assert data["event_id"] == "TEST-EVT-HIGH"
    assert data["is_read"] is False
    print(f"Status: {status} Created")
    print(f"Alert ID: {data['id']}, Title: {data['title']}")
    print(f"Severity: {data['severity']}, Risk Priority: {data['risk_priority']}")
    print("[PASS] High-risk event correctly generated and persisted an alert.")
    return data["id"]


def test_critical_event_creates_alert():
    print("\n--- TEST 3: Critical Thermal Event (Critical Alert Created) ---")
    url = f"{BASE_URL}/alerts"
    payload = {
        "event_id": "TEST-EVT-CRITICAL",
        "risk_priority": "Critical",
        "risk_score": 96.5,
        "event_type": "Critical Industrial Fire",
        "latitude": 22.3039,
        "longitude": 70.8022,
        "thermal_intensity": "1250 MW",
        "facility_name": "Jamnagar Petrochemical Complex",
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST"
    )
    
    with urllib.request.urlopen(req, timeout=10) as resp:
        status = resp.status
        data = json.loads(resp.read().decode("utf-8"))
        
    assert status == 201, f"Expected 201 Created, got {status}"
    assert data["severity"] == "Critical"
    assert data["risk_priority"] == "Critical"
    assert data["risk_score"] == 96.5
    assert data["event_id"] == "TEST-EVT-CRITICAL"
    assert data["is_read"] is False
    print(f"Status: {status} Created")
    print(f"Alert ID: {data['id']}, Title: {data['title']}")
    print(f"Severity: {data['severity']}, Risk Score: {data['risk_score']}")
    print("[PASS] Critical event correctly generated an emergency critical alert.")
    return data["id"]


def test_alert_creation_and_field_verification():
    print("\n--- TEST 4: Direct Alert Creation & All Required Fields Verification ---")
    url = f"{BASE_URL}/alerts"
    payload = {
        "title": "EMERGENCY: Hydrocracker Runaway Reaction",
        "message": "Thermal anomaly exceeding critical threshold detected at Unit 3.",
        "severity": "Critical",
        "risk_score": 98.0,
        "risk_priority": "Critical",
        "latitude": 22.3039,
        "longitude": 70.8022,
        "event_type": "Refinery Hazard",
        "event_id": "DEMO-ALERT-DIRECT-001",
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST"
    )
    
    with urllib.request.urlopen(req, timeout=10) as resp:
        status = resp.status
        data = json.loads(resp.read().decode("utf-8"))
        
    assert status == 201, f"Expected 201, got {status}"
    
    # Verify all 12 required fields
    for field in REQUIRED_ALERT_FIELDS:
        assert field in data, f"Required field '{field}' missing from alert response!"
        print(f"  Field check [{field}]: {data[field]}")
        
    assert data["is_read"] is False
    print("[PASS] Alert successfully created with all 12 required telemetry fields present.")
    return data["id"]


def test_unread_alerts():
    print("\n--- TEST 5: Query Unread Alerts (GET /api/alerts/unread) ---")
    url = f"{BASE_URL}/alerts/unread"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    
    with urllib.request.urlopen(req, timeout=10) as resp:
        status = resp.status
        data = json.loads(resp.read().decode("utf-8"))
        
    assert status == 200, f"Expected 200, got {status}"
    assert "unread_count" in data
    assert "items" in data
    assert data["unread_count"] > 0, "Expected at least 1 unread alert"
    assert len(data["items"]) > 0
    
    for item in data["items"]:
        assert item["is_read"] is False, f"Alert {item['id']} returned in unread list but is_read is True!"
        
    print(f"Status: {status} OK")
    print(f"Total Unread Alerts: {data['unread_count']}")
    print(f"Retrieved Unread Items: {len(data['items'])}")
    print("[PASS] Unread alerts endpoint correctly returns only active unread alerts.")
    return data["items"][0]["id"], data["unread_count"]


def test_mark_alert_as_read(alert_id_to_read, initial_unread_count):
    print(f"\n--- TEST 6: Mark Alert as Read (PUT /api/alerts/{alert_id_to_read}/read) ---")
    url = f"{BASE_URL}/alerts/{alert_id_to_read}/read"
    req = urllib.request.Request(
        url,
        data=b"{}",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="PUT"
    )
    
    with urllib.request.urlopen(req, timeout=10) as resp:
        status = resp.status
        data = json.loads(resp.read().decode("utf-8"))
        
    assert status == 200, f"Expected 200, got {status}"
    assert data["id"] == alert_id_to_read
    assert data["is_read"] is True, f"Alert {alert_id_to_read} should now have is_read=True!"
    print(f"Status: {status} OK")
    print(f"Alert ID: {data['id']}, is_read={data['is_read']}")
    
    # Verify unread count decremented
    unread_url = f"{BASE_URL}/alerts/unread"
    with urllib.request.urlopen(unread_url, timeout=10) as resp2:
        data2 = json.loads(resp2.read().decode("utf-8"))
        
    assert data2["unread_count"] == initial_unread_count - 1, (
        f"Expected unread count {initial_unread_count - 1}, got {data2['unread_count']}"
    )
    print(f"New Unread Count: {data2['unread_count']} (decremented from {initial_unread_count})")
    print("[PASS] Alert successfully marked as read; unread count properly decremented.")


def test_multi_channel_architecture_honesty():
    print("\n--- TEST 7: Multi-Channel Architecture & Push Service Transparency Check ---")
    from app.services.notification_service import get_notification_service
    
    dispatcher = get_notification_service()
    channels = dispatcher.channels
    
    print(f"Registered channels: {list(channels.keys())}")
    assert "database" in channels
    assert "fcm" in channels
    assert "web_push" in channels
    assert "email" in channels
    assert "sms" in channels
    
    assert channels["database"].is_active is True
    assert channels["fcm"].is_active is False, "FCM channel must be inactive until real credentials are provided"
    assert channels["web_push"].is_active is False
    assert channels["email"].is_active is False
    assert channels["sms"].is_active is False
    
    print("Channel status:")
    for name, chan in channels.items():
        print(f"  - {name}: active={chan.is_active} (channel_name='{chan.channel_name}')")
        
    print("[PASS] Complied with requirement: 'Do not claim mobile push notifications are fully implemented until a real push service is configured and tested.'")


def test_get_all_alerts():
    print("\n--- TEST 8: List All Alerts with Pagination (GET /api/alerts) ---")
    url = f"{BASE_URL}/alerts?page=1&page_size=10"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    
    with urllib.request.urlopen(req, timeout=10) as resp:
        status = resp.status
        data = json.loads(resp.read().decode("utf-8"))
        
    assert status == 200
    assert data["total"] >= 3
    assert len(data["items"]) > 0
    print(f"Total alerts in DB: {data['total']}")
    print(f"Page size: {data['page_size']}, Total pages: {data['total_pages']}")
    print(f"Sample Alert: ID={data['items'][0]['id']}, Severity={data['items'][0]['severity']}, Read={data['items'][0]['is_read']}")
    print("[PASS] GET /api/alerts returns paginated alert history successfully.")


if __name__ == "__main__":
    print("=" * 70)
    print("RUNNING PHASE 9: ALERT SYSTEM VERIFICATION SUITE")
    print("=" * 70)
    
    try:
        test_low_risk_event_no_alert()
        high_id = test_high_risk_event_creates_alert()
        crit_id = test_critical_event_creates_alert()
        created_id = test_alert_creation_and_field_verification()
        alert_to_read, unread_count = test_unread_alerts()
        test_mark_alert_as_read(alert_to_read, unread_count)
        test_multi_channel_architecture_honesty()
        test_get_all_alerts()
        
        print("\n" + "=" * 70)
        print("ALL PHASE 9 TESTS PASSED (100% SUCCESS)")
        print("=" * 70)
    except AssertionError as ae:
        print(f"\n[FAIL] Assertion Error: {ae}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
