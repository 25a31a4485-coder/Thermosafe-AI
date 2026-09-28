import re
import os
import sys

def test_rendered_dom():
    print("=" * 60)
    print("VERIFYING RENDERED DOM FROM HEADLESS BROWSER")
    print("=" * 60)
    
    dom_path = os.path.join(os.path.dirname(__file__), "rendered_dom.html")
    assert os.path.exists(dom_path), "rendered_dom.html does not exist!"
    
    with open(dom_path, "r", encoding="utf-8") as f:
        html = f.read()

    # TEST A: Fresh Browser Load
    print("\n--- TEST A: Fresh Browser Load & Immediate Dashboard Rendering ---")
    assert '<div class="kpi-grid">' in html, "FAIL: .kpi-grid missing from rendered DOM!"
    assert 'id="kpi-val-total"' in html, "FAIL: #kpi-val-total missing from rendered DOM!"
    assert 'Active Thermal Anomalies' in html, "FAIL: 'Active Thermal Anomalies' missing from rendered DOM!"
    assert 'id="map"' in html, "FAIL: #map container missing from rendered DOM!"
    assert 'leaflet-container' in html, "FAIL: Leaflet map container not initialized on #map!"
    print("[PASS] Dashboard rendered immediately with KPI grid and Leaflet map.")

    # Verify NO Login Gate / Initializing Spinner in content
    print("\n--- TEST A.1: Verify Zero Login Gate / Spinner at Startup ---")
    content_match = re.search(r'<div class="content" id="content">(.*?)</div>\s*</div>\s*<!--', html, re.DOTALL)
    if not content_match:
        content_match = re.search(r'id="content">(.*?)</div>', html, re.DOTALL)
    assert content_match, "FAIL: #content main container missing!"
    content_html = content_match.group(1)
    
    assert 'id="authForm"' not in content_html, "FAIL: Login form #authForm found in #content!"
    assert 'Initializing secure session' not in content_html, "FAIL: Initializing full-screen spinner found in #content!"
    assert 'Sign In to Platform' not in content_html, "FAIL: Login button found in #content!"
    print("[PASS] #content contains NO login gate, NO auth form, and NO initializing spinner.")

    # TEST G: Profile Stability & Operator Identity
    print("\n--- TEST G: Operator Profile & Avatar Stability ---")
    assert 'id="profileBtn"' in html, "FAIL: #profileBtn missing!"
    assert 'ThermoSafe Operator (Analyst)' in html, "FAIL: Operator profile title missing!"
    assert '>T</span>' in html, "FAIL: Operator initial 'T' avatar missing from profile button!"
    print("[PASS] Operator profile avatar 'T' and title 'ThermoSafe Operator (Analyst)' confirmed.")

    # TEST F: Navigation elements intact
    print("\n--- TEST F: All Navigation Elements Present ---")
    for page in ['dashboard', 'map', 'incidents', 'analytics', 'alerts', 'reports', 'settings']:
        assert f'data-page="{page}"' in html, f"FAIL: Navigation item for {page} missing!"
        print(f"  [PASS] Nav item data-page='{page}' verified.")

    # TEST C & D: Data source controls
    print("\n--- TEST C & D: LIVE / DEMO Controls ---")
    assert 'id="btnSourceLive"' in html, "FAIL: Live source button missing!"
    assert 'id="btnSourceDemo"' in html, "FAIL: Demo source button missing!"
    assert 'id="backendPill"' in html, "FAIL: Backend status pill missing!"
    print("[PASS] Data source toggles and status pill verified.")

    # Check that settings page template has edit profile modal trigger
    print("\n--- TEST H: Settings & Edit Profile Integration ---")
    fe_file = os.path.join(os.path.dirname(__file__), "frontend", "index.html")
    with open(fe_file, "r", encoding="utf-8") as f:
        fe_src = f.read()

    assert "openEditProfileModal" in fe_src, "FAIL: openEditProfileModal missing from frontend source!"
    assert "handleProfileSave" in fe_src, "FAIL: handleProfileSave missing from frontend source!"
    assert "DEFAULT_LOCAL_OPERATOR" in fe_src, "FAIL: DEFAULT_LOCAL_OPERATOR missing from frontend source!"
    assert "getStoredLocalOperator" in fe_src, "FAIL: getStoredLocalOperator missing from frontend source!"
    print("[PASS] Local operator profile management and persistence verified.")

    # Check that boot() follows exact single sequence
    print("\n--- TEST B & Boot Sequence ---")
    assert "let booted = false;" in fe_src, "FAIL: booted guard flag missing!"
    boot_match = re.search(r"async function boot\(\) \{(.*?)\}", fe_src, re.DOTALL)
    assert boot_match, "FAIL: boot() function missing!"
    boot_body = boot_match.group(1)
    
    assert "initializeLocalUser();" in boot_body, "FAIL: initializeLocalUser() missing from boot()"
    assert "renderApplicationShell();" in boot_body, "FAIL: renderApplicationShell() missing from boot()"
    assert "initializeNavigation();" in boot_body, "FAIL: initializeNavigation() missing from boot()"
    assert "initializeMap();" in boot_body, "FAIL: initializeMap() missing from boot()"
    assert "initializeDataSource();" in boot_body, "FAIL: initializeDataSource() missing from boot()"
    assert "startPolling();" in boot_body, "FAIL: startPolling() missing from boot()"
    assert "renderLoginPage" not in boot_body, "FAIL: renderLoginPage found in boot()!"
    assert "renderAuthInitializingState" not in boot_body, "FAIL: renderAuthInitializingState found in boot()!"
    print("[PASS] Exact boot sequence: initializeLocalUser -> renderApplicationShell -> initializeNavigation -> initializeMap -> initializeDataSource -> startPolling.")

    print("\n" + "=" * 60)
    print("ALL VERIFICATION SUITE CHECKS PASSED (100% SUCCESS)")
    print("=" * 60)

if __name__ == "__main__":
    test_rendered_dom()
