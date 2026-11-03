import smtplib
import unittest
from unittest.mock import patch

from email_alert import (
    send_email,
    send_down_alert,
    send_recovery_alert
)


class TestEmailAlert(unittest.TestCase):

    @patch("email_alert.smtplib.SMTP")
    @patch("pathlib.Path.read_text", return_value=(
        "GMAIL_ADDRESS=test@example.com\n"
        "GMAIL_APP_PASSWORD=test-password\n"
    ))
    def test_send_email_successfully(self, mock_config, mock_smtp):

        send_email("Test Subject", "Test Message")

        mock_smtp.assert_called_once_with(
            "smtp.gmail.com", 587, timeout=20
        )

        mock_server = mock_smtp.return_value.__enter__.return_value

        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with(
            "test@example.com", "test-password"
        )
        mock_server.send_message.assert_called_once()

    @patch("email_alert.smtplib.SMTP")
    @patch("pathlib.Path.read_text", return_value=(
        "GMAIL_ADDRESS=test@example.com\n"
        "GMAIL_APP_PASSWORD=test-password\n"
    ))
    def test_authentication_failure(self, mock_config, mock_smtp):

        mock_server = mock_smtp.return_value.__enter__.return_value

        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(
            535, b"Authentication failed"
        )

        with self.assertRaises(smtplib.SMTPAuthenticationError):
            send_email("Test Subject", "Test Message")

        mock_server.send_message.assert_not_called()

    @patch("email_alert.send_email")
    def test_down_alert_message(self, mock_send):

        send_down_alert(
            "https://demo.example",
            "2026-11-03 10:00:00"
        )

        subject, body = mock_send.call_args.args

        self.assertEqual(
            subject,
            "WorkflowWatch ALERT: https://demo.example is DOWN"
        )
        self.assertIn("Status: DOWN", body)
        self.assertIn("2026-11-03 10:00:00", body)

    @patch("email_alert.send_email")
    def test_recovery_alert_message(self, mock_send):

        send_recovery_alert(
            "https://demo.example",
            "2026-11-03 10:30:00"
        )

        subject, body = mock_send.call_args.args

        self.assertEqual(
            subject,
            "WorkflowWatch RECOVERY: https://demo.example is UP"
        )
        self.assertIn("Status: UP", body)
        self.assertIn("2026-11-03 10:30:00", body)


if __name__ == "__main__":
    unittest.main()
