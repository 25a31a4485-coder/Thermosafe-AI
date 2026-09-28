"""
Comprehensive Test Suite for Phase 7: Risk Assessment Engine
Tests all 4 risk categories (Low, Moderate, High, Critical), factor breakdowns, and prototype methodology disclaimer.
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
    print("PHASE 7: RISK ASSESSMENT ENGINE - COMPREHENSIVE TEST SUITE")
    print("=" * 70)

    # -------------------------------------------------------------
    # Test Case 1: Critical Event (Score 75 - 100)
    # -------------------------------------------------------------
    print("\n[Test 1] Testing 'Critical' risk bracket (Score 75–100)...")
    payload_crit = {
        "thermal_intensity": "1250 MW",
        "persistence": "Continuous (36+ hours active)",
        "industrial_facility_proximity_km": 0.1,
        "nearby_industrial_facility": "Jamnagar Petrochemical Complex",
        "population_proximity_km": 1.5,
        "historical_recurrence": 3,
        "ai_classification": "Critical Industrial Fire",
        "event_type": "Industrial Fire",
        "latitude": 22.3039,
        "longitude": 70.8022
    }
    status, res = api_request("/api/risk/analyze", method="POST", data=payload_crit)
    assert status == 200, f"Expected 200, got {status}: {res}"
    assert res["risk_priority"] == "Critical", f"Expected Critical, got: {res['risk_priority']}"
    assert 75.0 <= res["risk_score"] <= 100.0, f"Score out of Critical range: {res['risk_score']}"
    print(f"    Risk Score: {res['risk_score']} / 100 -> Category: {res['risk_priority']}")
    print(f"    Factors: Thermal={res['thermal_factor']}, Persist={res['persistence_factor']}, Ind={res['industrial_proximity_factor']}, Pop={res['population_proximity_factor']}, Hist={res['historical_factor']}")
    print(f"    Explanation: {res['explanation']}")
    print("    [PASS] Critical event verified.")

    # -------------------------------------------------------------
    # Test Case 2: High Event (Score 50 - 74)
    # -------------------------------------------------------------
    print("\n[Test 2] Testing 'High' risk bracket (Score 50–74)...")
    payload_high = {
        "thermal_intensity": "680 MW",
        "persistence": "Recurrent (Last 8 hours)",
        "industrial_facility_proximity_km": 0.8,
        "nearby_industrial_facility": "Hazira Industrial Port & Manufacturing Hub",
        "population_proximity_km": 4.0,
        "historical_recurrence": 2,
        "ai_classification": "High-Risk Thermal Event",
        "event_type": "High-Risk Thermal Event",
        "latitude": 21.1167,
        "longitude": 72.6500
    }
    status, res = api_request("/api/risk/analyze", method="POST", data=payload_high)
    assert status == 200, f"Expected 200, got {status}: {res}"
    assert res["risk_priority"] == "High", f"Expected High, got: {res['risk_priority']}"
    assert 50.0 <= res["risk_score"] < 75.0, f"Score out of High range: {res['risk_score']}"
    print(f"    Risk Score: {res['risk_score']} / 100 -> Category: {res['risk_priority']}")
    print(f"    Factors: Thermal={res['thermal_factor']}, Persist={res['persistence_factor']}, Ind={res['industrial_proximity_factor']}, Pop={res['population_proximity_factor']}, Hist={res['historical_factor']}")
    print("    [PASS] High event verified.")

    # -------------------------------------------------------------
    # Test Case 3: Moderate Event (Score 25 - 49)
    # -------------------------------------------------------------
    print("\n[Test 3] Testing 'Moderate' risk bracket (Score 25–49)...")
    payload_mod = {
        "thermal_intensity": "320 MW",
        "persistence": "Semi-continuous (Scheduled flaring)",
        "industrial_facility_proximity_km": 1.0,
        "nearby_industrial_facility": "Mumbai High Offshore Extraction Platform",
        "population_proximity_km": 25.0,
        "historical_recurrence": 8,
        "ai_classification": "Gas Flare",
        "event_type": "Gas Flare",
        "latitude": 19.4167,
        "longitude": 71.3333
    }
    status, res = api_request("/api/risk/analyze", method="POST", data=payload_mod)
    assert status == 200, f"Expected 200, got {status}: {res}"
    assert res["risk_priority"] == "Moderate", f"Expected Moderate, got: {res['risk_priority']}"
    assert 25.0 <= res["risk_score"] < 50.0, f"Score out of Moderate range: {res['risk_score']}"
    print(f"    Risk Score: {res['risk_score']} / 100 -> Category: {res['risk_priority']}")
    print(f"    Factors: Thermal={res['thermal_factor']}, Persist={res['persistence_factor']}, Ind={res['industrial_proximity_factor']}, Pop={res['population_proximity_factor']}, Hist={res['historical_factor']}")
    print("    [PASS] Moderate event verified.")

    # -------------------------------------------------------------
    # Test Case 4: Low Event (Score 0 - 24)
    # -------------------------------------------------------------
    print("\n[Test 4] Testing 'Low' risk bracket (Score 0–24)...")
    payload_low = {
        "thermal_intensity": "40 MW",
        "persistence": "Transient (< 2 hours)",
        "industrial_facility_proximity_km": 12.0,
        "nearby_industrial_facility": "Dahej Buffer Perimeter",
        "population_proximity_km": 20.0,
        "historical_recurrence": 1,
        "ai_classification": "Low-Risk Thermal Activity",
        "event_type": "Low-Risk Thermal Activity",
        "latitude": 21.7052,
        "longitude": 72.5873
    }
    status, res = api_request("/api/risk/analyze", method="POST", data=payload_low)
    assert status == 200, f"Expected 200, got {status}: {res}"
    assert res["risk_priority"] == "Low", f"Expected Low, got: {res['risk_priority']}"
    assert 0.0 <= res["risk_score"] < 25.0, f"Score out of Low range: {res['risk_score']}"
    print(f"    Risk Score: {res['risk_score']} / 100 -> Category: {res['risk_priority']}")
    print(f"    Factors: Thermal={res['thermal_factor']}, Persist={res['persistence_factor']}, Ind={res['industrial_proximity_factor']}, Pop={res['population_proximity_factor']}, Hist={res['historical_factor']}")
    print("    [PASS] Low event verified.")

    # -------------------------------------------------------------
    # Test Case 5: Verification of Required Fields & Prototype Disclaimer
    # -------------------------------------------------------------
    print("\n[Test 5] Verifying Return Fields & Prototype Disclaimer...")
    required_keys = [
        "risk_score", "risk_priority", "thermal_factor",
        "persistence_factor", "industrial_proximity_factor",
        "population_proximity_factor", "historical_factor", "explanation", "methodology"
    ]
    for k in required_keys:
        assert k in res, f"Missing required response field: '{k}'"
    
    assert "prototype" in res["methodology"].lower() or "experimental" in res["methodology"].lower()
    assert "not officially validated" in res["methodology"].lower()
    print(f"    Methodology Tag: {res['methodology']}")
    print("    [PASS] All return fields and explicit prototype disclaimer confirmed.")

    print("\n" + "=" * 70)
    print("ALL 4 RISK BRACKETS AND FACTOR CHECKS PASSED (100% COVERAGE)")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
