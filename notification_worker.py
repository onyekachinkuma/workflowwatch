from incident_manager import (
    load_incidents,
    save_incidents,
    get_pending_notifications,
    record_notification_attempt,
    mark_notification_sent
)


def process_pending_notifications(
    delivery_function,
    incident_file="incidents.json",
    now=None
):
    """Process eligible notifications using an injected delivery function."""

    incidents = load_incidents(incident_file)

    pending = get_pending_notifications(
        incidents,
        now=now
    )

    results = []

    for notification in pending:
        incident_id = notification["incident_id"]
        notification_type = notification["notification_type"]
        url = notification["url"]

        incident = next(
            item for item in incidents
            if item["incident_id"] == incident_id
        )

        checked_at = (
            incident["started_at"]
            if notification_type == "down"
            else incident["recovered_at"]
        )

        try:
            delivery_function(
                notification_type,
                url,
                checked_at
            )

        except Exception as error:
            record_notification_attempt(
                incidents,
                incident_id,
                notification_type,
                error=error,
                attempted_at=(
                    now.isoformat(timespec="seconds")
                    if now is not None else None
                )
            )

            results.append({
                "incident_id": incident_id,
                "notification_type": notification_type,
                "success": False,
                "error": str(error)
            })

        else:
            record_notification_attempt(
                incidents,
                incident_id,
                notification_type,
                attempted_at=(
                    now.isoformat(timespec="seconds")
                    if now is not None else None
                )
            )

            mark_notification_sent(
                incidents,
                incident_id,
                notification_type
            )

            results.append({
                "incident_id": incident_id,
                "notification_type": notification_type,
                "success": True,
                "error": None
            })

    if results:
        save_incidents(incidents, incident_file)

    return results
