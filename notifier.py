"""
notifier.py
Sends an email alert when a matching listing is found.
"""

import smtplib
import os
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()  # reads the .env file into environment variables

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")


def send_email_alert(subject, body, to_address=None):
    """
    Send an email using Gmail's SMTP server.

    to_address can be:
      - None            -> sends to yourself (GMAIL_ADDRESS)
      - a single string -> "friend@example.com"
      - a list/tuple    -> ["me@example.com", "friend@example.com"]
    """
    if to_address is None:
        # Default: just send to yourself
        recipients = [GMAIL_ADDRESS]
    elif isinstance(to_address, str):
        # Single email passed as a plain string
        recipients = [to_address]
    else:
        # Assume it's already a list/tuple of addresses
        recipients = list(to_address)

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = GMAIL_ADDRESS
    # Join the list with commas for the visible "To" header
    # (e.g. "a@example.com, b@example.com")
    msg["To"] = ", ".join(recipients)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        # sendmail needs an actual list of recipients (not just the
        # comma-joined header string) to know who to deliver to
        server.sendmail(GMAIL_ADDRESS, recipients, msg.as_string())

    print(f"Email sent to {', '.join(recipients)}: {subject}")


if __name__ == "__main__":
    # Quick test - running this file directly sends a test email
    send_email_alert(
        subject="PC Parts Bot - Test Email",
        body="If you're reading this, your email notifications are working!"
    )