import logging

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.core.config import SENDGRID_API_KEY, SENDER_EMAIL

logger = logging.getLogger(__name__)

DOLAR_API_URL = "https://dolarapi.com/v1/dolares"


class EmailService:

    @staticmethod
    def send(to: str, subject: str, body_html: str) -> bool:
        if not SENDGRID_API_KEY or not SENDER_EMAIL:
            logger.warning("SendGrid not configured — email not sent.")
            return False
        try:
            message = Mail(
                from_email=SENDER_EMAIL,
                to_emails=to,
                subject=subject,
                html_content=body_html,
            )
            sg = SendGridAPIClient(SENDGRID_API_KEY)
            sg.send(message)
            logger.info("Email sent to %s | subject: %s", to, subject)
            return True
        except Exception as exc:
            logger.error("SendGrid error: %s", exc)
            return False
