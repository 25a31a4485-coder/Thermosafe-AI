"""
Direct Python verification of NASA FIRMS API.
Tests live connection, endpoint syntax, response codes, and CSV parsing
WITHOUT leaking any MAP_KEY or credentials.
"""

import sys
import os
import urllib.request
import urllib.error
import socket
import csv
import io

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.config import settings

def mask_key(text: str, key: str) -> str:
    if not key or len(key) < 4:
        return text
    return text.replace(key, f"{key[:2]}...[REDACTED]...{key[-2:]}")

def test_direct_nasa(source: str = "VIIRS_NOAA21_NRT", area: str = "world", day_range: int = 1):
    map_key = settings.effective_firms_map_key
    base_url = settings.NASA_FIRMS_BASE_URL.rstrip("/")
    timeout = settings.NASA_FIRMS_TIMEOUT_SECONDS

    if not map_key:
        print("KEY_CONFIGURED = false")
        print("NASA_HTTP_STATUS = N/A")
        print("EVENT_COUNT = 0")
        print("ERROR = NASA FIRMS MAP KEY IS NOT CONFIGURED (backend/.env FIRMS_MAP_KEY is empty)")
        return {
            "key_configured": False,
            "status": None,
            "event_count": 0,
            "error": "NASA FIRMS MAP KEY IS NOT CONFIGURED"
        }

    url = f"{base_url}/api/area/csv/{map_key}/{source}/{area}/{day_range}"
    safe_url = mask_key(url, map_key)

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "ThermoSafe-AI/1.0 (Industrial Thermal Intelligence Backend)",
            "Accept": "text/csv, application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status_code = response.status
            raw_bytes = response.read()
            text = raw_bytes.decode("utf-8", errors="replace").strip()

        # Check for NASA textual error messages inside 200 response
        first_line = text.split("\n")[0] if text else ""
        if "Invalid MAP_KEY" in first_line or "Transaction limit" in first_line or "Invalid API call" in first_line:
            print("KEY_CONFIGURED = true")
            print(f"NASA_HTTP_STATUS = {status_code} (NASA inline rejection)")
            print("EVENT_COUNT = 0")
            print(f"ERROR = {first_line}")
            return {"key_configured": True, "status": status_code, "event_count": 0, "error": first_line}

        # Parse CSV lines
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        print("KEY_CONFIGURED = true")
        print(f"NASA_HTTP_STATUS = {status_code}")
        print(f"EVENT_COUNT = {len(rows)}")
        print("ERROR = None")
        return {"key_configured": True, "status": status_code, "event_count": len(rows), "error": None}

    except urllib.error.HTTPError as he:
        err_body = ""
        try:
            err_body = he.read().decode("utf-8", errors="replace").strip().split("\n")[0]
        except Exception:
            pass
        detail = f" - {err_body}" if err_body else ""
        safe_err = mask_key(f"HTTP {he.code} {he.reason}{detail}", map_key)
        print("KEY_CONFIGURED = true")
        print(f"NASA_HTTP_STATUS = {he.code}")
        print("EVENT_COUNT = 0")
        print(f"ERROR = {safe_err}")
        return {"key_configured": True, "status": he.code, "event_count": 0, "error": safe_err}

    except urllib.error.URLError as ue:
        safe_err = mask_key(str(ue.reason), map_key)
        print("KEY_CONFIGURED = true")
        print("NASA_HTTP_STATUS = Connection Failed")
        print("EVENT_COUNT = 0")
        print(f"ERROR = URLError: {safe_err}")
        return {"key_configured": True, "status": None, "event_count": 0, "error": safe_err}

    except (socket.timeout, TimeoutError):
        print("KEY_CONFIGURED = true")
        print("NASA_HTTP_STATUS = Timeout")
        print("EVENT_COUNT = 0")
        print(f"ERROR = Request timed out after {timeout} seconds")
        return {"key_configured": True, "status": None, "event_count": 0, "error": "Timeout"}

    except Exception as ex:
        safe_err = mask_key(str(ex), map_key)
        print("KEY_CONFIGURED = true")
        print("NASA_HTTP_STATUS = Exception")
        print("EVENT_COUNT = 0")
        print(f"ERROR = {type(ex).__name__}: {safe_err}")
        return {"key_configured": True, "status": None, "event_count": 0, "error": safe_err}

def run_all_tests():
    print("==================================================")
    print("NASA FIRMS DIRECT API VERIFICATION (NOAA-21, NOAA-20, SNPP)")
    print("==================================================")
    
    sources = ["VIIRS_NOAA21_NRT", "VIIRS_NOAA20_NRT", "VIIRS_SNPP_NRT"]
    for src in sources:
        print(f"\n--- Testing Source: {src} (area=world, days=1) ---")
        test_direct_nasa(source=src, area="world", day_range=1)

if __name__ == "__main__":
    run_all_tests()
