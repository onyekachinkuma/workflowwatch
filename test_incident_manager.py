import unittest
import tempfile
from pathlib import Path

from incident_manager import (
    record_status,
    mark_notification_sent,
    save_incidents,
    load_incidents
)


class TestIncidentManager(unittest.TestCase):

    def setUp(self):
        self.incidents = []
        self.url = "https://example.com"

    def test_new_incident(self):
        result = record_status(
            self.incidents, self.url, "DOWN"
        )
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
        result = mark_notification_sent(
            self.incidents, "unknown-id", "down"
        )

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
