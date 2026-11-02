import urllib.request
import urllib.error
import socket
import time
import json
from pathlib import Path
from datetime import datetime
from email_alert import send_down_alert, send_recovery_alert

STATE_FILE = Path("website_states.json")

# Load previous website states
if STATE_FILE.exists():
    try:
        previous_states = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if not isinstance(previous_states, dict):
            raise ValueError("State file must contain a JSON object")
    except (json.JSONDecodeError, ValueError) as error:
        raise SystemExit(f"Cannot read website states: {error}")
else:
    previous_states = {}

with open("monitored_websites.txt", "r", encoding="utf-8") as website_file:
    urls = [
        line.strip()
        for line in website_file
        if line.strip() and not line.strip().startswith("#")
    ]

if not urls:
    print("No website URLs found in monitored_websites.txt.")
else:
    up_count = 0
    down_count = 0
    http_error_count = 0
    check_failed_count = 0

    for url in urls:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        print(f"\nChecking {url} ...")
        checked_at = datetime.now().isoformat(timespec="seconds")

        start_time = time.perf_counter()

        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "WorkflowWatch/0.4"}
            )

            with urllib.request.urlopen(request, timeout=10) as response:
                http_code = response.status
                status = "UP" if 200 <= http_code < 400 else "HTTP_ERROR"

        except urllib.error.HTTPError as error:
            http_code = error.code
            status = "HTTP_ERROR"

        except (urllib.error.URLError, TimeoutError, socket.timeout) as error:
            http_code = "N/A"
            status = "DOWN"
            print(f"Connection detail: {type(error).__name__}")

        except Exception as error:
            http_code = "N/A"
            status = "CHECK_FAILED"
            print(f"Error detail: {type(error).__name__}")

        response_time_ms = (time.perf_counter() - start_time) * 1000

        previous_status = previous_states.get(url, "UNKNOWN")

        if status == "UP":
            up_count += 1
        elif status == "DOWN":
            down_count += 1
        elif status == "HTTP_ERROR":
            http_error_count += 1
        elif status == "CHECK_FAILED":
            check_failed_count += 1

        print(f"Website: {url}")
        print(f"Time checked: {checked_at}")
        print(f"Previous status: {previous_status}")
        print(f"Current status: {status}")
        print(f"HTTP code: {http_code}")
        print(f"Response time: {response_time_ms:.2f} ms")

        with open("website_checks.log", "a", encoding="utf-8") as log_file:
            log_file.write(
                f"{checked_at} | {url} | {status} | HTTP code: {http_code} | Response time: {response_time_ms:.2f} ms\n"
            )

        notification_sent = True

        try:
            if status == "DOWN" and previous_status != "DOWN":
                send_down_alert(url, checked_at)

            elif status == "UP" and previous_status == "DOWN":
                send_recovery_alert(url, checked_at)

        except Exception as error:
            notification_sent = False
            print(f"Email notification failed: {type(error).__name__}")

        # Save the new state only when notification succeeds
        if status in ("UP", "DOWN") and notification_sent:
            previous_states[url] = status

    # Save website states for the next scheduled run
    STATE_FILE.write_text(
        json.dumps(previous_states, indent=4),
        encoding="utf-8"
    )

    print("\nAll website checks completed.")
    print("Results saved to website_checks.log")
    print("Website states saved to website_states.json")

    total_checked = up_count + down_count + http_error_count + check_failed_count

    print("\n========== MONITORING SUMMARY ==========")
    print(f"Total websites checked: {total_checked}")
    print(f"UP: {up_count}")
    print(f"DOWN: {down_count}")
    print(f"HTTP_ERROR: {http_error_count}")
    print(f"CHECK_FAILED: {check_failed_count}")
    print("========================================")
