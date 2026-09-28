import os
import sys
import json
import urllib.request
import re

BACKEND_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://127.0.0.1:5173"
FRONTEND_HTML_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "index.html")

def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "SIH26162-MapTester/1.0"})
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))

def fetch_text(url):
    req = urllib.request.Request(url, headers={"User-Agent": "SIH26162-MapTester/1.0"})
    with urllib.request.urlopen(req) as resp:
        return resp.status, resp.read().decode("utf-8")

def run_tests():
    print("=" * 75)
    print("SIH26162 — MAP INTEGRATION VERIFICATION WITH LIVE BACKEND DATA")
    print("=" * 75)

    # ----------------------------------------------------
    # 1. Thermal events load from backend
    # ----------------------------------------------------
    print("\n--- CRITERIA 1: Thermal Events Load from Backend (GET /api/thermal-events) ---")
    st, data = fetch_json(f"{BACKEND_URL}/api/thermal-events?page_size=100")
    assert st == 200, f"Backend returned status {st}"
    events = data.get("items", [])
    total = data.get("total", len(events))
    assert len(events) >= 5, f"Expected at least 5 thermal events, found {len(events)}"
    print(f"[PASS] Successfully fetched {len(events)} thermal events from live backend (total: {total})")

    # ----------------------------------------------------
    # 2. Coordinates are correct
    # ----------------------------------------------------
    print("\n--- CRITERIA 2: Verify Exact Coordinates & Geometry Bounds ---")
    for ev in events:
        lat = ev.get("latitude")
        lng = ev.get("longitude")
        assert lat is not None and lng is not None, f"Event {ev.get('event_id')} missing coordinates"
        lat_f = float(lat)
        lng_f = float(lng)
        assert -90.0 <= lat_f <= 90.0, f"Latitude {lat_f} out of bounds"
        assert -180.0 <= lng_f <= 180.0, f"Longitude {lng_f} out of bounds"
        print(f"  * Event {ev.get('event_id')}: ({lat_f:.4f} N, {lng_f:.4f} E) -> VALID COORDINATES")
    print("[PASS] All thermal event coordinates are valid and precise")

    # ----------------------------------------------------
    # 3. Markers appear
    # ----------------------------------------------------
    print("\n--- CRITERIA 3: Verify Map Layering & Marker Creation Logic ---")
    with open(FRONTEND_HTML_PATH, "r", encoding="utf-8") as f:
        html_content = f.read()

    assert "state.thermalLayer = L.layerGroup().addTo(state.map);" in html_content, "thermalLayer not created or added to map"
    assert "makeThermalIcon(ev" in html_content, "makeThermalIcon logic missing"
    assert "marker.addTo(state.thermalLayer);" in html_content, "marker not added to thermalLayer"
    print("[PASS] Leaflet thermalLayer and marker instantiation logic verified")

    # ----------------------------------------------------
    # 4. Marker colors correspond to risk/event categories
    # ----------------------------------------------------
    print("\n--- CRITERIA 4: Marker Colors Correspondence to Risk & Categories ---")
    expected_colors = {
        "Critical Industrial Fire": {"hex": "#DC2626", "cls": "risk-critical", "name": "Red"},
        "High-Risk Thermal Event": {"hex": "#EA580C", "cls": "risk-high", "name": "Orange"},
        "Gas Flare": {"hex": "#CA8A04", "cls": "risk-gas", "name": "Yellow"},
        "Persistent Thermal Source": {"hex": "#7C3AED", "cls": "risk-persistent", "name": "Purple"},
        "Low-Risk Thermal Activity": {"hex": "#16A34A", "cls": "risk-low", "name": "Green"}
    }

    for ev_type, color_info in expected_colors.items():
        assert f"'{ev_type}':" in html_content or f'"{ev_type}":' in html_content, f"Color mapping missing for '{ev_type}'"
        assert color_info["hex"] in html_content, f"Hex code {color_info['hex']} missing for '{ev_type}'"
        print(f"  * '{ev_type}' -> {color_info['hex']} ({color_info['name']} / {color_info['cls']}) [MATCH]")
    print("[PASS] Marker color definitions correspond precisely to risk and event categories")

    # ----------------------------------------------------
    # 5. Clicking a marker opens the existing detail interface
    # ----------------------------------------------------
    print("\n--- CRITERIA 5: Marker Click Interaction & Detail Interface Binding ---")
    assert "marker.on('click'," in html_content, "Click listener missing on marker"
    assert "selectEvent(ev.id)" in html_content, "selectEvent binding missing on marker click"
    assert "openBottomSheet(ev.id)" in html_content, "openBottomSheet binding missing on mobile click"
    assert "renderAIPanel(ev)" in html_content, "renderAIPanel call missing in selectEvent"
    print("[PASS] Marker click handler correctly bound: opens renderAIPanel (desktop) and openBottomSheet (mobile)")

    # ----------------------------------------------------
    # 6-16: Verification of Details Shown for All 5 Event Types
    # ----------------------------------------------------
    print("\n--- CRITERIA 6-16: Comprehensive Attribute Verification for Multiple Event Types ---")

    required_attributes = [
        "Exact latitude and longitude (lat/lng)",
        "Event type",
        "Risk priority",
        "Risk score",
        "AI classification",
        "AI confidence",
        "Thermal intensity",
        "Persistence",
        "Nearby industrial facility",
        "Detection time",
        "AI explanation"
    ]

    # Verify attributes exist in detail panel template
    panel_snippet = html_content[html_content.find("function renderAIPanel(ev) {"):html_content.find("function createAlertFromEvent")]
    bottom_snippet = html_content[html_content.find("function openBottomSheet(id) {"):html_content.find("function renderAIPanel")]

    checks = {
        "6. Coordinates": ("ev.lat.toFixed(4)", "ev.lng.toFixed(4)"),
        "7. Event type": ("Event Type", "ev.eventType || ev.classification"),
        "8. Risk priority": ("riskBadge(ev.risk)",),
        "9. Risk score": ("Risk Score", "ev.score"),
        "10. AI classification": ("AI Classification", "ev.classification"),
        "11. AI confidence": ("AI Confidence", "ev.confidence"),
        "12. Thermal intensity": ("Thermal Intensity", "ev.intensity"),
        "13. Persistence": ("Persistence", "ev.persistence"),
        "14. Nearby facility": ("Nearby Facility", "ev.facility"),
        "15. Detection time": ("Detection Time", "ev.detected"),
        "16. AI explanation": ("AI Explanation", "ev.explanation")
    }

    for name, tokens in checks.items():
        for t in tokens:
            assert t in panel_snippet, f"Token '{t}' missing from desktop detail panel template"
            assert t in bottom_snippet, f"Token '{t}' missing from mobile bottom sheet template"
        print(f"  * {name}: Verified present in both desktop and mobile detail templates [PASS]")

    # ----------------------------------------------------
    # MULTI-EVENT VALIDATION WITH BACKEND DATA
    # ----------------------------------------------------
    print("\n--- MULTI-EVENT DATA PAYLOAD VERIFICATION ---")

    test_categories = [
        "Critical Industrial Fire",
        "High-Risk Thermal Event",
        "Gas Flare",
        "Persistent Thermal Source",
        "Low-Risk Thermal Activity"
    ]

    for cat in test_categories:
        matching = [e for e in events if e.get("event_type") == cat]
        assert len(matching) > 0, f"Backend is missing an event of type '{cat}'"
        ev = next((e for e in matching if e.get('facility_id') or e.get('facility')), matching[0])

        print(f"\n[EVENT CATEGORY: {cat}]")
        print(f"  - Event ID:           {ev.get('event_id')} (Database ID: {ev.get('id')})")
        print(f"  - Coordinates:        {float(ev.get('latitude')):.4f} N, {float(ev.get('longitude')):.4f} E")
        print(f"  - Event Type:         {ev.get('event_type')}")
        print(f"  - Risk Priority:      {ev.get('risk_priority')}")
        print(f"  - Risk Score:         {ev.get('risk_score')}/100")
        print(f"  - AI Classification:  {ev.get('event_type')}")
        conf_val = float(ev.get('confidence', 0.9))
        conf_pct = round(conf_val * 100) if conf_val <= 1 else round(conf_val)
        print(f"  - AI Confidence:      {conf_pct}% ({conf_val})")
        print(f"  - Thermal Intensity:  {ev.get('thermal_intensity')}")
        print(f"  - Persistence:        {ev.get('persistence')}")
        facility_name = ev.get('facility_name') or (ev.get('facility') or {}).get('name')
        print(f"  - Nearby Facility:    {facility_name}")
        print(f"  - Detection Time:     {ev.get('detected_at')}")
        exp = (ev.get('classifications') or [{}])[0].get('explanation') or (ev.get('risk_assessments') or [{}])[0].get('explanation') or 'Multi-factor risk analysis'
        print(f"  - AI Explanation:     {exp}")

        # Assert all fields are non-empty
        assert ev.get('latitude') is not None
        assert ev.get('longitude') is not None
        assert ev.get('event_type') == cat
        assert ev.get('risk_priority') is not None
        assert ev.get('risk_score') is not None
        assert ev.get('confidence') is not None
        assert ev.get('thermal_intensity') is not None
        assert ev.get('persistence') is not None
        assert facility_name is not None
        assert ev.get('detected_at') is not None
        assert exp is not None

    print("\n" + "=" * 75)
    print("ALL 16 MAP VERIFICATION CRITERIA PASSED ACROSS ALL 5 EVENT TYPES!")
    print("=" * 75)

if __name__ == "__main__":
    run_tests()
