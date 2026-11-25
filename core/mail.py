"""
Sends one email through the email service chosen in .env (EMAIL_BACKEND):
on a laptop the window running the site, or the Brevo email API when it is switched on.

If an email cannot be sent (no internet, a wrong API key, the email service is down),
the page still finishes and the problem is written in the window running the site.
"""
import logging

from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_email(subject, text, to_address):
    """Sends the email. Returns True when it was sent, and False when it could not be sent."""
    try:
        send_mail(subject, text, None, [to_address])     # None = DEFAULT_FROM_EMAIL from settings.py
        return True
    except Exception as error:                            # any problem in the email service
        logger.warning('Email "%s" to %s could not be sent: %s', subject, to_address, error)
        return False
