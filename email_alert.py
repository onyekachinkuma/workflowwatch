import smtplib
from pathlib import Path
from email.message import EmailMessage


def send_email(subject, body):
    config_file = Path.home() / ".config/workflowwatch/email.env"

    settings = {}
    for line in config_file.read_text().splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            settings[key] = value

    sender = settings["GMAIL_ADDRESS"]
    password = settings["GMAIL_APP_PASSWORD"].replace(" ", "")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = sender
    message.set_content(body)

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as server:
        server.starttls()
        server.login(sender, password)
        server.send_message(message)


def send_down_alert(url, checked_at):
    subject = f"WorkflowWatch ALERT: {url} is DOWN"

    body = (
        f"Website: {url}\n"
        f"Status: DOWN\n"
        f"Time checked: {checked_at}\n"
        f"Action: Please investigate the website."
    )

    send_email(subject, body)
    print(f"DOWN alert sent for {url}")


def send_recovery_alert(url, checked_at):
    subject = f"WorkflowWatch RECOVERY: {url} is UP"

    body = (
        f"Website: {url}\n"
        f"Status: UP\n"
        f"Time checked: {checked_at}\n"
        f"Message: The website has recovered and is responding again."
    )

    send_email(subject, body)
    print(f"RECOVERY alert sent for {url}")
