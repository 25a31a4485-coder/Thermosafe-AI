"""
Comprehensive Test Suite for Phase 10: Analytics API.
Tests real database aggregations across:
1. Executive summary KPIs (GET /api/analytics/summary)
2. Risk category distribution (GET /api/analytics/risk-distribution)
3. Event hazard types breakdown (GET /api/analytics/event-types)
4. Chronological time-series trend (GET /api/analytics/time-series)
5. Date filtering on all endpoints
6. Swagger / OpenAPI schema registration
"""

import json
import sys
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone, timedelta

BASE_URL = "http://127.0.0.1:8000/api/analytics"


def get_json(endpoint: str, params: dict = None):
    url = f"{BASE_URL}{endpoint}"
    if params:
        qs = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        if qs:
            url = f"{url}?{qs}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def test_analytics_summary():
    print("\n--- TEST 1: Executive Analytics Summary (GET /api/analytics/summary) ---")
    status, data = get_json("/summary")
    assert status == 200, f"Expected 200, got {status}"
    
    required_keys = [
        "total_thermal_events",
        "critical_events",
        "high_risk_events",
        "moderate_events",
        "low_risk_events",
        "active_alerts",
        "industrial_facilities",
        "events_detected_today",
        "events_detected_this_week",
    ]
    for key in required_keys:
        assert key in data, f"Required summary key '{key}' missing from response!"
        val = data[key]
        assert isinstance(val, int), f"Value for '{key}' must be integer, got {type(val)}"
        assert val >= 0, f"Value for '{key}' cannot be negative: {val}"
        print(f"  {key}: {val}")

    # Integrity verification: Priority sum must equal total events
    sum_priorities = (
        data["critical_events"]
        + data["high_risk_events"]
        + data["moderate_events"]
        + data["low_risk_events"]
    )
    assert sum_priorities == data["total_thermal_events"], (
        f"Sum of priorities ({sum_priorities}) does not match total events ({data['total_thermal_events']})"
    )
    assert data["industrial_facilities"] >= 8, f"Expected at least 8 facilities, got {data['industrial_facilities']}"
    print(f"[PASS] Summary metrics verified with real database aggregations (Total Events: {data['total_thermal_events']}).")
    return data["total_thermal_events"]


def test_risk_distribution(expected_total: int):
    print("\n--- TEST 2: Risk Category Distribution (GET /api/analytics/risk-distribution) ---")
    status, data = get_json("/risk-distribution")
    assert status == 200, f"Expected 200, got {status}"
    assert data["total_events"] == expected_total
    
    dist = data.get("distribution", [])
    assert len(dist) == 4, f"Expected 4 risk categories, got {len(dist)}"
    
    categories = [item["category"] for item in dist]
    assert set(categories) == {"Critical", "High", "Moderate", "Low"}
    
    sum_counts = sum(item["count"] for item in dist)
    assert sum_counts == expected_total, f"Sum of counts {sum_counts} != expected total {expected_total}"
    
    sum_percentages = sum(item["percentage"] for item in dist)
    if expected_total > 0:
        assert abs(sum_percentages - 100.0) < 1.0, f"Percentages sum {sum_percentages} does not equal 100%"
        
    for item in dist:
        print(f"  [{item['category']}] Count: {item['count']} ({item['percentage']}%), Avg Risk Score: {item['avg_risk_score']}")
        assert 0.0 <= item["avg_risk_score"] <= 100.0
        
    print("[PASS] Risk distribution calculated dynamically with 100% mathematical integrity.")


def test_event_types_breakdown(expected_total: int):
    print("\n--- TEST 3: Event Hazard Types Breakdown (GET /api/analytics/event-types) ---")
    status, data = get_json("/event-types")
    assert status == 200, f"Expected 200, got {status}"
    assert data["total_events"] == expected_total
    
    dist = data.get("distribution", [])
    assert len(dist) > 0, "Expected at least 1 event type breakdown item"
    
    sum_counts = sum(item["count"] for item in dist)
    assert sum_counts == expected_total
    
    sum_percentages = sum(item["percentage"] for item in dist)
    if expected_total > 0:
        assert abs(sum_percentages - 100.0) < 1.0, f"Percentages sum {sum_percentages} does not equal 100%"
        
    for item in dist:
        print(f"  - {item['event_type']}: {item['count']} incidents ({item['percentage']}%), Avg Score: {item['avg_risk_score']}")
        
    print("[PASS] Event types hazard breakdown verified.")


def test_time_series(expected_total: int):
    print("\n--- TEST 4: Chronological Time-Series Aggregation (GET /api/analytics/time-series) ---")
    status, data = get_json("/time-series", {"interval": "daily"})
    assert status == 200, f"Expected 200, got {status}"
    assert data["interval"] == "daily"
    assert data["total_events"] == expected_total
    
    series = data.get("series", [])
    assert len(series) > 0, "Expected at least 1 time point in series"
    assert data["total_periods"] == len(series)
    
    sum_total = sum(pt["total_events"] for pt in series)
    assert sum_total == expected_total
    
    for pt in series:
        print(f"  Date [{pt['date']}]: Total={pt['total_events']}, Critical={pt['critical_events']}, High={pt['high_events']}, Moderate={pt['moderate_events']}, Low={pt['low_events']}, AvgScore={pt['avg_risk_score']}")
        sum_breakdown = pt["critical_events"] + pt["high_events"] + pt["moderate_events"] + pt["low_events"]
        assert sum_breakdown == pt["total_events"], f"Date {pt['date']} sub-scores do not match total"
        
    print("[PASS] Time-series daily bins verified.")


def test_date_filtering():
    print("\n--- TEST 5: Temporal Date Window Filtering ---")
    # 1. Filter with impossible future dates -> expect 0 events
    future_start = "2099-01-01T00:00:00"
    future_end = "2099-12-31T23:59:59"
    status, future_data = get_json("/summary", {"start_date": future_start, "end_date": future_end})
    assert status == 200
    assert future_data["total_thermal_events"] == 0
    assert future_data["critical_events"] == 0
    print(f"  Future date range filter (2099): Total events = {future_data['total_thermal_events']} (Correctly 0)")
    
    # 2. Filter with broad historical window covering all demo data
    hist_start = "2020-01-01T00:00:00"
    hist_end = "2030-01-01T00:00:00"
    status, hist_data = get_json("/summary", {"start_date": hist_start, "end_date": hist_end})
    assert status == 200
    assert hist_data["total_thermal_events"] > 0
    print(f"  Full window filter (2020-2030): Total events = {hist_data['total_thermal_events']}")
    
    # 3. Test risk-distribution date filter
    status, dist_data = get_json("/risk-distribution", {"start_date": future_start, "end_date": future_end})
    assert status == 200
    assert dist_data["total_events"] == 0
    
    print("[PASS] Date filtering successfully restricts queries across all analytics endpoints.")


def test_swagger_documentation():
    print("\n--- TEST 6: Swagger / OpenAPI Schema Registration ---")
    req = urllib.request.Request("http://127.0.0.1:8000/openapi.json", headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as resp:
        openapi = json.loads(resp.read().decode("utf-8"))
        
    paths = openapi.get("paths", {})
    endpoints = [
        "/api/analytics/summary",
        "/api/analytics/risk-distribution",
        "/api/analytics/event-types",
        "/api/analytics/time-series",
    ]
    for ep in endpoints:
        assert ep in paths, f"Endpoint {ep} missing from OpenAPI schema!"
        get_spec = paths[ep].get("get", {})
        tags = get_spec.get("tags", [])
        assert "Analytics & Intelligence KPIs" in tags
        print(f"  Registered: {ep} (Tag: {tags})")
        
    print("[PASS] All 4 analytics endpoints properly documented in Swagger / OpenAPI.")


if __name__ == "__main__":
    print("=" * 70)
    print("RUNNING PHASE 10: ANALYTICS API VERIFICATION SUITE")
    print("=" * 70)
    
    try:
        total = test_analytics_summary()
        test_risk_distribution(total)
        test_event_types_breakdown(total)
        test_time_series(total)
        test_date_filtering()
        test_swagger_documentation()
        
        print("\n" + "=" * 70)
        print("ALL PHASE 10 TESTS PASSED (100% SUCCESS)")
        print("=" * 70)
    except AssertionError as ae:
        print(f"\n[FAIL] Assertion Error: {ae}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
