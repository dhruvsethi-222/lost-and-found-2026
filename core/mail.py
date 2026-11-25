"""
Sends one email through the email service chosen in .env (EMAIL_BACKEND):
on a laptop the window running the site, or the Brevo email API when it is switched on.

If an email cannot be sent (no internet, a wrong API key, the email service is down),
the page still finishes and the problem is written in the window running the site.

Made-up accounts (the five demo accounts and the "sample." accounts from add_sample_data) never
get real emails, because a real person could own the same address. Their emails are printed in
the window running the site instead, the same as on a laptop.
"""
import logging

from django.conf import settings
from django.core.mail import get_connection, send_mail

logger = logging.getLogger(__name__)

DEMO_ADDRESSES = ['jane@strathmore.edu', 'brian@strathmore.edu', 'amina@strathmore.edu',
                  'otieno@strathmore.edu', 'achieng@strathmore.edu']


def is_made_up(address):
    """True for the demo accounts and the sample accounts (their emails start with "sample.")."""
    return address in DEMO_ADDRESSES or address.startswith('sample.')


def sends_real_emails():
    """True when .env sends real emails (the Brevo API or an SMTP server)."""
    return 'anymail' in settings.EMAIL_BACKEND or 'smtp' in settings.EMAIL_BACKEND


def send_email(subject, text, to_address, html=None):
    """Sends the email. Returns True when it was sent, and False when it could not be sent."""
    connection = None                                     # None = the service chosen in .env
    if is_made_up(to_address) and sends_real_emails():
        connection = get_connection('django.core.mail.backends.console.EmailBackend')   # print it instead
    try:
        # html is the version with a button; email programs that cannot show it use the text
        send_mail(subject, text, None, [to_address], connection=connection, html_message=html)   # None = DEFAULT_FROM_EMAIL
        return True
    except Exception as error:                            # any problem in the email service
        logger.warning('Email "%s" to %s could not be sent: %s', subject, to_address, error)
        return False
