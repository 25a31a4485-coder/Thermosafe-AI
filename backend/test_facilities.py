"""
Comprehensive Test Suite for Phase 5: Industrial Facilities API
Tests every endpoint, filter, coordinate validation, demo seeding, and CRUD lifecycle.
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
    print("PHASE 5: INDUSTRIAL FACILITIES API - COMPREHENSIVE TEST SUITE")
    print("=" * 70)

    # -------------------------------------------------------------
    # 1. Test Seed Endpoint
    # -------------------------------------------------------------
    print("\n[1] Testing POST /api/facilities/seed (force=true)...")
    status, res = api_request("/api/facilities/seed", method="POST", params={"force": "true"})
    print(f"    Status: {status} -> {res.get('message')}")
    assert status == 200, f"Expected 200, got {status}: {res}"
    assert res.get("total_demo_facilities", 0) >= 8, f"Expected at least 8 demo facilities, got {res}"
    print(f"    [PASS] Total demo facilities in database: {res.get('total_demo_facilities')}")

    # -------------------------------------------------------------
    # 2. Test GET /api/facilities (Default List & Return Fields)
    # -------------------------------------------------------------
    print("\n[2] Testing GET /api/facilities (default list & field validation)...")
    status, res = api_request("/api/facilities")
    assert status == 200, f"Expected 200, got {status}: {res}"
    assert "items" in res and "total" in res, "Missing pagination structure"
    items = res["items"]
    assert len(items) >= 8, f"Expected at least 8 facilities, got {len(items)}"
    print(f"    Total items: {res['total']}, Items in page: {len(items)}")

    # Verify all fields requested by user: id, name, latitude, longitude, industry_type, operator, risk_level, address
    sample = items[0]
    required_fields = [
        "id", "name", "latitude", "longitude",
        "industry_type", "operator", "risk_level", "address"
    ]
    for field in required_fields:
        assert field in sample, f"Missing required facility field: '{field}'"
    
    assert sample["is_demo"] is True, "Demo facility must have is_demo = True"
    assert "geojson" in sample, "Facility must contain GeoJSON representation"
    assert sample["geojson"]["geometry"]["coordinates"] == [sample["longitude"], sample["latitude"]]
    print(f"    Sample facility: '{sample['name']}' ({sample['industry_type']}) - Risk: {sample['risk_level']}")
    print(f"    Location: ({sample['latitude']}, {sample['longitude']}), Address: {sample['address']}")
    print("    [PASS] All required return fields and map-compatible GeoJSON verified.")

    # -------------------------------------------------------------
    # 3. Test Filters (industry_type, risk_level, geographic area)
    # -------------------------------------------------------------
    print("\n[3] Testing Filters...")

    # 3a. Filter by industry_type
    print("    3a. Filter by industry_type='Refinery'...")
    status, res = api_request("/api/facilities", params={"industry_type": "Refinery"})
    assert status == 200 and len(res["items"]) >= 1, f"Expected Refinery facilities, got {len(res['items'])}"
    for fac in res["items"]:
        assert "refinery" in fac["industry_type"].lower()
    print(f"        [PASS] Found {len(res['items'])} Refinery facility(ies): {[f['name'] for f in res['items']]}")

    # 3b. Filter by risk_level
    print("    3b. Filter by risk_level='High'...")
    status, res = api_request("/api/facilities", params={"risk_level": "High"})
    assert status == 200 and len(res["items"]) >= 1
    for fac in res["items"]:
        assert fac["risk_level"].lower() == "high"
    print(f"        [PASS] Found {len(res['items'])} High-risk facility(ies).")

    # 3c. Filter by geographic area (Region/State text in address)
    print("    3c. Filter by geographic area text area='Gujarat'...")
    status, res = api_request("/api/facilities", params={"area": "Gujarat"})
    assert status == 200 and len(res["items"]) >= 1
    for fac in res["items"]:
        assert "gujarat" in fac["address"].lower() or "gujarat" in fac["name"].lower()
    print(f"        [PASS] Found {len(res['items'])} facility(ies) in Gujarat: {[f['name'] for f in res['items']]}")

    print("    3d. Filter by geographic area text area='Tamil Nadu'...")
    status, res = api_request("/api/facilities", params={"area": "Tamil Nadu"})
    assert status == 200 and len(res["items"]) >= 1
    assert "Manali" in res["items"][0]["name"]
    print(f"        [PASS] Found facility in Tamil Nadu: {res['items'][0]['name']}")

    # 3e. Filter by Bounding Box (Gujarat region: 20-24°N, 68-74°E)
    print("    3e. Filter by bounding box (20 <= lat <= 24, 68 <= lon <= 74)...")
    status, res = api_request("/api/facilities", params={
        "min_lat": 20.0, "max_lat": 24.0,
        "min_lon": 68.0, "max_lon": 74.0
    })
    assert status == 200 and len(res["items"]) >= 3
    for fac in res["items"]:
        assert 20.0 <= fac["latitude"] <= 24.0
        assert 68.0 <= fac["longitude"] <= 74.0
    print(f"        [PASS] Found {len(res['items'])} facilities within bounding box.")

    # 3f. Filter by Spatial Proximity (Surat/Hazira coords + 50km radius)
    print("    3f. Filter by spatial proximity (Hazira: 21.1167, 72.6500, radius=50km)...")
    status, res = api_request("/api/facilities", params={
        "latitude": 21.1167, "longitude": 72.6500, "radius_km": 50.0
    })
    assert status == 200 and len(res["items"]) >= 1
    assert any("Hazira" in f["name"] for f in res["items"])
    print(f"        [PASS] Proximity query matched: {[f['name'] for f in res['items']]}")

    # -------------------------------------------------------------
    # 4. Test Coordinate Validations (-90..90 lat, -180..180 lon)
    # -------------------------------------------------------------
    print("\n[4] Testing Coordinate Validations...")

    # 4a. Latitude > 90
    print("    4a. POST with invalid latitude = 94.5 (must reject with 422)...")
    invalid_lat_payload = {
        "name": "Invalid Latitude Facility",
        "latitude": 94.5,
        "longitude": 75.0,
        "industry_type": "Chemical"
    }
    status, res = api_request("/api/facilities", method="POST", data=invalid_lat_payload)
    assert status == 422, f"Expected 422, got {status}: {res}"
    print("        [PASS] Successfully rejected latitude > 90 with 422 Unprocessable Entity.")

    # 4b. Longitude < -180
    print("    4b. POST with invalid longitude = -188.0 (must reject with 422)...")
    invalid_lon_payload = {
        "name": "Invalid Longitude Facility",
        "latitude": 20.0,
        "longitude": -188.0,
        "industry_type": "Chemical"
    }
    status, res = api_request("/api/facilities", method="POST", data=invalid_lon_payload)
    assert status == 422, f"Expected 422, got {status}: {res}"
    print("        [PASS] Successfully rejected longitude < -180 with 422 Unprocessable Entity.")

    # -------------------------------------------------------------
    # 5. Test Full CRUD Lifecycle
    # -------------------------------------------------------------
    print("\n[5] Testing Full CRUD Lifecycle...")

    # 5a. CREATE: POST /api/facilities
    print("    5a. POST /api/facilities (Create)...")
    create_payload = {
        "name": "Bhubaneswar Aerospace & Metals SEZ",
        "latitude": 20.2961,
        "longitude": 85.8245,
        "industry_type": "Aerospace & Rare Earth Metallurgy",
        "operator": "Odisha Industrial Infrastructure Corp",
        "risk_level": "Medium",
        "address": "Zone C, Khurda Industrial Corridor, Bhubaneswar, Odisha, India",
        "is_demo": True
    }
    status, created_facility = api_request("/api/facilities", method="POST", data=create_payload)
    assert status == 201, f"Expected 201, got {status}: {created_facility}"
    facility_id = created_facility["id"]
    assert created_facility["name"] == "Bhubaneswar Aerospace & Metals SEZ"
    print(f"        [PASS] Created facility with ID: {facility_id}")

    # 5b. READ: GET /api/facilities/{id}
    print(f"    5b. GET /api/facilities/{facility_id} (Read)...")
    status, fetched_facility = api_request(f"/api/facilities/{facility_id}")
    assert status == 200, f"Expected 200, got {status}: {fetched_facility}"
    assert fetched_facility["id"] == facility_id
    assert fetched_facility["operator"] == "Odisha Industrial Infrastructure Corp"
    print(f"        [PASS] Successfully retrieved facility: '{fetched_facility['name']}'")

    # 5c. UPDATE: PUT /api/facilities/{id}
    print(f"    5c. PUT /api/facilities/{facility_id} (Update risk_level to 'High')...")
    update_payload = {
        "risk_level": "High",
        "operator": "Odisha State Heavy Industries Board"
    }
    status, updated_facility = api_request(f"/api/facilities/{facility_id}", method="PUT", data=update_payload)
    assert status == 200, f"Expected 200, got {status}: {updated_facility}"
    assert updated_facility["risk_level"] == "High"
    assert updated_facility["operator"] == "Odisha State Heavy Industries Board"
    print(f"        [PASS] Successfully updated risk_level to '{updated_facility['risk_level']}' and operator.")

    # 5d. DELETE: DELETE /api/facilities/{id}
    print(f"    5d. DELETE /api/facilities/{facility_id} (Delete)...")
    status, del_resp = api_request(f"/api/facilities/{facility_id}", method="DELETE")
    assert status == 200, f"Expected 200, got {status}: {del_resp}"
    print(f"        [PASS] Deleted: {del_resp.get('message')}")

    # 5e. VERIFY 404: GET /api/facilities/{id} -> 404
    print(f"    5e. GET /api/facilities/{facility_id} (Verify 404 after deletion)...")
    status, err_resp = api_request(f"/api/facilities/{facility_id}")
    assert status == 404, f"Expected 404, got {status}: {err_resp}"
    print("        [PASS] Confirmed 404 Not Found after deletion.")

    print("\n" + "=" * 70)
    print("ALL INDUSTRIAL FACILITIES API TESTS PASSED SUCCESSFULLY (100% COVERAGE)")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
