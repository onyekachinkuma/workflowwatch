import json
import os
import tempfile
import uuid
from pathlib import Path
from datetime import datetime, timezone


INCIDENT_FILE = Path("incidents.json")


def current_timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_incidents(incident_file=INCIDENT_FILE):
    """Load incident history."""
    incident_file = Path(incident_file)

    if not incident_file.exists():
        return []

    try:
        incidents = json.loads(
            incident_file.read_text(encoding="utf-8")
        )

        if not isinstance(incidents, list):
            raise ValueError("Incident file must contain a JSON list")

        return incidents

    except (json.JSONDecodeError, ValueError) as error:
        raise ValueError(f"Cannot read incident history: {error}")


def save_incidents(incidents, incident_file=INCIDENT_FILE):
    """Save incident history using atomic file replacement."""
    incident_file = Path(incident_file)
    temp_file = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=incident_file.parent,
            prefix="incidents_",
            suffix=".tmp",
            delete=False
        ) as file:
            temp_file = Path(file.name)
            json.dump(incidents, file, indent=4)
            file.flush()
            os.fsync(file.fileno())

        os.replace(temp_file, incident_file)

    finally:
        if temp_file is not None and temp_file.exists():
            temp_file.unlink()


def record_status(incidents, url, status, checked_at=None):
    """Record a new outage or close an existing incident."""

    if status not in ("UP", "DOWN"):
        return "NO INCIDENT CHANGE"

    checked_at = checked_at or current_timestamp()

    open_incident = next(
        (
            incident for incident in reversed(incidents)
            if incident["url"] == url and incident["status"] == "OPEN"
        ),
        None
    )

    if status == "DOWN" and open_incident is None:
        incidents.append({
            "incident_id": str(uuid.uuid4()),
            "url": url,
            "status": "OPEN",
            "started_at": checked_at,
            "recovered_at": None,
            "down_notification_sent": False,
            "recovery_notification_sent": False,
            "down_notification_attempts": 0,
            "down_notification_last_attempt_at": None,
            "down_notification_last_error": None,
            "recovery_notification_attempts": 0,
            "recovery_notification_last_attempt_at": None,
            "recovery_notification_last_error": None
        })

        return "INCIDENT OPENED"

    if status == "UP" and open_incident is not None:
        open_incident["status"] = "CLOSED"
        open_incident["recovered_at"] = checked_at

        return "INCIDENT CLOSED"

    return "NO INCIDENT CHANGE"


def mark_notification_sent(incidents, incident_id, notification_type):
    """Record successful DOWN or recovery notification delivery."""

    notification_fields = {
        "down": "down_notification_sent",
        "recovery": "recovery_notification_sent"
    }

    field = notification_fields.get(notification_type)

    if field is None:
        raise ValueError(
            "notification_type must be 'down' or 'recovery'"
        )

    for incident in incidents:
        if incident["incident_id"] == incident_id:
            incident[field] = True
            return True

    return False



def record_notification_attempt(
    incidents,
    incident_id,
    notification_type,
    error=None,
    attempted_at=None
):
    """Record one notification delivery attempt."""

    notification_fields = {
        "down": "down_notification",
        "recovery": "recovery_notification"
    }

    prefix = notification_fields.get(notification_type)

    if prefix is None:
        raise ValueError(
            "notification_type must be 'down' or 'recovery'"
        )

    for incident in incidents:
        if incident["incident_id"] == incident_id:
            attempts_field = f"{prefix}_attempts"
            timestamp_field = f"{prefix}_last_attempt_at"
            error_field = f"{prefix}_last_error"

            incident[attempts_field] = (
                incident.get(attempts_field, 0) + 1
            )
            incident[timestamp_field] = (
                attempted_at or current_timestamp()
            )
            incident[error_field] = (
                str(error) if error is not None else None
            )

            return True

    return False



def notification_retry_is_due(
    incident,
    notification_type,
    now=None,
    max_attempts=3,
    retry_delays=(60, 120)
):
    """Check whether a notification is eligible for another attempt."""

    notification_fields = {
        "down": "down_notification",
        "recovery": "recovery_notification"
    }

    prefix = notification_fields.get(notification_type)

    if prefix is None:
        raise ValueError(
            "notification_type must be 'down' or 'recovery'"
        )

    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    if len(retry_delays) < max_attempts - 1:
        raise ValueError("Not enough retry delays supplied")

    attempts = incident.get(f"{prefix}_attempts", 0)

    if attempts < 0:
        raise ValueError("Notification attempts cannot be negative")

    if attempts == 0:
        return True

    if attempts >= max_attempts:
        return False

    last_attempt = incident.get(f"{prefix}_last_attempt_at")

    if not last_attempt:
        return True

    last_attempt_time = datetime.fromisoformat(last_attempt)

    if last_attempt_time.tzinfo is None:
        last_attempt_time = last_attempt_time.replace(
            tzinfo=timezone.utc
        )

    now = now or datetime.now(timezone.utc)

    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    delay = retry_delays[attempts - 1]

    elapsed = (now - last_attempt_time).total_seconds()

    return elapsed >= delay


def get_pending_notifications(
    incidents,
    now=None,
    max_attempts=3,
    retry_delays=(60, 120)
):
    """Return unsent notifications that are eligible for delivery."""

    pending = []

    for incident in incidents:
        if (
            not incident["down_notification_sent"]
            and notification_retry_is_due(
                incident,
                "down",
                now=now,
                max_attempts=max_attempts,
                retry_delays=retry_delays
            )
        ):
            pending.append({
                "incident_id": incident["incident_id"],
                "url": incident["url"],
                "notification_type": "down"
            })

        if (
            incident["status"] == "CLOSED"
            and not incident["recovery_notification_sent"]
            and notification_retry_is_due(
                incident,
                "recovery",
                now=now,
                max_attempts=max_attempts,
                retry_delays=retry_delays
            )
        ):
            pending.append({
                "incident_id": incident["incident_id"],
                "url": incident["url"],
                "notification_type": "recovery"
            })

    return pending
