import asyncio
import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def _send_sync(message: EmailMessage) -> None:
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as server:
        if settings.SMTP_STARTTLS:
            server.starttls()
        if settings.SMTP_USER:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(message)


async def send_email(to: str, subject: str, body: str) -> None:
    """Send an email, or log it when no SMTP host is configured.

    The console fallback is not a stub - it is the standard development
    path (Django ships the same idea as its console email backend). It
    keeps signup, verification and resend fully exercisable without a mail
    account, and switching to real delivery is a matter of filling in
    SMTP_HOST in .env, with no code change.
    """
    if not settings.SMTP_HOST:
        logger.warning(
            "SMTP_HOST is not set - printing this email instead of sending it.\n"
            "----- EMAIL (not sent) -----\n"
            "To: %s\nSubject: %s\n\n%s\n"
            "----------------------------",
            to,
            subject,
            body,
        )
        return

    message = EmailMessage()
    message["From"] = settings.SMTP_FROM
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    # smtplib is blocking. Running it directly in an async handler would
    # stall the event loop for the whole SMTP round trip, freezing every
    # other in-flight request.
    try:
        await asyncio.to_thread(_send_sync, message)
    except Exception:
        # A mail failure must not fail the request that triggered it - a
        # signup that created the account but 500s on the email is worse
        # than one that succeeds and offers a resend button.
        logger.exception("Failed to send email to %s", to)
