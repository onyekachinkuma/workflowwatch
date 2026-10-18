import urllib.request
import urllib.error
from datetime import datetime

url = input("Enter a website URL (for example, https://example.com): ").strip()

if not url.startswith(("http://", "https://")):
    url = "https://" + url

print(f"\nChecking {url} ...")

checked_at = datetime.now().isoformat(timespec="seconds")

try:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "WorkflowWatch/0.2"}
    )

    with urllib.request.urlopen(request, timeout=10) as response:
        status = f"Website responded (HTTP {response.status})"

except urllib.error.HTTPError as error:
    status = f"Website responded with HTTP error {error.code}"

except Exception as error:
    status = f"Check failed ({type(error).__name__})"

print(f"Time checked: {checked_at}")
print(f"Status: {status}")

with open("website_checks.log", "a", encoding="utf-8") as log_file:
    log_file.write(f"{checked_at} | {url} | {status}\n")

print("Result saved to website_checks.log")
