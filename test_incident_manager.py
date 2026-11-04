import unittest
import tempfile
from pathlib import Path

from incident_manager import (
    record_status,
    mark_notification_sent,
    save_incidents,
    load_incidents,
    get_pending_notifications,
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


if __name__ == "__main__":
    unittest.main()
