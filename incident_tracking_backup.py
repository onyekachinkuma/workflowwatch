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


tests = [
    ("UP", "DOWN", True),
    ("DOWN", "DOWN", True),
    ("DOWN", "UP", True),
    ("UP", "UP", True),
    ("UP", "DOWN", False),
    ("DOWN", "UP", False),
    ("UNKNOWN", "DOWN", True),
]

for previous, current, email_succeeds in tests:
    action, new_state = process_transition(
        previous, current, email_succeeds
    )

    print(
        f"{previous} -> {current} | "
        f"Email succeeds: {email_succeeds} | "
        f"Action: {action} | "
        f"Saved state: {new_state}"
    )
