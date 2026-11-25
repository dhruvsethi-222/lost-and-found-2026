"""
Sending the verification email (ST-O1, SF-O1, EM-P1).

The link in the email has two parts:
    /accounts/verify/<account id>/<token>/
The token is a secret code made by Django's ready-made token tool (the same one
Django uses for "forgot password" links). Nobody can guess it, and it stops
working after 3 days (PASSWORD_RESET_TIMEOUT in settings.py).
"""
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from core.mail import send_email


def verification_link(request, user):
    """Builds the full link, e.g. https://site/accounts/verify/MQ/abc123.../"""
    account_id = urlsafe_base64_encode(force_bytes(user.pk))    # the id, written in a web-safe way
    token = default_token_generator.make_token(user)            # the secret code
    path = reverse('accounts:verify', args=[account_id, token])
    return request.build_absolute_uri(path)                     # adds https://site in front


def send_verification_email(request, user):
    """Returns True when the email was sent, False when it could not be sent."""
    details = {'user': user, 'link': verification_link(request, user)}
    # 1. fill in the two versions of the email: plain text, and the one with the button
    text = render_to_string('accounts/email/verify_email.txt', details)
    html = render_to_string('accounts/email/verify_email.html', details)
    # 2. hand both to the email service
    return send_email('Confirm your Lost and Found account', text, user.email, html)
