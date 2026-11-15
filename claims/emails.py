"""The claim decision email (EM-P3)."""
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse


def send_claim_decision(claim):
    """Tells the claimant what the Admin decided, with the reason."""
    text = render_to_string('claims/email/claim_decision.txt', {
        'claim': claim,
        'link': settings.SITE_URL + reverse('core:my_page'),
        'collection_hours': settings.DESK_COLLECTION_HOURS,
    })
    send_mail(f'Your claim: {claim.get_status_display().lower()}', text, None, [claim.user.email])
