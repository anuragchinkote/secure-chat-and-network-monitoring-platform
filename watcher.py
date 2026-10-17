
import logging
import os
import smtplib
import socket
import time

from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

HOST = "127.0.0.1"
PORT = 55556

INTERVAL_SECONDS = 10
TIMEOUT_SECONDS = 2

Path("logs").mkdir(exist_ok=True)

logging.basicConfig(
    filename="logs/network.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


def get_email_config():
    """Load and validate email configuration without exposing secrets."""
    email_from = os.getenv("MONITOR_EMAIL")
    email_password = os.getenv("MONITOR_EMAIL_APP_PASSWORD")
    email_to = os.getenv("ALERT_EMAIL")

    missing = [
        name
        for name, value in [
            ("MONITOR_EMAIL", email_from),
            ("MONITOR_EMAIL_APP_PASSWORD", email_password),
            ("ALERT_EMAIL", email_to),
        ]
        if not value or not value.strip()
    ]

    if missing:
        raise RuntimeError(
            "Missing email configuration in .env: "
            + ", ".join(missing)
        )

    return email_from, email_password, email_to


def send_alert(subject, body):
    """Send one email alert. Return True only if delivery is accepted."""
    try:
        email_from, email_password, email_to = get_email_config()

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = email_from
        message["To"] = email_to
        message.set_content(body)

        with smtplib.SMTP(
            SMTP_HOST,
            SMTP_PORT,
            timeout=10,
        ) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(email_from, email_password)
            smtp.send_message(message)

        logging.info(
            "event=email_alert status=sent subject=%s",
            subject,
        )
        print(f"Email alert sent: {subject}")
        return True

    except (OSError, smtplib.SMTPException, RuntimeError) as exc:
        logging.error(
            "event=email_alert status=failed subject=%s error=%s",
            subject,
            exc,
        )
        print(f"Email alert failed: {exc}")
        return False


def check_server():
    """Check TCP connectivity and return status, latency, and error."""
    start = time.perf_counter()

    try:
        with socket.create_connection(
            (HOST, PORT),
            timeout=TIMEOUT_SECONDS,
        ):
            latency_ms = (time.perf_counter() - start) * 1000

        logging.info(
            "event=connectivity status=UP host=%s port=%s "
            "latency_ms=%.2f",
            HOST,
            PORT,
            latency_ms,
        )

        print(f"UP   {HOST}:{PORT}  {latency_ms:.2f} ms")
        return "UP", latency_ms, None

    except OSError as exc:
        logging.error(
            "event=connectivity status=DOWN host=%s port=%s error=%s",
            HOST,
            PORT,
            exc,
        )

        print(f"DOWN {HOST}:{PORT}  {exc}")
        return "DOWN", None, str(exc)


def handle_status_change(status, previous_status, error=None):
    """Send alerts only when the observed server state changes."""
    if status == previous_status:
        return

    if status == "DOWN":
        logging.error(
            "event=server_status status=DOWN"
        )

        details = error or "Connection failed."
        send_alert(
            "Chat server DOWN",
            (
                f"The chat server at {HOST}:{PORT} is unreachable.\n\n"
                f"Details: {details}\n"
                f"Check the server process and network configuration."
            ),
        )

        print("ALERT: server is DOWN")

    elif previous_status == "DOWN":
        logging.info(
            "event=server_status status=UP"
        )

        send_alert(
            "Chat server RECOVERED",
            (
                f"The chat server at {HOST}:{PORT} is reachable again."
            ),
        )

        print("RECOVERED: server is UP")


def main():
    print(
        f"Monitoring {HOST}:{PORT} "
        f"every {INTERVAL_SECONDS} seconds"
    )

    previous_status = None

    try:
        # Validate configuration before the monitoring loop begins.
        get_email_config()
        print("Email alert configuration found.")

    except RuntimeError as exc:
        logging.error("event=configuration status=invalid error=%s", exc)
        print(f"Configuration error: {exc}")
        print("Check your .env file. Do not share its credentials.")
        return

    try:
        while True:
            cycle_start = time.perf_counter()

            status, _, error = check_server()

            if status != previous_status:
                handle_status_change(
                    status,
                    previous_status,
                    error,
                )
                previous_status = status

            elapsed = time.perf_counter() - cycle_start
            time.sleep(max(0, INTERVAL_SECONDS - elapsed))

    except KeyboardInterrupt:
        print("\nMonitor stopped.")
        logging.info("event=monitor status=stopped")


if __name__ == "__main__":
    main()
