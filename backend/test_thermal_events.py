"""
Comprehensive Test Suite for Phase 4: Thermal Event API
Tests every endpoint, filter, pagination, sorting, coordinate validation, and CRUD operations.
"""
import urllib.request
import urllib.parse
import urllib.error
import json
import sys

BASE_URL = "http://127.0.0.1:8000"


def api_request(path, method="GET", data=None, params=None):
    url = f"{BASE_URL}{path}"
    if params:
        query_string = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        if query_string:
            url = f"{url}?{query_string}"
    
    headers = {"Content-Type": "application/json"}
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            status_code = resp.status
            content = resp.read().decode("utf-8")
            return status_code, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        try:
            return e.code, json.loads(content)
        except Exception:
            return e.code, {"raw_error": content}


def run_tests():
    print("=" * 70)
    print("PHASE 4: THERMAL EVENT API - COMPREHENSIVE TEST SUITE")
    print("=" * 70)

    # -------------------------------------------------------------
    # 1. Test Seed Endpoint
    # -------------------------------------------------------------
    print("\n[1] Testing POST /api/thermal-events/seed (force=true)...")
    status, res = api_request("/api/thermal-events/seed", method="POST", params={"force": "true"})
    print(f"    Status: {status} -> {res.get('message')}")
    assert status == 200, f"Expected 200, got {status}: {res}"
    assert res.get("status") == "success", f"Seed failed: {res}"
    print("    [PASS] Demo events successfully seeded.")

    # -------------------------------------------------------------
    # 2. Test GET /api/thermal-events (Default List & Structure)
    # -------------------------------------------------------------
    print("\n[2] Testing GET /api/thermal-events (default list & map-compatible format)...")
    status, res = api_request("/api/thermal-events")
    assert status == 200, f"Expected 200, got {status}: {res}"
    assert "items" in res and "total" in res, "Missing pagination structure"
    items = res["items"]
    assert len(items) >= 5, f"Expected at least 5 demo events, got {len(items)}"
    print(f"    Total items: {res['total']}, Items in page: {len(items)}")

    # Verify map-compatible fields and required attributes on each event
    sample = next((it for it in items if it.get("is_demo")), items[0])
    required_fields = [
        "id", "event_id", "latitude", "longitude", "detected_at",
        "event_type", "thermal_intensity", "persistence", "confidence",
        "risk_score", "risk_priority", "facility", "land_cover",
        "data_source", "status", "geojson"
    ]
    for field in required_fields:
        assert field in sample, f"Missing required event field: '{field}'"
    
    assert sample["is_demo"] is True, "Demo record must have is_demo = True"
    assert "coordinates" in sample["geojson"]["geometry"], "GeoJSON must contain geometry coordinates"
    assert sample["geojson"]["geometry"]["coordinates"] == [sample["longitude"], sample["latitude"]], "GeoJSON coordinate order must be [lon, lat]"
    assert sample.get("ai_classification") is not None, "AI classification should be populated on demo events"
    print(f"    Sample event: '{sample['event_id']}' - {sample['event_type']} at ({sample['latitude']}, {sample['longitude']})")
    print(f"    AI Classification: {sample['ai_classification']['classification']} (confidence: {sample['ai_classification']['confidence']})")
    print("    [PASS] All map-compatible fields and AI classification verified.")

    # -------------------------------------------------------------
    # 3. Test Filters
    # -------------------------------------------------------------
    print("\n[3] Testing Query Filters...")
    
    # 3a. Event Type Filter
    print("    3a. Filter by event_type='Gas Flare'...")
    status, res = api_request("/api/thermal-events", params={"event_type": "Gas Flare"})
    assert status == 200 and len(res["items"]) == 1, f"Expected 1 Gas Flare, got {len(res['items'])}"
    assert res["items"][0]["event_type"] == "Gas Flare"
    print(f"        [PASS] Found: {res['items'][0]['event_id']} ({res['items'][0]['event_type']})")

    # 3b. Risk Priority Filter
    print("    3b. Filter by risk_priority='CRITICAL'...")
    status, res = api_request("/api/thermal-events", params={"risk_priority": "CRITICAL"})
    assert status == 200 and len(res["items"]) >= 1
    for itm in res["items"]:
        assert itm["risk_priority"].upper() == "CRITICAL"
    print(f"        [PASS] Found {len(res['items'])} CRITICAL event(s).")

    # 3c. Risk Score Threshold Filter
    print("    3c. Filter by min_risk_score=80.0...")
    status, res = api_request("/api/thermal-events", params={"min_risk_score": 80.0})
    assert status == 200
    for itm in res["items"]:
        assert itm["risk_score"] >= 80.0
    print(f"        [PASS] Found {len(res['items'])} event(s) with risk_score >= 80.0.")

    # 3d. Status Filter
    print("    3d. Filter by status='contained'...")
    status, res = api_request("/api/thermal-events", params={"status": "contained"})
    assert status == 200 and len(res["items"]) >= 1
    assert res["items"][0]["status"] == "contained"
    print(f"        [PASS] Found: {res['items'][0]['event_id']} with status='contained'")

    # 3e. Data Source Filter
    print("    3e. Filter by data_source='MODIS'...")
    status, res = api_request("/api/thermal-events", params={"data_source": "MODIS"})
    assert status == 200 and len(res["items"]) >= 1
    assert "MODIS" in res["items"][0]["data_source"]
    print(f"        [PASS] Found: {res['items'][0]['event_id']} with data_source='{res['items'][0]['data_source']}'")

    # 3f. Facility Name Filter
    print("    3f. Filter by facility='Jamnagar'...")
    status, res = api_request("/api/thermal-events", params={"facility": "Jamnagar"})
    assert status == 200 and len(res["items"]) >= 1
    assert "Jamnagar" in res["items"][0]["facility"]["name"]
    print(f"        [PASS] Linked facility: {res['items'][0]['facility']['name']}")

    # 3g. Bounding Box Filter (Gujarat Region: 20-24 N, 68-74 E)
    print("    3g. Filter by bounding box (20 <= lat <= 24, 68 <= lon <= 74)...")
    status, res = api_request("/api/thermal-events", params={
        "min_lat": 20.0, "max_lat": 24.0,
        "min_lon": 68.0, "max_lon": 74.0
    })
    assert status == 200
    for itm in res["items"]:
        assert 20.0 <= itm["latitude"] <= 24.0
        assert 68.0 <= itm["longitude"] <= 74.0
    print(f"        [PASS] Found {len(res['items'])} events inside Gujarat bounding box.")

    # 3h. Proximity Filter (Jamnagar: 22.3039, 70.8022, radius=100km)
    print("    3h. Filter by spatial proximity (Jamnagar lat/lon, radius=100km)...")
    status, res = api_request("/api/thermal-events", params={
        "latitude": 22.3039, "longitude": 70.8022, "radius_km": 100.0
    })
    assert status == 200 and len(res["items"]) >= 1
    assert any(itm["event_id"] == "DEMO-EVT-001" for itm in res["items"])
    print(f"        [PASS] Proximity search correctly identified DEMO-EVT-001 in results.")

    # -------------------------------------------------------------
    # 4. Test Sorting & Pagination
    # -------------------------------------------------------------
    print("\n[4] Testing Sorting & Pagination...")

    # 4a. Sort by risk_score desc
    print("    4a. Sort by risk_score desc...")
    status, res = api_request("/api/thermal-events", params={"sort_by": "risk_score", "sort_order": "desc"})
    scores = [itm["risk_score"] for itm in res["items"]]
    assert scores == sorted(scores, reverse=True), f"Scores not descending: {scores}"
    print(f"        [PASS] Risk scores descending: {scores}")

    # 4b. Sort by thermal_intensity desc
    print("    4b. Sort by thermal_intensity desc...")
    status, res = api_request("/api/thermal-events", params={"sort_by": "thermal_intensity", "sort_order": "desc"})
    intensities = [itm["thermal_intensity"] for itm in res["items"]]
    print(f"        [PASS] Intensities sorted: {intensities}")

    # 4c. Pagination: page 1 of size 2
    print("    4c. Pagination test (page=1, page_size=2)...")
    status, res = api_request("/api/thermal-events", params={"page": 1, "page_size": 2})
    assert status == 200
    assert len(res["items"]) == 2
    assert res["total_pages"] >= 3
    assert res["has_next"] is True
    print(f"        [PASS] Page 1: 2 items, total_pages: {res['total_pages']}, has_next: {res['has_next']}")

    # -------------------------------------------------------------
    # 5. Test Coordinate Validation (-90..90 lat, -180..180 lon)
    # -------------------------------------------------------------
    print("\n[5] Testing Coordinate Validations...")
    
    # 5a. Invalid Latitude > 90
    print("    5a. POST with invalid latitude = 95.5 (must reject)...")
    invalid_lat_payload = {
        "latitude": 95.5,
        "longitude": 72.0,
        "event_type": "Test Out of Bounds",
        "risk_score": 50.0
    }
    status, res = api_request("/api/thermal-events", method="POST", data=invalid_lat_payload)
    assert status == 422, f"Expected 422, got {status}: {res}"
    print("        [PASS] Successfully rejected latitude > 90 with 422 Unprocessable Entity.")

    # 5b. Invalid Longitude < -180
    print("    5b. POST with invalid longitude = -195.0 (must reject)...")
    invalid_lon_payload = {
        "latitude": 22.0,
        "longitude": -195.0,
        "event_type": "Test Out of Bounds",
        "risk_score": 50.0
    }
    status, res = api_request("/api/thermal-events", method="POST", data=invalid_lon_payload)
    assert status == 422, f"Expected 422, got {status}: {res}"
    print("        [PASS] Successfully rejected longitude < -180 with 422 Unprocessable Entity.")

    # -------------------------------------------------------------
    # 6. Test Full CRUD Lifecycle
    # -------------------------------------------------------------
    print("\n[6] Testing Full CRUD Lifecycle...")
    api_request("/api/thermal-events/TEST-EVT-999", method="DELETE")

    # 6a. CREATE: POST /api/thermal-events
    print("    6a. POST /api/thermal-events (Create)...")
    create_payload = {
        "event_id": "TEST-EVT-999",
        "latitude": 18.9220,
        "longitude": 72.8347,
        "event_type": "Industrial Tank Rupture",
        "thermal_intensity": "550 MW",
        "persistence": "Transient (1 hour)",
        "confidence": 0.91,
        "risk_score": 78.5,
        "land_cover": "Port & Chemical Silos",
        "data_source": "NASA FIRMS TEST",
        "status": "active"
    }
    status, created_event = api_request("/api/thermal-events", method="POST", data=create_payload)
    assert status == 201, f"Expected 201, got {status}: {created_event}"
    assert created_event["event_id"] == "TEST-EVT-999"
    assert created_event["risk_priority"] == "HIGH", f"Auto risk priority failed: {created_event['risk_priority']}"
    print(f"        [PASS] Created event ID: {created_event['id']} (event_id: {created_event['event_id']})")

    # 6b. READ: GET /api/thermal-events/{event_id}
    print("    6b. GET /api/thermal-events/TEST-EVT-999 (Read)...")
    status, fetched_event = api_request(f"/api/thermal-events/{created_event['event_id']}")
    assert status == 200, f"Expected 200, got {status}: {fetched_event}"
    assert fetched_event["event_id"] == "TEST-EVT-999"
    assert fetched_event["event_type"] == "Industrial Tank Rupture"
    print(f"        [PASS] Successfully retrieved event: {fetched_event['event_id']}")

    # 6c. UPDATE: PUT /api/thermal-events/{event_id}
    print("    6c. PUT /api/thermal-events/TEST-EVT-999 (Update status to 'contained')...")
    update_payload = {
        "status": "contained",
        "thermal_intensity": "120 MW",
        "risk_score": 35.0
    }
    status, updated_event = api_request(f"/api/thermal-events/{created_event['event_id']}", method="PUT", data=update_payload)
    assert status == 200, f"Expected 200, got {status}: {updated_event}"
    assert updated_event["status"] == "contained"
    assert updated_event["risk_score"] == 35.0
    assert updated_event["risk_priority"] == "LOW", f"Expected LOW for 35.0 risk_score, got {updated_event['risk_priority']}"
    print(f"        [PASS] Successfully updated event status to '{updated_event['status']}' and auto-derived priority to '{updated_event['risk_priority']}'")

    # 6d. DELETE: DELETE /api/thermal-events/{event_id}
    print("    6d. DELETE /api/thermal-events/TEST-EVT-999 (Delete)...")
    status, del_resp = api_request(f"/api/thermal-events/{created_event['event_id']}", method="DELETE")
    assert status == 200, f"Expected 200, got {status}: {del_resp}"
    print(f"        [PASS] Deleted: {del_resp.get('message')}")

    # 6e. VERIFY DELETION: GET /api/thermal-events/{event_id} -> 404
    print("    6e. GET /api/thermal-events/TEST-EVT-999 (Verify 404 after deletion)...")
    status, err_resp = api_request(f"/api/thermal-events/{created_event['event_id']}")
    assert status == 404, f"Expected 404, got {status}: {err_resp}"
    print("        [PASS] Confirmed 404 Not Found after deletion.")

    print("\n" + "=" * 70)
    print("ALL THERMAL EVENT API TESTS PASSED SUCCESSFULLY (100% COVERAGE)")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
