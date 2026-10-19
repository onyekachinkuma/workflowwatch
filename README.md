# WorkflowWatch

WorkflowWatch is a beginner-friendly Python project that checks whether websites respond and records the results.

## Current Features

- Accepts multiple website URLs separated by commas.
- Adds HTTPS when a URL has no HTTP or HTTPS prefix.
- Checks each website one at a time.
- Uses a 10-second timeout for each request.
- Reports the HTTP response status or the type of connection error.
- Records the check time, URL, and result in a log file.
- Preserves earlier results when new checks are recorded.
- Handles empty input without attempting a website check.

## Requirements

- Python 3
- An internet connection for checking public websites

## How to Run

Open a terminal in the project folder and run:

```bash
python3 website_checker.py
```

Enter one or more website URLs separated by commas. For example:

```text
https://example.com, https://www.google.com
```

The program checks each website and displays its result.

## Log History

Results are saved in `website_checks.log`.

To view the saved results, run:

```bash
cat website_checks.log
```

## Current Limitations

- Requires the user to start each check manually.
- Does not yet send alerts.
- Does not automatically monitor websites at regular intervals.
- Checks website responses but does not verify forms, email notifications, or scheduled tasks.

## Planned Improvements

- Run checks automatically at regular intervals.
- Improve monitoring history and reporting.
- Add email alerts for failed checks.
- Explore monitoring for business forms and automation workflows.

## Learning Goals

This project is helping me practise Python, HTTP requests, error handling, file logging, and monitoring fundamentals as part of my Cloud and DevOps learning journey.
