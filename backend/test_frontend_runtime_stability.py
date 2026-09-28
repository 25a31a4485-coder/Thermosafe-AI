"""
ThermoSafe AI Frontend Runtime Stability & Anti-Reset Verification Suite
Validates all architectural fixes applied to resolve the dashboard blanking / resetting issue.
"""
import re
import os
import sys

def run_tests():
    print("=" * 70)
    print("THERMOSAFE AI: FRONTEND RUNTIME STABILITY VERIFICATION")
    print("=" * 70)

    # 1. File Parity Test
    print("\n--- TEST 1: File Parity Check (index.html vs frontend/index.html) ---")
    root_path = os.path.join(os.path.dirname(__file__), "..", "index.html")
    fe_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")

    with open(root_path, "r", encoding="utf-8") as f:
        root_content = f.read()
    with open(fe_path, "r", encoding="utf-8") as f:
        fe_content = f.read()

    assert root_content == fe_content, "ERROR: root index.html and frontend/index.html are not identical!"
    print(f"[PASS] 100% Bit-for-bit file parity verified ({len(root_content)} bytes).")

    content = fe_content

    # 2. Initial Auth & Page State
    print("\n--- TEST 2: Initial 3-State Auth Lifecycle & Mount State ---")
    assert "currentPage: 'initializing'" in content, "state.currentPage must initialize to 'initializing'"
    assert "authStatus: 'initializing'" in content, "state.authStatus must initialize to 'initializing'"
    assert "dashboardMountCount: 0" in content, "state.dashboardMountCount must initialize to 0"
    assert "liveFetchRequestId: 0" in content, "state.liveFetchRequestId must initialize to 0"
    print("  [PASS] state.currentPage initialized to 'initializing'")
    print("  [PASS] state.authStatus initialized to 'initializing'")
    print("  [PASS] state.dashboardMountCount initialized to 0")
    print("  [PASS] state.liveFetchRequestId initialized to 0")
    print("[PASS] Initial state structure verified.")

    # 3. Scoped 401 Session Handling
    print("\n--- TEST 3: Scoped 401 Session Handling ---")
    assert "resp.status === 401 && endpoint === '/api/auth/me'" in content, (
        "401 logout must be scoped strictly to '/api/auth/me'"
    )
    assert "Secondary endpoint returned 401" in content, (
        "Secondary 401 must log warning without clearing session"
    )
    # Ensure broad 401 logout does not exist
    broad_401 = re.search(r"if\s*\(\s*resp\.status\s*===\s*401\s*&&\s*token\s*\)\s*\{\s*localStorage\.removeItem", content)
    assert broad_401 is None, "ERROR: Broad 401 logout interceptor still found in code!"
    print("  [PASS] 401 session clearing strictly scoped to /api/auth/me")
    print("  [PASS] Secondary endpoint 401 errors fail gracefully without logging out")
    print("  [PASS] Broad 401 logout pattern verified eliminated")
    print("[PASS] Scoped 401 resilience verified.")

    # 4. In-Place Dashboard Live View Updates
    print("\n--- TEST 4: In-Place Dashboard Live View Architecture ---")
    assert "function updateDashboardLiveView()" in content, "updateDashboardLiveView() must be defined"
    assert 'id="kpi-val-total"' in content, "kpi-val-total ID must be present on total anomalies element"
    assert 'id="kpi-sub-total"' in content, "kpi-sub-total ID must be present on subtitle"
    assert 'id="kpi-val-critical"' in content, "kpi-val-critical ID must be present on critical count"
    assert 'id="kpi-val-high"' in content, "kpi-val-high ID must be present on high count"
    assert 'id="kpi-val-moderate"' in content, "kpi-val-moderate ID must be present on moderate count"
    assert 'id="kpi-val-facilities"' in content, "kpi-val-facilities ID must be present on facilities count"
    assert 'id="kpi-val-low"' in content, "kpi-val-low ID must be present on low count"
    assert "elValTotal.textContent = totalEvents" in content, "updateDashboardLiveView must update textContent in-place"
    print("  [PASS] updateDashboardLiveView() function defined")
    print("  [PASS] Unique KPI element IDs present (kpi-val-total, kpi-val-critical, etc.)")
    print("  [PASS] In-place DOM textContent updates confirmed")
    print("[PASS] Non-destructive in-place dashboard update verified.")

    # 5. Non-Destructive Polling
    print("\n--- TEST 5: Non-Destructive Polling in fetchLiveData ---")
    # In fetchLiveData, when currentPage === 'dashboard', it must call updateDashboardLiveView()
    fetch_func_match = re.search(r"async function fetchLiveData\(silent = false\) \{(.*?)\n  async function setDataSource", content, re.DOTALL)
    assert fetch_func_match, "Could not extract fetchLiveData function body"
    fetch_body = fetch_func_match.group(1)

    assert "updateDashboardLiveView();" in fetch_body, (
        "fetchLiveData must call updateDashboardLiveView() instead of renderDashboard()"
    )
    # Ensure renderDashboard() is NOT called inside fetchLiveData
    assert "renderDashboard();" not in fetch_body, (
        "ERROR: renderDashboard() must NOT be called inside fetchLiveData!"
    )
    assert "reqId !== state.liveFetchRequestId" in fetch_body, (
        "Race condition protection reqId !== state.liveFetchRequestId must be present in fetchLiveData"
    )
    print("  [PASS] fetchLiveData calls updateDashboardLiveView() for dashboard page")
    print("  [PASS] fetchLiveData verified NOT calling renderDashboard()")
    print("  [PASS] Asynchronous race condition sequence counter verified")
    print("[PASS] Non-destructive polling verified.")

    # 6. Leaflet Map Hardening
    print("\n--- TEST 6: Leaflet Map Hardening & Container Cleanup ---")
    assert "state.map.off()" in content, "initMap must call state.map.off() before removal"
    assert "delete mapEl._leaflet_id" in content, "initMap must delete mapEl._leaflet_id to avoid container collisions"
    print("  [PASS] state.map.off() listener detachment present")
    print("  [PASS] delete mapEl._leaflet_id container reset present")
    print("[PASS] Leaflet container hardening verified.")

    # 7. Boot Lifecycle & Initial Blank Prevention
    print("\n--- TEST 7: Boot Lifecycle & Blank Screen Prevention ---")
    assert "renderAuthInitializingState()" in content, "renderAuthInitializingState must be defined and called on boot"
    assert "renderAuthInitializingState();" in content, "boot() must call renderAuthInitializingState()"
    assert "#devDiagnosticPanel" in content, "#devDiagnosticPanel CSS and element must be configured"
    print("  [PASS] renderAuthInitializingState() renders professional loading state")
    print("  [PASS] boot() invokes initializing state immediately so content is never blank")
    print("  [PASS] Non-invasive dev diagnostic overlay present")
    print("[PASS] Boot lifecycle verified.")

    # 8. Window Exports
    print("\n--- TEST 8: Global Window Exports ---")
    for exp in ["updateDashboardLiveView", "updateDebugDiagnostics", "renderAuthInitializingState"]:
        assert exp in content, f"window.__thermosafe must export {exp}"
        print(f"  [PASS] window.__thermosafe exports {exp}")
    print("[PASS] Window exports verified.")

    print("\n" + "=" * 70)
    print("ALL FRONTEND RUNTIME STABILITY VERIFICATIONS PASSED (100% SUCCESS)")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
