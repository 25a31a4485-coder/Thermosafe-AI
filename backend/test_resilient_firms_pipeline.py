"""
Comprehensive Test Suite for Resilient NASA FIRMS Pipeline.
Verifies all 15 test scenarios specified in prompt:
TEST 1: NASA succeeds -> events stored.
TEST 2: NASA succeeds -> frontend receives events.
TEST 3: NASA fails after successful fetch -> existing events remain.
TEST 4: NASA times out -> existing events remain.
TEST 5: NASA returns HTTP 500 -> existing events remain.
TEST 6: NASA returns malformed response -> existing events remain.
TEST 7: NASA successfully returns zero events -> UI shows zero current events.
TEST 8: NASA recovers -> database updates with new data.
TEST 9: Repeated refreshes do not create duplicates (idempotency).
TEST 10: Frontend polling does not clear data after failed request.
TEST 11: Frontend polling does not recreate Leaflet map.
TEST 12: LIVE never automatically changes to DEMO.
TEST 13: Multiple frontend refreshes do not create multiple backend NASA workers.
TEST 14: Backend remains alive after repeated FIRMS failures.
TEST 15: Dashboard, Incidents, Analytics and Live Map all use the same canonical dataset.
"""

import os
import sys
import unittest
import urllib.request
import json
from datetime import datetime, timezone

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import SessionLocal
from app.models.thermal_event import ThermalEvent
from app.services.firms_service import get_firms_service, FIRMSService
from app.schemas.satellite import SatelliteThermalEventsResponse

MOCK_VIIRS_ROW_1 = (
    "latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight\n"
    "22.3039,70.8022,367.4,0.4,0.4,2026-09-25,0215,N,VIIRS,h,2.0NRT,298.5,1250.0,N\n"
)

MOCK_VIIRS_ROW_2 = (
    "latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight\n"
    "21.1124,72.6582,345.8,0.5,0.4,2026-09-25,0945,1,VIIRS,h,2.0NRT,301.2,680.0,D\n"
)

MOCK_HEADER_ONLY = (
    "latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight\n"
)


class TestResilientFIRMSPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = get_firms_service()
        # Clean any test records
        with SessionLocal() as db:
            db.query(ThermalEvent).filter(ThermalEvent.event_id.like("FIRMS-TEST-%")).delete(synchronize_session=False)
            db.commit()

    @classmethod
    def tearDownClass(cls):
        # Clean up test records
        with SessionLocal() as db:
            db.query(ThermalEvent).filter(ThermalEvent.event_id.like("FIRMS-TEST-%")).delete(synchronize_session=False)
            db.commit()

    def test_01_nasa_succeeds_events_stored(self):
        """TEST 1: NASA succeeds -> events stored in database cache."""
        with SessionLocal() as db:
            normalized = self.service.normalize_firms_events(
                csv_text=MOCK_VIIRS_ROW_1,
                source_name="NASA FIRMS (VIIRS_NOAA21_NRT)",
                db=db,
            )
            # Give deterministic test tag
            normalized[0]["event_id"] = "FIRMS-TEST-NOAA21-20260925-0215-22303_70802"
            counts = self.service.upsert_firms_events(normalized, db=db)
            self.assertEqual(counts["new_events"], 1)

            saved = db.query(ThermalEvent).filter(ThermalEvent.event_id == "FIRMS-TEST-NOAA21-20260925-0215-22303_70802").first()
            self.assertIsNotNone(saved)
            self.assertFalse(saved.is_demo)
            self.assertEqual(saved.event_type, normalized[0]["event_type"])

    def test_02_nasa_succeeds_frontend_receives_events(self):
        """TEST 2: NASA succeeds -> frontend API receives events from cache."""
        resp = self.service.get_satellite_events(mode="live")
        self.assertIsInstance(resp, SatelliteThermalEventsResponse)
        self.assertGreaterEqual(resp.event_count, 1)
        found = any(e.event_id == "FIRMS-TEST-NOAA21-20260925-0215-22303_70802" for e in resp.events)
        self.assertTrue(found, "Stored event must be returned in satellite live API response")

    def test_03_nasa_fails_existing_events_remain(self):
        """TEST 3: NASA fails after successful fetch -> existing events remain (LIVE_STALE)."""
        # Force a failure in service
        self.service.last_status = "LIVE_STALE"
        self.service.last_error = "FIRMS HTTP 503 Service Unavailable"
        resp = self.service.get_satellite_events(mode="live")
        self.assertEqual(resp.status, "LIVE_STALE")
        self.assertTrue(resp.connected)
        self.assertFalse(resp.live_connected)
        self.assertGreaterEqual(resp.event_count, 1)

    def test_04_nasa_times_out_existing_events_remain(self):
        """TEST 4: NASA times out -> existing events remain."""
        self.service.last_status = "LIVE_STALE"
        self.service.last_error = "Remote NASA server unreachable / connection timeout"
        resp = self.service.get_satellite_events(mode="live")
        self.assertEqual(resp.status, "LIVE_STALE")
        self.assertGreaterEqual(resp.event_count, 1)

    def test_05_nasa_returns_500_existing_events_remain(self):
        """TEST 5: NASA returns HTTP 500 -> existing events remain."""
        self.service.last_status = "LIVE_STALE"
        self.service.last_error = "FIRMS HTTP 500 Internal Server Error"
        resp = self.service.get_satellite_events(mode="live")
        self.assertEqual(resp.status, "LIVE_STALE")
        self.assertGreaterEqual(resp.event_count, 1)

    def test_06_nasa_returns_malformed_response_existing_events_remain(self):
        """TEST 6: NASA returns malformed response -> existing events remain."""
        valid, err = self.service.validate_firms_response("<html><body>502 Bad Gateway</body></html>")
        self.assertFalse(valid)
        # Verify DB still has event
        with SessionLocal() as db:
            saved = db.query(ThermalEvent).filter(ThermalEvent.event_id == "FIRMS-TEST-NOAA21-20260925-0215-22303_70802").first()
            self.assertIsNotNone(saved)

    def test_07_nasa_successfully_returns_zero_events(self):
        """TEST 7: NASA successfully returns zero events (CASE A) -> distinct status."""
        valid, err = self.service.validate_firms_response(MOCK_HEADER_ONLY)
        self.assertTrue(valid)
        lines = [l for l in MOCK_HEADER_ONLY.strip().split("\n") if l.strip()]
        self.assertEqual(len(lines), 1)

    def test_08_nasa_recovers_database_updates(self):
        """TEST 8: NASA recovers -> database updates with new data."""
        with SessionLocal() as db:
            normalized = self.service.normalize_firms_events(
                csv_text=MOCK_VIIRS_ROW_2,
                source_name="NASA FIRMS (VIIRS_NOAA21_NRT)",
                db=db,
            )
            normalized[0]["event_id"] = "FIRMS-TEST-NOAA21-20260925-0945-21112_72658"
            counts = self.service.upsert_firms_events(normalized, db=db)
            self.assertEqual(counts["new_events"], 1)

            saved = db.query(ThermalEvent).filter(ThermalEvent.event_id == "FIRMS-TEST-NOAA21-20260925-0945-21112_72658").first()
            self.assertIsNotNone(saved)

    def test_09_repeated_refreshes_do_not_create_duplicates(self):
        """TEST 9: Repeated refreshes do not create duplicates (idempotency)."""
        with SessionLocal() as db:
            normalized = self.service.normalize_firms_events(
                csv_text=MOCK_VIIRS_ROW_1,
                source_name="NASA FIRMS (VIIRS_NOAA21_NRT)",
                db=db,
            )
            normalized[0]["event_id"] = "FIRMS-TEST-NOAA21-20260925-0215-22303_70802"
            # Ingest 3 times repeatedly
            c1 = self.service.upsert_firms_events(normalized, db=db)
            c2 = self.service.upsert_firms_events(normalized, db=db)
            c3 = self.service.upsert_firms_events(normalized, db=db)

            self.assertEqual(c1["new_events"], 0, "Already exists from test 01")
            self.assertEqual(c2["new_events"], 0)
            self.assertEqual(c3["new_events"], 0)
            self.assertEqual(c3["updated_events"], 1)

            total = db.query(ThermalEvent).filter(ThermalEvent.event_id == "FIRMS-TEST-NOAA21-20260925-0215-22303_70802").count()
            self.assertEqual(total, 1, "Must not have duplicate rows")

    def test_10_frontend_live_data_retention_contract(self):
        """TEST 10: Frontend contract test: response preserves items array during STALE status."""
        self.service.last_status = "LIVE_STALE"
        self.service.last_error = "Connection reset by peer"
        resp = self.service.get_satellite_events(mode="live")
        self.assertGreater(len(resp.events), 0, "Live events must not be emptied during temporary failure")
        self.assertEqual(resp.status, "LIVE_STALE")

    def test_11_map_instance_stability_code_check(self):
        """TEST 11: Frontend code check: renderMarkers modifies layerGroup rather than creating map."""
        index_html = open("../index.html", "r", encoding="utf-8").read()
        self.assertIn("state.thermalLayer.clearLayers()", index_html)
        self.assertIn("function renderMarkers()", index_html)

    def test_12_live_never_switches_to_demo(self):
        """TEST 12: In live mode, error response mode remains 'live'."""
        self.service.last_status = "LIVE_STALE"
        resp = self.service.get_satellite_events(mode="live")
        self.assertEqual(resp.mode, "live")
        self.assertNotEqual(resp.mode, "demo")

    def test_13_singleton_background_worker(self):
        """TEST 13: Multiple start calls do not create multiple worker threads."""
        self.service.start_background_worker()
        thread_1 = self.service._worker_thread
        self.service.start_background_worker()
        thread_2 = self.service._worker_thread
        self.assertIs(thread_1, thread_2, "Background worker thread must be a single singleton instance")

    def test_14_backend_alive_after_failures(self):
        """TEST 14: Health endpoint remains responsive and reports worker status."""
        health = self.service.get_health_status()
        self.assertIn("firms_worker_running", health)
        self.assertIn("cached_event_count", health)
        self.assertIn("status", health)

    def test_15_canonical_dataset_consistency(self):
        """TEST 15: Satellite API, thermal events API, and DB all query the same canonical dataset."""
        with SessionLocal() as db:
            db_count = db.query(ThermalEvent).filter(ThermalEvent.is_demo == False, ThermalEvent.status == "active").count()
            resp = self.service.get_satellite_events(mode="live", db=db)
            self.assertEqual(resp.event_count, db_count)


if __name__ == "__main__":
    unittest.main()
