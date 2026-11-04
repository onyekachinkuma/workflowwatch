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
            "recovery_notification_sent": False
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


def get_pending_notifications(incidents):
    """Return notifications that have not yet been delivered."""

    pending = []

    for incident in incidents:
        if (
            not incident["down_notification_sent"]
        ):
            pending.append({
                "incident_id": incident["incident_id"],
                "url": incident["url"],
                "notification_type": "down"
            })

        if (
            incident["status"] == "CLOSED"
            and not incident["recovery_notification_sent"]
        ):
            pending.append({
                "incident_id": incident["incident_id"],
                "url": incident["url"],
                "notification_type": "recovery"
            })

    return pending
