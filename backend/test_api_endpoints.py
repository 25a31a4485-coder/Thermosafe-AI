import urllib.request
import json
import sys

endpoints = [
    '/health',
    '/api/satellite/thermal-events?mode=live',
    '/api/thermal-events?page_size=100',
    '/api/analytics/summary',
    '/api/analytics/risk-distribution',
    '/api/analytics/event-types',
]

base = 'http://localhost:8000'
all_ok = True

for ep in endpoints:
    url = base + ep
    req = urllib.request.Request(url, headers={'User-Agent': 'ThermoSafe-Test'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            status = resp.status
            if 'items' in data:
                print(f"{ep} -> HTTP {status}, items count = {len(data['items'])}")
            elif 'events' in data:
                print(f"{ep} -> HTTP {status}, events count = {len(data['events'])} (status: {data.get('status')})")
            elif 'total_thermal_events' in data:
                print(f"{ep} -> HTTP {status}, total_thermal_events = {data['total_thermal_events']}")
            elif 'total_events' in data:
                print(f"{ep} -> HTTP {status}, total_events = {data['total_events']}")
            else:
                print(f"{ep} -> HTTP {status}, keys = {list(data.keys())[:4]}")
    except Exception as e:
        print(f"{ep} -> ERROR: {e}")
        all_ok = False

if all_ok:
    print("\nALL HTTP ENDPOINTS PASSED SUCCESSFULLY!")
else:
    print("\nSOME ENDPOINTS FAILED")
    sys.exit(1)
