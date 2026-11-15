"""
Sending the verification email (ST-O1, SF-O1, EM-P1).

The link in the email has two parts:
    /accounts/verify/<account id>/<token>/
The token is a secret code made by Django's ready-made token tool (the same one
Django uses for "forgot password" links). Nobody can guess it, and it stops
working after 3 days (PASSWORD_RESET_TIMEOUT in settings.py).
"""
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def verification_link(request, user):
    """Builds the full link, e.g. https://site/accounts/verify/MQ/abc123.../"""
    account_id = urlsafe_base64_encode(force_bytes(user.pk))    # the id, written in a web-safe way
    token = default_token_generator.make_token(user)            # the secret code
    path = reverse('accounts:verify', args=[account_id, token])
    return request.build_absolute_uri(path)                     # adds https://site in front


def send_verification_email(request, user):
    # 1. fill in the email text (templates/accounts/email/verify_email.txt)
    text = render_to_string('accounts/email/verify_email.txt',
                            {'user': user, 'link': verification_link(request, user)})
    # 2. hand it to the email service
    send_mail('Confirm your Lost and Found account', text, None, [user.email])
