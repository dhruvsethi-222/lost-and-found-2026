"""The claim decision email (EM-P3)."""
from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse

from core.mail import send_email


def send_claim_decision(claim):
    """Tells the claimant what the Admin decided, with the reason."""
    text = render_to_string('claims/email/claim_decision.txt', {
        'claim': claim,
        'link': settings.SITE_URL + reverse('core:my_page'),
        'collection_hours': settings.DESK_COLLECTION_HOURS,
    })
    return send_email(f'Your claim: {claim.get_status_display().lower()}', text, claim.user.email)
