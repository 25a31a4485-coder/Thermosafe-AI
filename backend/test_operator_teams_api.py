import urllib.request
import json
import sys

BASE = 'http://127.0.0.1:8000/api'

# 1. Create Team
team_payload = {
    'team_name': 'Hazmat Rapid Response Unit 7',
    'facility_name': 'Jamnagar Petrochemical Complex',
    'facility_type': 'Petrochemical',
    'latitude': 22.47,
    'longitude': 70.06,
    'team_email': 'hazmat7@jamnagar-refinery.in',
    'team_phone': '+91-288-2998877',
    'specialization': 'Hazmat & Industrial Fire',
    'team_members': ['Commander Vikram S.', 'Specialist Anita R.'],
    'is_active': True,
    'notification_enabled': True,
    'call_escalation_enabled': True
}

req = urllib.request.Request(f'{BASE}/operator-teams', data=json.dumps(team_payload).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
with urllib.request.urlopen(req) as resp:
    created = json.loads(resp.read().decode())
    team_id = created['id']
    print(f"[PASS] Created Operator Team ID {team_id}: {created['name']}, Call Escalation={created.get('call_escalation_enabled')}")

# 2. Get Team
with urllib.request.urlopen(f'{BASE}/operator-teams/{team_id}') as resp:
    team_detail = json.loads(resp.read().decode())
    assert team_detail['id'] == team_id
    print(f"[PASS] Retrieved Operator Team ID {team_id}: {team_detail['name']}")

# 3. Edit Team
edit_payload = {
    'team_name': 'Hazmat Rapid Response Unit 7 (Updated)',
    'team_phone': '+91-288-2998899',
    'specialization': 'Advanced Chemical Hazmat'
}
req = urllib.request.Request(f'{BASE}/operator-teams/{team_id}', data=json.dumps(edit_payload).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='PUT')
with urllib.request.urlopen(req) as resp:
    updated = json.loads(resp.read().decode())
    assert updated['name'] == 'Hazmat Rapid Response Unit 7 (Updated)'
    print(f"[PASS] Updated Operator Team ID {team_id}: {updated['name']}, Phone={updated['phone']}")

# 4. Toggle Active
req = urllib.request.Request(f'{BASE}/operator-teams/{team_id}/toggle-active', headers={'Content-Type': 'application/json'}, method='PATCH')
with urllib.request.urlopen(req) as resp:
    toggled = json.loads(resp.read().decode())
    assert toggled['is_active'] is False
    print(f"[PASS] Toggled active status for Team ID {team_id}: is_active={toggled['is_active']}")

# 5. Escalate an alert (Already acknowledged)
alerts = json.loads(urllib.request.urlopen(f'{BASE}/alerts').read().decode())['items']
if alerts:
    al_id = alerts[0]['id']
    req = urllib.request.Request(f'{BASE}/alerts/{al_id}/escalate', headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req) as resp:
        esc = json.loads(resp.read().decode())
        print(f"[PASS] Escalation endpoint for Alert ID {al_id}: Status={esc.get('status')}, Telephony={esc.get('telephony_mode') or esc.get('reason')}")

# 6. Escalate an unacknowledged Critical alert
unack_alert = {
    'title': 'CRITICAL TEST REFINERY FIRE',
    'message': 'Thermal hotspot 850MW detected near petrochemical storage.',
    'severity': 'Critical',
    'risk_score': 92.0,
    'risk_priority': 'CRITICAL',
    'latitude': 22.47,
    'longitude': 70.06,
    'event_type': 'Industrial Fire',
    'is_read': False
}
req = urllib.request.Request(f'{BASE}/alerts', data=json.dumps(unack_alert).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
with urllib.request.urlopen(req) as resp:
    new_al = json.loads(resp.read().decode())
    new_al_id = new_al['id']

req = urllib.request.Request(f'{BASE}/alerts/{new_al_id}/escalate', headers={'Content-Type': 'application/json'}, method='POST')
with urllib.request.urlopen(req) as resp:
    esc_result = json.loads(resp.read().decode())
    assert esc_result['status'] == 'ESCALATED'
    assert esc_result['telephony_mode'] == 'SIMULATED_MOCK_TELEPHONY'
    assert 'SIMULATED' in esc_result['message']
    print(f"[PASS] Unacknowledged Critical Alert #{new_al_id} triggered simulated telephony escalation to {esc_result['team_name']} ({esc_result['target_phone']}).")

print("ALL OPERATOR TEAM AND ESCALATION TESTS PASSED SUCCESSFULLY!")
