"""The match alert email (SY-O2, EM-P2 -> ST-O3, SF-O3)."""
from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse

from core.mail import send_email


def send_match_alert(report):
    """
    Tells the person who reported a lost item that something like it is at the security desk.
    The email names the kind of item only. It never contains private details (NFR-02).
    """
    my_page_link = settings.SITE_URL + reverse('core:my_page')
    text = render_to_string('matching/email/match_alert.txt',
                            {'report': report, 'link': my_page_link})
    return send_email('A possible match for your lost item', text, report.user.email)
