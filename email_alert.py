import smtplib
from pathlib import Path
from email.message import EmailMessage


def send_down_alert(url, checked_at):
    config_file = Path.home() / ".config/workflowwatch/email.env"

    settings = {}
    for line in config_file.read_text().splitlines():
        key, value = line.split("=", 1)
        settings[key] = value

    sender = settings["GMAIL_ADDRESS"]
    password = settings["GMAIL_APP_PASSWORD"].replace(" ", "")

    message = EmailMessage()
    message["Subject"] = f"WorkflowWatch ALERT: {url} is DOWN"
    message["From"] = sender
    message["To"] = sender
    message.set_content(
        f"Website: {url}\n"
        f"Status: DOWN\n"
        f"Time checked: {checked_at}\n"
    )

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as server:
        server.starttls()
        server.login(sender, password)
        server.send_message(message)

    print(f"Email alert sent for {url}")
