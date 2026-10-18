# WorkflowWatch

WorkflowWatch is a beginner-friendly Python project that checks whether a website responds and records the result.

## Current Features

- Accepts a website URL from the user.
- Adds HTTPS when the URL has no HTTP or HTTPS prefix.
- Sends a request with a 10-second timeout.
- Reports the HTTP response status or the type of connection error.
- Records the check time, URL, and result in a log file.
- Preserves earlier results when new checks are recorded.

## Requirements

- Python 3
- An internet connection for checking public websites

## How to Run

Open a terminal in the project folder and run:

```bash
python3 website_checker.py
```

Enter a website URL when prompted.

## Log History

Results are saved in `website_checks.log`.

To view the saved results, run:

```bash
cat website_checks.log
```

## Current Limitations

- Checks one website at a time.
- Requires the user to start each check manually.
- Does not yet send alerts or perform scheduled monitoring.

## Planned Improvements

- Check multiple websites.
- Run checks automatically at regular intervals.
- Improve monitoring history and reporting.
- Add email alerts for failed checks.

## Learning Goals

This project is helping me practise Python, HTTP requests, error handling, file logging, and monitoring fundamentals as part of my Cloud and DevOps learning journey.
