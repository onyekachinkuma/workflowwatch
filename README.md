# WorkflowWatch

WorkflowWatch is a beginner-friendly Python project that checks whether websites respond and records the results. It also tracks website incidents and manages email notifications when monitored websites go down or recover.

## Current Features

- Reads multiple website URLs from `monitored_websites.txt`.
- Ignores blank lines and comments in the website list.
- Adds HTTPS when a URL has no HTTP or HTTPS prefix.
- Checks each website one at a time.
- Uses a 10-second timeout for each request.
- Reports the HTTP response status or the type of connection error.
- Records the check time, URL, and result in a log file.
- Preserves earlier results when new checks are recorded.
- Tracks website states between monitoring runs.
- Creates and manages website incidents.
- Sends DOWN and recovery email notifications.
- Retries failed notifications using a controlled retry process.

## Requirements

- Python 3
- An internet connection for checking public websites
- Gmail SMTP credentials for email notifications

## How to Run

Open a terminal in the project folder and run:

    python3 website_checker.py

The program reads website URLs from `monitored_websites.txt`.

Add one website URL per line. For example:

    https://example.com
    https://www.google.com

You can also add comments by starting a line with `#`.

## Log History

Results are saved in `website_checks.log`.

To view the saved results, run:

    cat website_checks.log

## Incident Management

- Creates an incident when a website changes to DOWN.
- Prevents duplicate open incidents for repeated DOWN results.
- Closes an open incident when the website recovers.
- Preserves incident history in `incidents.json`.
- Tracks DOWN and recovery notification status separately.
- Records notification attempts and delivery errors.

## Notification Management

- Processes pending DOWN and recovery notifications.
- Keeps failed notifications pending for retry.
- Uses retry delays and a maximum of three worker attempts.
- Uses file locking to coordinate incident updates and notification processing.
- Prevents cooperating notification workers from processing the same pending notification simultaneously.
- Saves notification delivery results independently of website state.

## Incident and State Files

- `incidents.json` stores incident history and notification delivery status.
- `website_states.json` stores the latest known status of each website.
- `website_checks.log` stores individual monitoring results.

## Email Delivery

- Uses Gmail SMTP with TLS.
- Reads Gmail credentials from a private configuration file outside the project.
- Retries certain temporary SMTP connection failures.
- Does not mark a notification as sent when delivery fails.
- Email delivery failures do not stop the website monitoring run.

Email sending is handled by `email_alert.py`.

Gmail credentials are stored in:

`~/.config/workflowwatch/email.env`

Never commit this file or share its contents.

## Automatic Monitoring

This development copy can be run manually using:

    python3 website_checker.py

The separate live WorkflowWatch installation has a cron job configured to run every five minutes. That scheduled job runs from `/home/onyekachi/workflowwatch`, not from this development directory.

## Testing

Run the automated test suite:

    python3 -m unittest -v

## Current Limitations

- Website checks focus on HTTP availability and response status.
- The project does not yet verify website forms or confirm that business emails arrive.
- If form monitoring is added, captcha-protected forms will need human intervention.
- The project does not yet provide a customer-facing dashboard or multi-customer account management.
- Email delivery currently uses Gmail SMTP.

## Learning Goals

This project helps me practise:

- Python programming and HTTP requests.
- Website availability monitoring and error handling.
- Incident creation, recovery, and history management.
- Email notifications and retry handling.
- File storage, logging, and concurrency control.
- Testing and debugging a practical monitoring application.
