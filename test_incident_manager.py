import unittest
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from incident_manager import (
    record_status,
    mark_notification_sent,
    save_incidents,
    load_incidents,
    get_pending_notifications,
    record_notification_attempt,
    notification_retry_is_due,
)


class TestIncidentManager(unittest.TestCase):

    def setUp(self):
        self.incidents = []
        self.url = "https://example.com"

    def test_new_incident(self):
        result = record_status(self.incidents, self.url, "DOWN")
        self.assertEqual(result, "INCIDENT OPENED")
        self.assertEqual(len(self.incidents), 1)

    def test_duplicate_down_prevention(self):
        record_status(self.incidents, self.url, "DOWN")
        result = record_status(self.incidents, self.url, "DOWN")
        self.assertEqual(result, "NO INCIDENT CHANGE")
        self.assertEqual(len(self.incidents), 1)

    def test_incident_recovery(self):
        record_status(self.incidents, self.url, "DOWN")
        result = record_status(self.incidents, self.url, "UP")
        self.assertEqual(result, "INCIDENT CLOSED")
        self.assertEqual(self.incidents[0]["status"], "CLOSED")

    def test_repeated_outages_create_history(self):
        record_status(self.incidents, self.url, "DOWN")
        record_status(self.incidents, self.url, "UP")
        record_status(self.incidents, self.url, "DOWN")
        self.assertEqual(len(self.incidents), 2)
        self.assertEqual(self.incidents[0]["status"], "CLOSED")
        self.assertEqual(self.incidents[1]["status"], "OPEN")

    def test_down_notification_tracking(self):
        record_status(self.incidents, self.url, "DOWN")
        incident_id = self.incidents[0]["incident_id"]
        result = mark_notification_sent(self.incidents, incident_id, "down")
        self.assertTrue(result)
        self.assertTrue(self.incidents[0]["down_notification_sent"])
        self.assertFalse(self.incidents[0]["recovery_notification_sent"])

    def test_recovery_notification_tracking(self):
        record_status(self.incidents, self.url, "DOWN")
        record_status(self.incidents, self.url, "UP")
        incident_id = self.incidents[0]["incident_id"]
        result = mark_notification_sent(self.incidents, incident_id, "recovery")
        self.assertTrue(result)
        self.assertTrue(self.incidents[0]["recovery_notification_sent"])
        self.assertFalse(self.incidents[0]["down_notification_sent"])

    def test_invalid_notification_type(self):
        record_status(self.incidents, self.url, "DOWN")
        incident_id = self.incidents[0]["incident_id"]
        with self.assertRaises(ValueError):
            mark_notification_sent(self.incidents, incident_id, "unknown")

    def test_save_and_load_incidents(self):
        record_status(self.incidents, self.url, "DOWN")
        with tempfile.TemporaryDirectory() as directory:
            test_file = Path(directory) / "incidents.json"
            save_incidents(self.incidents, test_file)
            loaded = load_incidents(test_file)
            self.assertEqual(loaded, self.incidents)

    def test_unknown_incident_notification(self):
        result = mark_notification_sent(self.incidents, "unknown-id", "down")
        self.assertFalse(result)

    def test_new_down_notification_is_pending(self):
        record_status(self.incidents, self.url, "DOWN")
        pending = get_pending_notifications(self.incidents)
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["notification_type"], "down")
        self.assertEqual(pending[0]["url"], self.url)

    def test_sent_down_notification_is_not_pending(self):
        record_status(self.incidents, self.url, "DOWN")
        incident_id = self.incidents[0]["incident_id"]
        mark_notification_sent(self.incidents, incident_id, "down")
        pending = get_pending_notifications(self.incidents)
        self.assertEqual(pending, [])

    def test_recovery_notification_is_pending(self):
        record_status(self.incidents, self.url, "DOWN")
        record_status(self.incidents, self.url, "UP")
        pending = get_pending_notifications(self.incidents)
        self.assertEqual(len(pending), 2)
        self.assertEqual(pending[0]["notification_type"], "down")
        self.assertEqual(pending[1]["notification_type"], "recovery")

    def test_pending_notifications_do_not_modify_incidents(self):
        record_status(self.incidents, self.url, "DOWN")
        original_incidents = [
            incident.copy() for incident in self.incidents
        ]
        first_result = get_pending_notifications(self.incidents)
        second_result = get_pending_notifications(self.incidents)
        self.assertEqual(first_result, second_result)
        self.assertEqual(self.incidents, original_incidents)


    def test_notification_attempt_records_failure(self):
        record_status(self.incidents, self.url, "DOWN")
        incident_id = self.incidents[0]["incident_id"]
        attempted_at = "2026-11-04T20:00:00+00:00"

        result = record_notification_attempt(
            self.incidents,
            incident_id,
            "down",
            error="SMTP connection failed",
            attempted_at=attempted_at
        )

        self.assertTrue(result)
        self.assertEqual(
            self.incidents[0]["down_notification_attempts"], 1
        )
        self.assertEqual(
            self.incidents[0]["down_notification_last_attempt_at"],
            attempted_at
        )
        self.assertEqual(
            self.incidents[0]["down_notification_last_error"],
            "SMTP connection failed"
        )

    def test_retry_not_due_before_60_seconds(self):
        record_status(self.incidents, self.url, "DOWN")
        incident = self.incidents[0]
        first_attempt = datetime(
            2026, 11, 4, 20, 0, tzinfo=timezone.utc
        )

        record_notification_attempt(
            self.incidents,
            incident["incident_id"],
            "down",
            error="Temporary failure",
            attempted_at=first_attempt.isoformat()
        )

        self.assertFalse(
            notification_retry_is_due(
                incident,
                "down",
                now=first_attempt + timedelta(seconds=59)
            )
        )

    def test_retry_due_after_60_seconds(self):
        record_status(self.incidents, self.url, "DOWN")
        incident = self.incidents[0]
        first_attempt = datetime(
            2026, 11, 4, 20, 0, tzinfo=timezone.utc
        )

        record_notification_attempt(
            self.incidents,
            incident["incident_id"],
            "down",
            error="Temporary failure",
            attempted_at=first_attempt.isoformat()
        )

        self.assertTrue(
            notification_retry_is_due(
                incident,
                "down",
                now=first_attempt + timedelta(seconds=60)
            )
        )

    def test_retry_stops_after_maximum_attempts(self):
        record_status(self.incidents, self.url, "DOWN")
        incident = self.incidents[0]

        for attempt in range(3):
            record_notification_attempt(
                self.incidents,
                incident["incident_id"],
                "down",
                error="Temporary failure",
                attempted_at=f"2026-11-04T20:0{attempt}:00+00:00"
            )

        self.assertEqual(incident["down_notification_attempts"], 3)
        self.assertFalse(
            notification_retry_is_due(
                incident,
                "down",
                now=datetime(2026, 11, 4, 21, 0, tzinfo=timezone.utc)
            )
        )

    def test_down_and_recovery_attempts_are_independent(self):
        record_status(self.incidents, self.url, "DOWN")
        record_status(self.incidents, self.url, "UP")
        incident = self.incidents[0]
        incident_id = incident["incident_id"]

        record_notification_attempt(
            self.incidents,
            incident_id,
            "down",
            error="DOWN alert failed"
        )

        record_notification_attempt(
            self.incidents,
            incident_id,
            "recovery",
            error="Recovery alert failed"
        )

        self.assertEqual(incident["down_notification_attempts"], 1)
        self.assertEqual(incident["recovery_notification_attempts"], 1)
        self.assertEqual(
            incident["down_notification_last_error"],
            "DOWN alert failed"
        )
        self.assertEqual(
            incident["recovery_notification_last_error"],
            "Recovery alert failed"
        )

    def test_pending_queue_respects_retry_delay(self):
        record_status(self.incidents, self.url, "DOWN")
        incident = self.incidents[0]
        first_attempt = datetime(
            2026, 11, 4, 20, 0, tzinfo=timezone.utc
        )

        record_notification_attempt(
            self.incidents,
            incident["incident_id"],
            "down",
            error="Temporary failure",
            attempted_at=first_attempt.isoformat()
        )

        early_check = get_pending_notifications(
            self.incidents,
            now=first_attempt + timedelta(seconds=59)
        )
        due_check = get_pending_notifications(
            self.incidents,
            now=first_attempt + timedelta(seconds=60)
        )

        self.assertEqual(early_check, [])
        self.assertEqual(len(due_check), 1)
        self.assertEqual(due_check[0]["notification_type"], "down")


if __name__ == "__main__":
    unittest.main()
