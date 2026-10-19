import urllib.request
import urllib.error
import socket
from datetime import datetime

websites = input(
    "Enter website URLs separated by commas "
    "(for example, https://example.com, https://www.google.com): "
).strip()

urls = [url.strip() for url in websites.split(",") if url.strip()]

if not urls:
    print("No website URLs entered. Please try again.")
else:
    for url in urls:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        print(f"\nChecking {url} ...")
        checked_at = datetime.now().isoformat(timespec="seconds")

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

        print(f"Website: {url}")
        print(f"Time checked: {checked_at}")
        print(f"Status: {status}")
        print(f"HTTP code: {http_code}")

        with open("website_checks.log", "a", encoding="utf-8") as log_file:
            log_file.write(
                f"{checked_at} | {url} | {status} | HTTP code: {http_code}\n"
            )

    print("\nAll website checks completed.")
    print("Results saved to website_checks.log")
