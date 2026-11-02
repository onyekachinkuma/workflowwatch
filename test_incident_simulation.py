def simulate_check(states, url, current_status, email_sender):
    previous_status = states.get(url, "UNKNOWN")

    try:
        if current_status == "DOWN" and previous_status != "DOWN":
            email_sender("DOWN", url)

        elif current_status == "UP" and previous_status == "DOWN":
            email_sender("RECOVERY", url)

    except Exception as error:
        print(f"Notification failed: {error}")
        print("Previous state retained for retry.")
        return

    if current_status in ("UP", "DOWN"):
        states[url] = current_status

    print(f"Previous: {previous_status} | Current: {current_status}")
    print(f"Saved state: {states[url]}")
    print("-" * 45)


def fake_email_sender(alert_type, url):
    print(f"SIMULATED EMAIL: {alert_type} alert for {url}")


states = {"https://demo.example": "UP"}
url = "https://demo.example"

print("TEST 1: Website goes DOWN")
simulate_check(states, url, "DOWN", fake_email_sender)

print("TEST 2: Website remains DOWN")
simulate_check(states, url, "DOWN", fake_email_sender)

print("TEST 3: Website recovers")
simulate_check(states, url, "UP", fake_email_sender)

print("\nFINAL SIMULATED STATE:")
print(states)
