import unittest


def process_transition(previous_status, current_status, email_succeeds=True):
    notification_required = (
        (current_status == "DOWN" and previous_status != "DOWN")
        or (current_status == "UP" and previous_status == "DOWN")
    )

    if notification_required and not email_succeeds:
        return "EMAIL FAILED - RETRY NEXT RUN", previous_status

    if current_status == "DOWN" and previous_status != "DOWN":
        return "SEND DOWN ALERT", current_status

    elif current_status == "UP" and previous_status == "DOWN":
        return "SEND RECOVERY ALERT", current_status

    if current_status in ("UP", "DOWN"):
        return "NO EMAIL", current_status

    return "NO EMAIL - STATE UNCHANGED", previous_status


class TestIncidentTracking(unittest.TestCase):

    def test_website_goes_down(self):
        self.assertEqual(
            process_transition("UP", "DOWN"),
            ("SEND DOWN ALERT", "DOWN")
        )

    def test_website_remains_down(self):
        self.assertEqual(
            process_transition("DOWN", "DOWN"),
            ("NO EMAIL", "DOWN")
        )

    def test_website_recovers(self):
        self.assertEqual(
            process_transition("DOWN", "UP"),
            ("SEND RECOVERY ALERT", "UP")
        )

    def test_website_remains_up(self):
        self.assertEqual(
            process_transition("UP", "UP"),
            ("NO EMAIL", "UP")
        )

    def test_down_alert_email_failure(self):
        self.assertEqual(
            process_transition("UP", "DOWN", False),
            ("EMAIL FAILED - RETRY NEXT RUN", "UP")
        )

    def test_recovery_email_failure(self):
        self.assertEqual(
            process_transition("DOWN", "UP", False),
            ("EMAIL FAILED - RETRY NEXT RUN", "DOWN")
        )

    def test_unknown_previous_state(self):
        self.assertEqual(
            process_transition("UNKNOWN", "DOWN"),
            ("SEND DOWN ALERT", "DOWN")
        )


if __name__ == "__main__":
    unittest.main()
