import json
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock

from notification_worker import process_pending_notifications


class TestNotificationWorker(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.incident_file = Path(self.temp_dir.name) / "incidents.json"

        self.incidents = [
            {
                "incident_id": "test-incident-001",
                "url": "https://demo.example",
                "status": "OPEN",
                "started_at": "2026-11-05T20:00:00+00:00",
                "recovered_at": None,
                "down_notification_sent": False,
                "recovery_notification_sent": False,
                "down_notification_attempts": 0,
                "down_notification_last_attempt_at": None,
                "down_notification_last_error": None,
                "recovery_notification_attempts": 0,
                "recovery_notification_last_attempt_at": None,
                "recovery_notification_last_error": None
            }
        ]

        self.save_fixture()

    def tearDown(self):
        self.temp_dir.cleanup()

    def save_fixture(self):
        self.incident_file.write_text(
            json.dumps(self.incidents),
            encoding="utf-8"
        )

    def load_fixture(self):
        return json.loads(
            self.incident_file.read_text(encoding="utf-8")
        )

    def test_successful_down_notification(self):
        mock_delivery = Mock()

        results = process_pending_notifications(
            mock_delivery,
            incident_file=self.incident_file
        )

        mock_delivery.assert_called_once_with(
            "down",
            "https://demo.example",
            "2026-11-05T20:00:00+00:00"
        )

        updated = self.load_fixture()[0]

        self.assertTrue(updated["down_notification_sent"])
        self.assertEqual(updated["down_notification_attempts"], 1)
        self.assertIsNone(updated["down_notification_last_error"])
        self.assertTrue(results[0]["success"])

    def test_failed_down_notification(self):
        mock_delivery = Mock(
            side_effect=ConnectionError("Mock email delivery failed")
        )

        results = process_pending_notifications(
            mock_delivery,
            incident_file=self.incident_file
        )

        updated = self.load_fixture()[0]

        self.assertFalse(updated["down_notification_sent"])
        self.assertEqual(updated["down_notification_attempts"], 1)
        self.assertEqual(
            updated["down_notification_last_error"],
            "Mock email delivery failed"
        )
        self.assertFalse(results[0]["success"])

    def test_successful_recovery_notification(self):
        self.incidents[0]["status"] = "CLOSED"
        self.incidents[0]["down_notification_sent"] = True
        self.incidents[0]["recovered_at"] = (
            "2026-11-05T20:10:00+00:00"
        )
        self.save_fixture()

        mock_delivery = Mock()

        results = process_pending_notifications(
            mock_delivery,
            incident_file=self.incident_file
        )

        mock_delivery.assert_called_once_with(
            "recovery",
            "https://demo.example",
            "2026-11-05T20:10:00+00:00"
        )

        updated = self.load_fixture()[0]

        self.assertTrue(updated["recovery_notification_sent"])
        self.assertEqual(updated["recovery_notification_attempts"], 1)
        self.assertTrue(results[0]["success"])

    def test_no_delivery_after_three_attempts(self):
        self.incidents[0]["down_notification_attempts"] = 3
        self.incidents[0]["down_notification_last_attempt_at"] = (
            "2026-11-05T20:00:00+00:00"
        )
        self.incidents[0]["down_notification_last_error"] = (
            "Previous delivery failed"
        )
        self.save_fixture()

        mock_delivery = Mock()

        results = process_pending_notifications(
            mock_delivery,
            incident_file=self.incident_file
        )

        mock_delivery.assert_not_called()
        self.assertEqual(results, [])



    def test_first_retry_waits_60_seconds(self):
        base_time = datetime(
            2026, 11, 5, 20, 0, 0,
            tzinfo=timezone.utc
        )

        self.incidents[0]["down_notification_attempts"] = 1
        self.incidents[0]["down_notification_last_attempt_at"] = (
            base_time.isoformat(timespec="seconds")
        )
        self.save_fixture()

        mock_delivery = Mock()

        process_pending_notifications(
            mock_delivery,
            incident_file=self.incident_file,
            now=base_time + timedelta(seconds=59)
        )
        mock_delivery.assert_not_called()

        process_pending_notifications(
            mock_delivery,
            incident_file=self.incident_file,
            now=base_time + timedelta(seconds=60)
        )
        mock_delivery.assert_called_once()

        updated = self.load_fixture()[0]
        self.assertEqual(updated["down_notification_attempts"], 2)
        self.assertEqual(
            updated["down_notification_last_attempt_at"],
            "2026-11-05T20:01:00+00:00"
        )

    def test_second_retry_waits_120_seconds(self):
        base_time = datetime(
            2026, 11, 5, 20, 0, 0,
            tzinfo=timezone.utc
        )

        self.incidents[0]["down_notification_attempts"] = 2
        self.incidents[0]["down_notification_last_attempt_at"] = (
            (base_time + timedelta(seconds=60)).isoformat(
                timespec="seconds"
            )
        )
        self.save_fixture()

        mock_delivery = Mock()

        process_pending_notifications(
            mock_delivery,
            incident_file=self.incident_file,
            now=base_time + timedelta(seconds=179)
        )
        mock_delivery.assert_not_called()

        process_pending_notifications(
            mock_delivery,
            incident_file=self.incident_file,
            now=base_time + timedelta(seconds=180)
        )
        mock_delivery.assert_called_once()

        updated = self.load_fixture()[0]
        self.assertEqual(updated["down_notification_attempts"], 3)
        self.assertEqual(
            updated["down_notification_last_attempt_at"],
            "2026-11-05T20:03:00+00:00"
        )



    def test_concurrent_workers_send_notification_only_once(self):
        delivery_started = threading.Event()
        allow_delivery_to_finish = threading.Event()
        delivery_calls = []
        worker_results = []
        worker_errors = []

        def mock_delivery(notification_type, url, checked_at):
            delivery_calls.append(notification_type)
            delivery_started.set()

            if not allow_delivery_to_finish.wait(timeout=5):
                raise TimeoutError("Test delivery timed out")

        def run_worker():
            try:
                result = process_pending_notifications(
                    mock_delivery,
                    incident_file=self.incident_file
                )
                worker_results.append(result)
            except Exception as error:
                worker_errors.append(error)

        first_worker = threading.Thread(target=run_worker)
        second_worker = threading.Thread(target=run_worker)

        first_worker.start()
        self.assertTrue(delivery_started.wait(timeout=5))

        second_worker.start()
        allow_delivery_to_finish.set()

        first_worker.join(timeout=5)
        second_worker.join(timeout=5)

        self.assertFalse(first_worker.is_alive())
        self.assertFalse(second_worker.is_alive())
        self.assertEqual(worker_errors, [])
        self.assertEqual(delivery_calls, ["down"])
        self.assertEqual(len(worker_results), 2)
        self.assertEqual(sum(len(result) for result in worker_results), 1)

        updated = self.load_fixture()[0]
        self.assertTrue(updated["down_notification_sent"])
        self.assertEqual(updated["down_notification_attempts"], 1)


if __name__ == "__main__":
    unittest.main()
