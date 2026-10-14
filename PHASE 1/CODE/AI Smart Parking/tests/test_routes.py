import unittest
import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from backend.billing_manager import calculate_dynamic_bill
from backend.booking_manager import book_slot
from backend.database import create_tables, get_connection
from backend.entry_manager import normalize_detected_plate, vehicle_entry, vehicle_exit
from backend.anomaly_manager import get_all_anomalies
from backend.main import app
from backend.monitoring_manager import get_open_alerts, record_alert, record_vision_observation
from backend.slot_manager import create_parking_slots


class DynamicBillingTests(unittest.TestCase):
    def test_vehicle_type_changes_base_rate(self):
        bike_bill = calculate_dynamic_bill("Bike", 60)
        car_bill = calculate_dynamic_bill("Car", 60)

        self.assertEqual(bike_bill["amount"], 10)
        self.assertEqual(car_bill["amount"], 20)

    def test_extended_parking_uses_hourly_rate_only(self):
        bill = calculate_dynamic_bill("Car", 13 * 60)

        self.assertEqual(bill["billable_hours"], 13)
        self.assertEqual(bill["amount"], 370)


class ParkingRouteTests(unittest.TestCase):
    def test_detected_plate_normalizer_accepts_one_letter_series(self):
        self.assertEqual(normalize_detected_plate("MP33 C 3370"), "MP33C3370")
        self.assertEqual(normalize_detected_plate("TNOGBY9726"), "TN09BY9726")
        self.assertEqual(normalize_detected_plate("FEES6"), "")

    def test_camera_entry_registers_plate_and_exit_rejects_unknown_plate(self):
        with TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "parking.db"
            with (
                patch("backend.database.DB_PATH", database_path),
                patch("backend.slot_manager.DB_PATH", database_path),
            ):
                create_tables()
                create_parking_slots()
                entry = vehicle_entry("AUTO123", "Car")
                unknown_exit = vehicle_exit("UNKNOWN123")
                connection = get_connection()
                vehicle = connection.execute(
                    "SELECT number_plate FROM vehicles WHERE number_plate = ?",
                    ("AUTO123",),
                ).fetchone()
                slot = connection.execute(
                    "SELECT status FROM parking_slots WHERE slot_id = ?",
                    (entry["slot_id"],),
                ).fetchone()
                connection.close()

        self.assertTrue(entry["success"])
        self.assertEqual(vehicle["number_plate"], "AUTO123")
        self.assertEqual(slot["status"], "Occupied")
        self.assertFalse(unknown_exit["success"])
        self.assertEqual(unknown_exit["message"], "Vehicle not registered")

    def test_open_alerts_hide_legacy_overstay_records(self):
        with TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "parking.db"
            with patch("backend.database.DB_PATH", database_path):
                create_tables()
                record_alert("Overstay", "Legacy overstay alert", "High")
                record_alert("Improper Parking", "Vehicle outside its bay", "Medium")

                alerts = get_open_alerts()["alerts"]

        self.assertEqual([alert["alert_type"] for alert in alerts], ["Improper Parking"])

    def test_billing_rates_are_exposed_for_portals(self):
        client = TestClient(app)
        response = client.get("/api/billing/rates")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["currency"], "INR")
        self.assertEqual(payload["hourly_rates"]["Car"], 20)

    def test_slot_api_does_not_expose_legacy_safety_fields(self):
        response = TestClient(app).get("/api/slots")

        self.assertEqual(response.status_code, 200)
        slot = response.json()["slots"][0]
        self.assertEqual(set(slot), {"slot_id", "floor", "section", "status"})

    def test_booking_anpr_billing_and_payment_slot_release(self):
        with TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "parking.db"
            with (
                patch("backend.database.DB_PATH", database_path),
                patch("backend.slot_manager.DB_PATH", database_path),
            ):
                create_tables()
                create_parking_slots()
                booking = book_slot(
                    "Test Driver",
                    "TEST123",
                    "Car",
                    "A2",
                    start_time="2026-09-28 10:00:00",
                    end_time="2026-09-28 12:00:00",
                )
                self.assertTrue(booking["success"])

                entry = vehicle_entry("TEST123", "Car")
                self.assertTrue(entry["success"])
                self.assertEqual(entry["entry_type"], "Booking")
                self.assertEqual(entry["slot_id"], "A2")

                observation = record_vision_observation({
                    "number_plate": "TEST123",
                    "slot_id": "A1",
                    "vehicle_count": 2,
                })
                alert_types = {alert["type"] for alert in observation["alerts"]}
                self.assertIn("Slot Mismatch", alert_types)
                self.assertIn("Double Parking", alert_types)
                self.assertGreaterEqual(get_open_alerts()["total"], 2)

                exit_result = vehicle_exit("TEST123")
                self.assertTrue(exit_result["success"])
                self.assertEqual(exit_result["status"], "Awaiting Payment")
                connection = get_connection()
                slot_status = connection.execute(
                    "SELECT status FROM parking_slots WHERE slot_id = 'A2'"
                ).fetchone()["status"]
                connection.close()
                self.assertEqual(slot_status, "Occupied")

                payment_response = TestClient(app).post(
                    f"/api/payments/{exit_result['session_id']}/pay"
                )
                self.assertEqual(payment_response.status_code, 200)
                connection = get_connection()
                slot_status = connection.execute(
                    "SELECT status FROM parking_slots WHERE slot_id = 'A2'"
                ).fetchone()["status"]
                connection.close()
                self.assertEqual(slot_status, "Available")

                walk_in = vehicle_entry("WALK123", "Bike")
                self.assertTrue(walk_in["success"])
                self.assertEqual(walk_in["entry_type"], "Walk-in")

    def test_anomalies_are_capped_to_slot_capacity(self):
        with patch("backend.anomaly_manager.get_all_slots", return_value=[{"slot_id": f"A{i}"} for i in range(1, 41)]):
            with patch("backend.anomaly_manager.detect_no_show_bookings", return_value=[
                {"type": "No-Show Booking", "severity": "Low", "booking_id": booking_id}
                for booking_id in range(50)
            ]):
                with patch("backend.anomaly_manager.detect_duplicate_sessions", return_value=[]):
                    payload = get_all_anomalies()
                    self.assertEqual(payload["total"], 40)
                    self.assertEqual(len(payload["anomalies"]), 40)

    def test_camera_detection_updates_latest_vehicle(self):
        client = TestClient(app)
        entry_result = {
            "success": True,
            "number_plate": "TN14AB2345",
            "vehicle_type": "Car",
            "slot_id": "A1",
        }
        with patch("backend.main.active_camera_scan_id", "current-scan"):
            stale = client.post(
                "/api/camera/detection",
                json={"number_plate": "OLD123", "scan_id": "old-scan"},
            )
            with patch("backend.main.vehicle_entry", return_value=entry_result) as enter_vehicle:
                response = client.post(
                    "/api/camera/detection",
                    json={"number_plate": "TN14AB2345", "vehicle_type": "Car", "scan_id": "current-scan"},
                )
                duplicate = client.post(
                    "/api/camera/detection",
                    json={"number_plate": "TN14AB2345", "vehicle_type": "Car", "scan_id": "current-scan"},
                )
        self.assertEqual(stale.status_code, 409)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["action_result"], entry_result)
        self.assertEqual(duplicate.json()["action_result"], entry_result)
        enter_vehicle.assert_called_once_with("TN14AB2345", "Car")

        fetched = client.get("/api/camera/latest")
        self.assertEqual(fetched.status_code, 200)
        self.assertEqual(fetched.headers["cache-control"], "no-store")
        self.assertEqual(fetched.json()["number_plate"], "TN14AB2345")
        self.assertEqual(fetched.json()["vehicle_type"], "Car")

    def test_camera_exit_detection_uses_registered_vehicle_service(self):
        client = TestClient(app)
        exit_result = {"success": False, "message": "Vehicle not registered"}
        with (
            patch("backend.main.active_camera_scan_id", "exit-scan"),
            patch("backend.main.vehicle_exit", return_value=exit_result) as exit_vehicle,
        ):
            response = client.post(
                "/api/camera/detection",
                json={
                    "number_plate": "TN09BY9726",
                    "mode": "EXIT",
                    "scan_id": "exit-scan",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["action_result"], exit_result)
        exit_vehicle.assert_called_once_with("TN09BY9726")

    def test_camera_start_endpoint_starts_capture_process(self):
        client = TestClient(app)
        previous_process = MagicMock()
        previous_process.poll.return_value = None
        previous_process.pid = 4321
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.pid = 1234
        detection_state = {
            "number_plate": "OLD123",
            "vehicle_type": "Car",
            "source": "camera",
            "detected_at": "old-time",
            "scan_id": "old-scan",
        }

        with (
            patch("backend.main.camera_process", previous_process),
            patch("backend.main.last_camera_detection", detection_state),
            patch("backend.main.subprocess.Popen", return_value=mock_process) as launch_process,
        ):
            response = client.post(
                "/api/camera/start",
                json={"mode": "entry"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertEqual(response.json()["mode"], "ENTRY")
        self.assertTrue(response.json()["scan_id"])
        self.assertEqual(response.json()["scan_id"], launch_process.call_args.kwargs["env"]["PARKING_SCAN_ID"])
        self.assertEqual(launch_process.call_args.kwargs["env"]["PARKING_SHOW_CAMERA"], "1")
        self.assertEqual(launch_process.call_args.args[0][0], sys.executable)
        self.assertEqual(
            launch_process.call_args.kwargs["creationflags"],
            getattr(subprocess, "CREATE_NEW_CONSOLE", 0),
        )
        self.assertEqual(detection_state["number_plate"], "")
        previous_process.terminate.assert_called_once()
        previous_process.wait.assert_called_once_with(timeout=5)
        launch_process.assert_called_once()


if __name__ == "__main__":
    unittest.main()
