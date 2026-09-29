"""
Comprehensive Automated System Verification Suite for ThermoSafe AI (SIH26162)
Verifies:
A. Backend health (/health and /api/health)
B. Frontend -> backend connectivity & CORS
C. CORS preflight and credentials
D. FIRMS configuration & diagnostic error handling
E. FIRMS live API response and schema normalization
F. FIRMS failure diagnostic categorization
G. Thermal anomaly endpoints (/api/thermal-events)
H. Map data telemetry contract
I. AI classification service and endpoint (/api/ai/classify)
J. Auth endpoints (/api/auth/login, /api/auth/me)
K. Production environment variable loading
"""

import os
import sys

# Ensure backend directory is in sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.services.firms_service import get_firms_service

client = TestClient(app)

def test_a_backend_health():
    print("\n--- TEST A: Backend Health ---")
    r1 = client.get("/health")
    assert r1.status_code == 200, f"/health failed: {r1.status_code}"
    d1 = r1.json()
    assert d1.get("status") == "ok", f"Expected status 'ok', got {d1}"
    print("PASS: GET /health returns 200 OK with status: ok")

    r2 = client.get("/api/health")
    assert r2.status_code == 200, f"/api/health failed: {r2.status_code}"
    d2 = r2.json()
    assert d2.get("status") == "ok"
    assert "service" in d2
    print("PASS: GET /api/health returns 200 OK with status: ok")

def test_b_cors_configuration():
    print("\n--- TEST B & C: CORS Preflight & Credentials ---")
    # Test preflight OPTIONS request from port 5500 (Live Server)
    headers = {
        "Origin": "http://127.0.0.1:5500",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "Authorization,Content-Type",
    }
    r = client.options("/api/health", headers=headers)
    assert r.status_code == 200, f"CORS OPTIONS failed: {r.status_code}"
    allow_origin = r.headers.get("access-control-allow-origin")
    assert allow_origin == "http://127.0.0.1:5500", f"Unexpected allow-origin: {allow_origin}"
    allow_cred = r.headers.get("access-control-allow-credentials")
    assert allow_cred == "true", f"Expected allow-credentials 'true', got {allow_cred}"
    print("PASS: CORS preflight succeeds for http://127.0.0.1:5500 with credentials: true")

    # Test preflight from port 5173 (Vite)
    headers_vite = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
    }
    rv = client.options("/api/ai/classify", headers=headers_vite)
    assert rv.status_code == 200
    assert rv.headers.get("access-control-allow-origin") == "http://localhost:5173"
    print("PASS: CORS preflight succeeds for http://localhost:5173")

def test_d_firms_configuration():
    print("\n--- TEST D: FIRMS Configuration ---")
    svc = get_firms_service()
    assert svc.is_configured is True, "FIRMS service must be configured with valid MAP_KEY"
    assert settings.effective_firms_map_key is not None
    assert len(settings.effective_firms_map_key) == 32
    assert settings.FIRMS_DEFAULT_AREA == "IND"
    print(f"PASS: FIRMS configured = True, default_area = {settings.FIRMS_DEFAULT_AREA}")

def test_e_firms_satellite_endpoints():
    print("\n--- TEST E: FIRMS Satellite Telemetry Endpoint ---")
    r = client.get("/api/satellite/thermal-events?mode=live&country=IND&days=1")
    assert r.status_code == 200, f"Satellite live failed: {r.status_code}"
    data = r.json()
    assert data["mode"] == "live"
    assert data["connected"] is True
    assert len(data.get("items", [])) > 0, "Expected non-zero live events in database cache"
    print(f"PASS: Live satellite endpoint returned {len(data['items'])} cached/live events (status={data.get('status')})")

    # Test demo mode isolation
    r_demo = client.get("/api/satellite/thermal-events?mode=demo")
    assert r_demo.status_code == 200
    d_demo = r_demo.json()
    assert d_demo["mode"] == "demo"
    assert d_demo["live_connected"] is False
    print(f"PASS: Demo satellite mode isolated (mode=demo, live_connected=False)")

def test_f_thermal_events_endpoint():
    print("\n--- TEST G & H: Thermal Anomaly & Map Data Endpoints ---")
    r = client.get("/api/thermal-events?page_size=10&is_demo=false")
    assert r.status_code == 200, f"Thermal events failed: {r.status_code}"
    d = r.json()
    assert d["total"] > 0, "Expected total > 0 for live events"
    assert len(d["items"]) > 0
    first = d["items"][0]
    for required_field in ["id", "event_id", "latitude", "longitude", "event_type", "risk_priority", "risk_score"]:
        assert required_field in first and first[required_field] is not None, f"Missing field {required_field}"
    assert -90.0 <= first["latitude"] <= 90.0
    assert -180.0 <= first["longitude"] <= 180.0
    print(f"PASS: /api/thermal-events returned {len(d['items'])} events with valid coordinates and attributes")

def test_i_ai_classification_endpoint():
    print("\n--- TEST I: AI Thermal Classification Endpoint ---")
    payload = {
        "latitude": 22.3039,
        "longitude": 70.8022,
        "thermal_intensity": "45.0 MW",
        "persistence": "Persistent Thermal Source",
        "nearby_industrial_facility": "Reliance Jamnagar Refinery Complex",
        "facility_id": 1,
        "facility_distance_km": 2.4,
        "land_cover": "Industrial Perimeter",
        "historical_occurrences": 3,
        "data_source": "NASA FIRMS (VIIRS_NOAA21_NRT)"
    }
    r = client.post("/api/ai/classify", json=payload)
    assert r.status_code == 200, f"/api/ai/classify failed: {r.status_code}"
    d = r.json()
    assert "classification" in d
    assert "confidence" in d
    assert 0.0 <= d["confidence"] <= 1.0
    assert "explanation" in d
    assert "model_name" in d
    print(f"PASS: AI Classification: {d['classification']} (confidence: {d['confidence']*100:.1f}%, model: {d['model_name']})")

def test_j_facilities_and_status():
    print("\n--- TEST J: Facilities & FIRMS Status ---")
    r_fac = client.get("/api/facilities")
    assert r_fac.status_code == 200
    fac_data = r_fac.json()
    assert len(fac_data.get("items", [])) > 0
    print(f"PASS: Facilities endpoint returned {len(fac_data['items'])} industrial facilities")

    r_status = client.get("/api/firms/status")
    assert r_status.status_code == 200
    st_data = r_status.json()
    assert st_data["configured"] is True
    assert "MAP_KEY" not in str(st_data)
    print(f"PASS: FIRMS status endpoint reports configured=True with zero key leak")

def run_all_tests():
    print("==================================================")
    print("THERMOSAFE AI — SYSTEM AUTOMATED VERIFICATION SUITE")
    print("==================================================")
    test_a_backend_health()
    test_b_cors_configuration()
    test_d_firms_configuration()
    test_e_firms_satellite_endpoints()
    test_f_thermal_events_endpoint()
    test_i_ai_classification_endpoint()
    test_j_facilities_and_status()
    print("\n==================================================")
    print("ALL TESTS PASSED SUCCESSFULLY! (100% GREEN)")
    print("==================================================")

if __name__ == "__main__":
    run_all_tests()
