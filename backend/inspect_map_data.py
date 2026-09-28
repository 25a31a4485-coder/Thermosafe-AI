import urllib.request
import json

resp = urllib.request.urlopen("http://127.0.0.1:8000/api/thermal-events?page_size=100")
data = json.loads(resp.read().decode())
print(f"Total backend thermal events: {data.get('total', len(data.get('items', [])))}")
for item in data.get('items', []):
    print(f"ID={item.get('id')}, EventID={item.get('event_id')}, Type='{item.get('event_type')}', Risk={item.get('risk_priority')}, Score={item.get('risk_score')}, Lat={item.get('latitude')}, Lng={item.get('longitude')}, Conf={item.get('confidence')}, Intensity={item.get('thermal_intensity')}, Persistence={item.get('persistence')}, Facility={item.get('facility_name') or (item.get('facility') or {}).get('name')}")
