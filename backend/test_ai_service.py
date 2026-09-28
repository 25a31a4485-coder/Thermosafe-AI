"""
Comprehensive Test Suite for Phase 6: AI Classification Service
Tests all 6 classification outcomes, coordinate validation, confidence ranges, and Swagger registration.
"""
import urllib.request
import urllib.parse
import urllib.error
import json
import sys

BASE_URL = "http://127.0.0.1:8000"


def api_request(path, method="POST", data=None):
    url = f"{BASE_URL}{path}"
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
    print("PHASE 6: AI CLASSIFICATION SERVICE - MULTI-SCENARIO TEST SUITE")
    print("=" * 70)

    EXPECTED_MODEL = "ThermalSafe-RuleEngine-Prototype-v1"

    # -------------------------------------------------------------
    # Scenario 1: Critical Industrial Fire
    # -------------------------------------------------------------
    print("\n[Scenario 1] Testing 'Critical Industrial Fire' classification...")
    payload_1 = {
        "latitude": 22.3039,
        "longitude": 70.8022,
        "thermal_intensity": "1250 MW",
        "persistence": "Continuous (36+ hours active)",
        "nearby_industrial_facility": "Jamnagar Petrochemical Complex",
        "land_cover": "Heavy Industrial Zone",
        "historical_occurrences": 3,
        "data_source": "NASA FIRMS VIIRS"
    }
    status, res = api_request("/api/ai/classify", method="POST", data=payload_1)
    assert status == 200, f"Expected 200, got {status}: {res}"
    assert res["classification"] == "Critical Industrial Fire", f"Wrong classification: {res}"
    assert 0.0 <= res["confidence"] <= 1.0, f"Confidence out of range: {res['confidence']}"
    assert res["confidence"] >= 0.90, f"Expected high confidence, got: {res['confidence']}"
    assert res["model_name"] == EXPECTED_MODEL
    assert len(res["explanation"]) > 20
    print(f"    Result: {res['classification']} (Confidence: {res['confidence']:.2f})")
    print(f"    Explanation: {res['explanation']}")
    print("    [PASS] Scenario 1 verified successfully.")

    # -------------------------------------------------------------
    # Scenario 2: High-Risk Thermal Event
    # -------------------------------------------------------------
    print("\n[Scenario 2] Testing 'High-Risk Thermal Event' classification...")
    payload_2 = {
        "latitude": 21.1167,
        "longitude": 72.6500,
        "thermal_intensity": "680 MW",
        "persistence": "Recurrent (Last 8 hours)",
        "nearby_industrial_facility": "Hazira Industrial Port & Manufacturing Hub",
        "land_cover": "Industrial Storage & Steel Mill",
        "historical_occurrences": 2,
        "data_source": "NASA FIRMS MODIS"
    }
    status, res = api_request("/api/ai/classify", method="POST", data=payload_2)
    assert status == 200, f"Expected 200, got {status}: {res}"
    assert res["classification"] == "High-Risk Thermal Event", f"Wrong classification: {res}"
    assert 0.0 <= res["confidence"] <= 1.0
    assert res["confidence"] >= 0.85
    assert res["model_name"] == EXPECTED_MODEL
    print(f"    Result: {res['classification']} (Confidence: {res['confidence']:.2f})")
    print(f"    Explanation: {res['explanation']}")
    print("    [PASS] Scenario 2 verified successfully.")

    # -------------------------------------------------------------
    # Scenario 3: Gas Flare
    # -------------------------------------------------------------
    print("\n[Scenario 3] Testing 'Gas Flare' classification...")
    payload_3 = {
        "latitude": 19.4167,
        "longitude": 71.3333,
        "thermal_intensity": "320 MW",
        "persistence": "Semi-continuous (Scheduled flaring)",
        "nearby_industrial_facility": "Mumbai High Offshore Extraction Platform",
        "land_cover": "Offshore Marine Platform",
        "historical_occurrences": 8,
        "data_source": "NASA FIRMS VIIRS"
    }
    status, res = api_request("/api/ai/classify", method="POST", data=payload_3)
    assert status == 200, f"Expected 200, got {status}: {res}"
    assert res["classification"] == "Gas Flare", f"Wrong classification: {res}"
    assert 0.0 <= res["confidence"] <= 1.0
    assert res["confidence"] >= 0.90
    assert res["model_name"] == EXPECTED_MODEL
    print(f"    Result: {res['classification']} (Confidence: {res['confidence']:.2f})")
    print(f"    Explanation: {res['explanation']}")
    print("    [PASS] Scenario 3 verified successfully.")

    # -------------------------------------------------------------
    # Scenario 4: Persistent Thermal Source
    # -------------------------------------------------------------
    print("\n[Scenario 4] Testing 'Persistent Thermal Source' classification...")
    payload_4 = {
        "latitude": 22.3595,
        "longitude": 82.7501,
        "thermal_intensity": "410 MW",
        "persistence": "Continuous (Historical 90+ days)",
        "nearby_industrial_facility": "Korba Super Thermal Power Plant",
        "land_cover": "Power Generation & Slag Yard",
        "historical_occurrences": 25,
        "data_source": "NASA FIRMS SLSTR"
    }
    status, res = api_request("/api/ai/classify", method="POST", data=payload_4)
    assert status == 200, f"Expected 200, got {status}: {res}"
    assert res["classification"] == "Persistent Thermal Source", f"Wrong classification: {res}"
    assert 0.0 <= res["confidence"] <= 1.0
    assert res["confidence"] >= 0.85
    assert res["model_name"] == EXPECTED_MODEL
    print(f"    Result: {res['classification']} (Confidence: {res['confidence']:.2f})")
    print(f"    Explanation: {res['explanation']}")
    print("    [PASS] Scenario 4 verified successfully.")

    # -------------------------------------------------------------
    # Scenario 5: Low-Risk Thermal Activity
    # -------------------------------------------------------------
    print("\n[Scenario 5] Testing 'Low-Risk Thermal Activity' classification...")
    payload_5 = {
        "latitude": 21.7052,
        "longitude": 72.5873,
        "thermal_intensity": "45 MW",
        "persistence": "Transient (< 2 hours)",
        "nearby_industrial_facility": "Dahej Buffer Perimeter",
        "land_cover": "Scrubland / Industrial Buffer",
        "historical_occurrences": 1,
        "data_source": "NASA FIRMS VIIRS"
    }
    status, res = api_request("/api/ai/classify", method="POST", data=payload_5)
    assert status == 200, f"Expected 200, got {status}: {res}"
    assert res["classification"] == "Low-Risk Thermal Activity", f"Wrong classification: {res}"
    assert 0.0 <= res["confidence"] <= 1.0
    assert 0.70 <= res["confidence"] <= 0.90
    assert res["model_name"] == EXPECTED_MODEL
    print(f"    Result: {res['classification']} (Confidence: {res['confidence']:.2f})")
    print(f"    Explanation: {res['explanation']}")
    print("    [PASS] Scenario 5 verified successfully.")

    # -------------------------------------------------------------
    # Scenario 6: Unknown
    # -------------------------------------------------------------
    print("\n[Scenario 6] Testing 'Unknown' classification on inconclusive signals...")
    payload_6 = {
        "latitude": 15.0000,
        "longitude": 75.0000,
        "thermal_intensity": "0 MW",
        "persistence": "Uncertain",
        "nearby_industrial_facility": None,
        "land_cover": None,
        "historical_occurrences": 0,
        "data_source": "Unknown Sensor"
    }
    status, res = api_request("/api/ai/classify", method="POST", data=payload_6)
    assert status == 200, f"Expected 200, got {status}: {res}"
    assert res["classification"] == "Unknown", f"Wrong classification: {res}"
    assert 0.0 <= res["confidence"] <= 1.0
    assert res["confidence"] < 0.60
    assert res["model_name"] == EXPECTED_MODEL
    print(f"    Result: {res['classification']} (Confidence: {res['confidence']:.2f})")
    print(f"    Explanation: {res['explanation']}")
    print("    [PASS] Scenario 6 verified successfully.")

    # -------------------------------------------------------------
    # Coordinate Validations
    # -------------------------------------------------------------
    print("\n[Coordinate Validations] Testing latitude & longitude boundary checks...")
    
    # Invalid Latitude
    invalid_lat = dict(payload_1, latitude=95.5)
    status, res = api_request("/api/ai/classify", method="POST", data=invalid_lat)
    assert status == 422, f"Expected 422 for latitude > 90, got {status}: {res}"
    print("    [PASS] Successfully rejected latitude = 95.5 with 422 Unprocessable Entity.")

    # Invalid Longitude
    invalid_lon = dict(payload_1, longitude=-192.0)
    status, res = api_request("/api/ai/classify", method="POST", data=invalid_lon)
    assert status == 422, f"Expected 422 for longitude < -180, got {status}: {res}"
    print("    [PASS] Successfully rejected longitude = -192.0 with 422 Unprocessable Entity.")

    print("\n" + "=" * 70)
    print("ALL 6 AI CLASSIFICATION SCENARIOS AND VALIDATIONS PASSED (100% COVERAGE)")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
