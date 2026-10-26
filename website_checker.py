import urllib.request
import urllib.error
import socket
import time
from datetime import datetime

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
        print(f"Status: {status}")
        print(f"HTTP code: {http_code}")
        print(f"Response time: {response_time_ms:.2f} ms")

        with open("website_checks.log", "a", encoding="utf-8") as log_file:
            log_file.write(
                f"{checked_at} | {url} | {status} | HTTP code: {http_code} | Response time: {response_time_ms:.2f} ms\n"
            )

    print("\nAll website checks completed.")
    print("Results saved to website_checks.log")
    total_checked = up_count + down_count + http_error_count + check_failed_count
    print("\n========== MONITORING SUMMARY ==========")
    print(f"Total websites checked: {total_checked}")
    print(f"UP: {up_count}")
    print(f"DOWN: {down_count}")
    print(f"HTTP_ERROR: {http_error_count}")
    print(f"CHECK_FAILED: {check_failed_count}")
    print("========================================")
