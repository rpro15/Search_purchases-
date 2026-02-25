"""Send an Excel attachment via mail.ru SMTP (STARTTLS on port 587).

Credentials are accepted at call-time and are never persisted to disk.

TODO: If you need to extend this module consider:
  - Reading SMTP_LOGIN / SMTP_PASSWORD from environment variables via python-dotenv
    as a fallback when no credentials are passed explicitly.
  - Adding retry logic and proper error reporting back to the Streamlit UI.
"""

import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SMTP_HOST = "smtp.mail.ru"
SMTP_PORT = 587


def send_email(
    recipient: str,
    subject: str,
    body: str,
    attachment_bytes: bytes,
    attachment_filename: str,
    smtp_login: str,
    smtp_password: str,
) -> None:
    """Send an e-mail with an Excel attachment via mail.ru SMTP.

    Args:
        recipient: Destination e-mail address.
        subject: E-mail subject line.
        body: Plain-text body of the message.
        attachment_bytes: Raw bytes of the file to attach.
        attachment_filename: File name shown to the recipient (e.g. ``results.xlsx``).
        smtp_login: Full mail.ru address used for authentication (e.g. ``user@mail.ru``).
        smtp_password: SMTP password (app-specific password recommended).

    Raises:
        smtplib.SMTPException: On any SMTP-level error.
    """
    msg = MIMEMultipart()
    msg["From"] = smtp_login
    msg["To"] = recipient
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain", "utf-8"))

    part = MIMEBase("application", "octet-stream")
    part.set_payload(attachment_bytes)
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f'attachment; filename="{attachment_filename}"',
    )
    msg.attach(part)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(smtp_login, smtp_password)
        server.sendmail(smtp_login, recipient, msg.as_string())
