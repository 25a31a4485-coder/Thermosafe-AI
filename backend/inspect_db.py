import sqlite3
from datetime import datetime, timezone, timedelta

def inspect():
    conn = sqlite3.connect('sih26162.db')
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cursor.fetchall()]
    print("Database tables:", tables)

    cursor.execute('SELECT COUNT(*) FROM thermal_events')
    total = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM thermal_events WHERE is_demo = 0')
    live_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM thermal_events WHERE is_demo = 1')
    demo_count = cursor.fetchone()[0]

    now = datetime.now(timezone.utc)
    d24 = (now - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
    d7 = (now - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('SELECT COUNT(*) FROM thermal_events WHERE created_at >= ?', (d24,))
    c24 = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM thermal_events WHERE created_at >= ?', (d7,))
    c7 = cursor.fetchone()[0]

    cursor.execute('SELECT MIN(detected_at), MAX(detected_at), MIN(created_at), MAX(created_at) FROM thermal_events')
    timestamps = cursor.fetchone()

    print(f"Total thermal events in DB: {total}")
    print(f"Live events (is_demo=0): {live_count}")
    print(f"Demo events (is_demo=1): {demo_count}")
    print(f"Created in last 24h: {c24}")
    print(f"Created in last 7 days: {c7}")
    print(f"Earliest detected_at: {timestamps[0]}, Latest detected_at: {timestamps[1]}")
    print(f"Earliest created_at: {timestamps[2]}, Latest created_at: {timestamps[3]}")

    cursor.execute('SELECT id, event_id, event_type, is_demo, data_source, detected_at FROM thermal_events LIMIT 10')
    print("Sample records:")
    for row in cursor.fetchall():
        print(" ", row)

if __name__ == '__main__':
    inspect()
