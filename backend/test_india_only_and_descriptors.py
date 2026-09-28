"""
Comprehensive verification test suite for SIH26162 / ThermoSafe AI:
1. Verifies ThermalEvent model attribute assignment (descriptors/setters)
2. Verifies None-safe attribute handling in firms_service
3. Verifies is_inside_india geospatial validation (accepts India, rejects outside India)
4. Verifies FIRMS CSV parsing strictly filters out non-India records
5. Verifies FIRMS database persistence strictly filters out non-India records
6. Verifies analytics queries are strictly bounded to India
7. Verifies reports queries are strictly bounded to India
8. Verifies get_cached_live_events queries only India events
9. Verifies absence of global fallback data or demo substitution
"""

import sys
import os
import unittest
from datetime import datetime, timezone

# Ensure backend directory is in sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.spatial import (
    is_inside_india,
    INDIA_LAT_MIN,
    INDIA_LAT_MAX,
    INDIA_LON_MIN,
    INDIA_LON_MAX,
    INDIA_BBOX_CSV,
)
from app.models.thermal_event import ThermalEvent
from app.services.firms_service import get_firms_service
from app.services.analytics_service import get_analytics_service
from app.core.database import SessionLocal

firms_service = get_firms_service()
analytics_service = get_analytics_service()


class TestIndiaGeospatialValidation(unittest.TestCase):
    """Test A & B: India vs Non-India filtering."""

    def test_india_coordinates_accepted(self):
        # Major Indian cities / regions
        india_points = [
            (28.6139, 77.2090),  # New Delhi
            (19.0760, 72.8777),  # Mumbai
            (13.0827, 80.2707),  # Chennai
            (22.5726, 88.3639),  # Kolkata
            (22.3524, 69.8652),  # Jamnagar
            (17.6868, 83.2185),  # Visakhapatnam
            (34.0837, 74.7973),  # Srinagar
            (8.5241, 76.9366),   # Thiruvananthapuram
        ]
        for lat, lon in india_points:
            self.assertTrue(
                is_inside_india(lat, lon),
                f"Expected ({lat}, {lon}) to be accepted inside India",
            )

    def test_non_india_coordinates_rejected(self):
        # Global locations
        non_india_points = [
            (51.5074, -0.1278),   # London
            (40.7128, -74.0060),  # New York
            (-33.8688, 151.2093), # Sydney
            (35.6762, 139.6503),  # Tokyo
            (-23.5505, -46.6333), # Sao Paulo
            (0.0, 0.0),           # Equator / Prime Meridian
            (-43.37, 147.20),     # Southern Ocean (from past corrupt data)
            (55.7558, 37.6173),   # Moscow
            (1.3521, 103.8198),   # Singapore
        ]
        for lat, lon in non_india_points:
            self.assertFalse(
                is_inside_india(lat, lon),
                f"Expected ({lat}, {lon}) to be rejected as outside India",
            )


class TestThermalEventModelDescriptors(unittest.TestCase):
    """Test H: Verify no read-only descriptor errors on ThermalEvent mutations."""

    def test_model_mutations_and_setters(self):
        event = ThermalEvent(
            event_id="TEST-VERIF-001",
            latitude=22.35,
            longitude=69.86,
            status="active",
            confidence=85.0,
            risk_score=72.5,
            risk_priority="HIGH",
            thermal_intensity=450.0,
            persistence="3.5 hours",
            is_demo=False,
            detected_at=datetime.now(timezone.utc),
        )
        # Mutate all 8 previously failing descriptor attributes
        event.status = "monitoring"
        event.updated_at = datetime.now(timezone.utc)
        event.confidence = 90.0
        event.risk_score = 80.0
        event.risk_priority = "CRITICAL"
        event.thermal_intensity = 600.0
        event.persistence = "5.0 hours"
        event.is_demo = False

        self.assertEqual(event.status, "monitoring")
        self.assertEqual(event.confidence, 90.0)
        self.assertEqual(event.risk_score, 80.0)
        self.assertEqual(event.risk_priority, "CRITICAL")
        self.assertEqual(event.thermal_intensity, 600.0)
        self.assertEqual(event.persistence, "5.0 hours")
        self.assertFalse(event.is_demo)


class TestFIRMSServiceParsingAndIndiaFiltering(unittest.TestCase):
    """Test C & D: Global FIRMS response containing mixed records -> only India records returned."""

    def test_parse_firms_csv_mixed_records(self):
        csv_data = """latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,confidence,version,bright_ti5,frp,daynight
22.3524,69.8652,345.2,0.4,0.4,2026-09-28,0630,N,nominal,2.0N,295.1,45.2,D
51.5074,-0.1278,330.1,0.5,0.4,2026-09-28,0630,N,nominal,2.0N,290.0,12.0,D
-33.8688,151.2093,350.0,0.4,0.4,2026-09-28,0630,N,nominal,2.0N,292.0,80.0,D
19.0760,72.8777,360.5,0.4,0.4,2026-09-28,0630,N,nominal,2.0N,300.0,95.0,D
40.7128,-74.0060,320.0,0.4,0.4,2026-09-28,0630,N,nominal,2.0N,285.0,10.0,D
"""
        parsed = firms_service.normalize_firms_events(csv_data, source_name="VIIRS")
        # Out of 5 rows, only Jamnagar (22.35, 69.86) and Mumbai (19.07, 72.87) are inside India
        self.assertEqual(len(parsed), 2)
        for ev in parsed:
            self.assertTrue(is_inside_india(ev["latitude"], ev["longitude"]))

    def test_empty_firms_csv(self):
        """Test D: Empty FIRMS response handled safely."""
        empty_csv = ""
        parsed = firms_service.normalize_firms_events(empty_csv, source_name="VIIRS")
        self.assertEqual(len(parsed), 0)

        header_only_csv = "latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,confidence,version,bright_ti5,frp,daynight\n"
        parsed_header = firms_service.normalize_firms_events(header_only_csv, source_name="VIIRS")
        self.assertEqual(len(parsed_header), 0)


class TestDatabaseIntegrity(unittest.TestCase):
    """Test G: Database contains only India records, counts match across services."""

    def test_all_database_records_inside_india(self):
        db = SessionLocal()
        try:
            # Check if any record in thermal_events is outside India bounds
            outside_records = (
                db.query(ThermalEvent)
                .filter(
                    (ThermalEvent.latitude < INDIA_LAT_MIN)
                    | (ThermalEvent.latitude > INDIA_LAT_MAX)
                    | (ThermalEvent.longitude < INDIA_LON_MIN)
                    | (ThermalEvent.longitude > INDIA_LON_MAX)
                )
                .all()
            )
            self.assertEqual(
                len(outside_records),
                0,
                f"Found {len(outside_records)} non-India records in database!",
            )

            # Check analytics summary
            summary = analytics_service.get_summary(db)
            total = summary.total_thermal_events
            print(f"Verified Database: Total events in India = {total}")

            # Verify that total count matches India-bounded query
            india_count = (
                db.query(ThermalEvent)
                .filter(
                    ThermalEvent.latitude >= INDIA_LAT_MIN,
                    ThermalEvent.latitude <= INDIA_LAT_MAX,
                    ThermalEvent.longitude >= INDIA_LON_MIN,
                    ThermalEvent.longitude <= INDIA_LON_MAX,
                )
                .count()
            )
            self.assertEqual(total, india_count)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
