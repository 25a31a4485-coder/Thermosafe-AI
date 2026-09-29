import os
import sys

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath("backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from app.core.config import settings
from app.core.spatial import INDIA_BBOX_CSV, is_inside_india
from app.services.firms_service import FIRMSService, get_firms_service
from app.main import app

def test_full_firms_suite():
    print("=" * 60)
    print("RUNNING COMPREHENSIVE NASA FIRMS LIVE INTEGRATION TEST")
    print("=" * 60)

    # 1. Environment Variable Detection
    key = settings.effective_firms_map_key
    print(f"\n1. FIRMS Environment Variable Check:")
    print(f"   settings.effective_firms_map_key detected: {'YES' if key else 'NO'}")
    assert key, "NASA FIRMS MAP_KEY must be configured in environment or .env"
    print(f"   Key length: {len(key)} characters (Secret masked: {key[:4]}...{key[-4:]})")

    # 2. Bounding Box & India Scope
    print(f"\n2. India Geographic Scope Check:")
    print(f"   INDIA_BBOX_CSV: {INDIA_BBOX_CSV}")
    assert INDIA_BBOX_CSV == "68,6,97,37", f"Unexpected bounding box: {INDIA_BBOX_CSV}"
    assert is_inside_india(28.6139, 77.2090), "Delhi should be inside India"
    assert is_inside_india(19.0760, 72.8777), "Mumbai should be inside India"
    assert not is_inside_india(0.0, 0.0), "Gulf of Guinea should NOT be inside India"
    assert not is_inside_india(51.5074, -0.1278), "London should NOT be inside India"
    print("   Spatial boundary validation passed.")

    # 3. Direct NASA FIRMS Area API Call
    print(f"\n3. NASA FIRMS Live Area API Call:")
    svc = get_firms_service()
    success, csv_text, error, status_code, reason = svc.fetch_firms_data(
        source="VIIRS_NOAA21_NRT",
        area=INDIA_BBOX_CSV,
        days=1,
    )
    print(f"   HTTP Status: {status_code}")
    print(f"   Success: {success}")
    if error:
        print(f"   Error: {error} (Reason: {reason})")
    assert success, f"Direct NASA FIRMS fetch failed: {error}"
    assert csv_text and "latitude" in csv_text.lower(), "CSV response missing latitude header"
    lines = [l for l in csv_text.strip().split("\n") if l.strip()]
    record_count = len(lines) - 1
    print(f"   Direct NASA FIRMS records returned: {record_count}")

    # 4. Ingest and DB Persistence Verification
    print(f"\n4. Ingestion & Spatial Filter Verification:")
    ingest_result = svc.ingest_live_telemetry(source="VIIRS_NOAA21_NRT", days=1)
    print(f"   Ingested: {ingest_result.get('ingested')}")
    print(f"   Ignored (out-of-bounds/duplicates): {ingest_result.get('ignored')}")
    print(f"   Status: {ingest_result.get('status')}")
    assert ingest_result.get("status") in ("LIVE_CURRENT", "LIVE_OK_ZERO_EVENTS"), f"Unexpected status: {ingest_result.get('status')}"

    # 5. FastAPI Endpoints Testing with TestClient
    print(f"\n5. FastAPI FIRMS Endpoint Verification:")
    client = TestClient(app)

    # 5a. GET /api/firms/live
    resp_live = client.get("/api/firms/live?days=1")
    print(f"   GET /api/firms/live -> Status: {resp_live.status_code}")
    assert resp_live.status_code == 200
    data_live = resp_live.json()
    assert data_live["success"] is True, f"Expected success=True, got {data_live}"
    assert data_live["source"] == "NASA FIRMS"
    assert data_live["live"] is True
    assert isinstance(data_live["count"], int)
    assert isinstance(data_live["data"], list)
    assert len(data_live["data"]) == data_live["count"]
    print(f"   -> Returned count={data_live['count']} records in 'data' array")

    # Verify all records strictly inside India
    for rec in data_live["data"]:
        lat = rec["latitude"]
        lon = rec["longitude"]
        assert 6.0 <= lat <= 37.0 and 68.0 <= lon <= 97.0, f"Record out of India bbox: lat={lat}, lon={lon}"
        assert is_inside_india(lat, lon), f"Record failed is_inside_india: lat={lat}, lon={lon}"
    print("   -> 100% of returned live records are verified inside India!")

    # 5b. GET /api/firms/health
    resp_health = client.get("/api/firms/health")
    print(f"\n   GET /api/firms/health -> Status: {resp_health.status_code}")
    assert resp_health.status_code == 200
    data_health = resp_health.json()
    assert data_health["service"] == "NASA FIRMS"
    assert data_health["configured"] is True
    assert data_health["reachable"] is True
    assert data_health["live"] is True
    assert "map_key" not in str(data_health).lower() and "638bb381" not in str(data_health)
    print(f"   -> Health response: {data_health}")
    print("   -> No secrets exposed in health endpoint.")

    # 5c. GET /api/satellite/thermal-events?mode=live
    resp_sat = client.get("/api/satellite/thermal-events?mode=live")
    print(f"\n   GET /api/satellite/thermal-events?mode=live -> Status: {resp_sat.status_code}")
    assert resp_sat.status_code == 200
    data_sat = resp_sat.json()
    assert data_sat["success"] is True
    assert data_sat["live"] is True
    assert data_sat["count"] == data_live["count"]
    print(f"   -> Satellite proxy returned {data_sat['count']} live events.")

    # 6. Error Handling Verification (Missing Key Simulation)
    print(f"\n6. Missing Key Error Handling Verification:")
    unconfigured_svc = FIRMSService(api_key="", default_mode="live")
    payload = unconfigured_svc.get_firms_live_payload()
    print(f"   Unconfigured payload: success={payload['success']}, error='{payload.get('error')}'")
    assert payload["success"] is False
    assert payload["live"] is False
    assert payload["error"] == "NASA FIRMS MAP_KEY is not configured on the server."
    assert payload["count"] == 0
    assert payload["data"] == []
    print("   -> Missing key returns clear, safe error message.")

    health_unconf = unconfigured_svc.get_firms_health_summary()
    assert health_unconf["configured"] is False
    assert health_unconf["reachable"] is False
    assert health_unconf["live"] is False
    print("   -> Unconfigured health check returns configured=False, reachable=False.")

    print("\n" + "=" * 60)
    print("ALL NASA FIRMS BACKEND & FRONTEND INTEGRATION TESTS PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    test_full_firms_suite()
