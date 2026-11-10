"""Sending the verification email (ST-O1, SF-O1, EM-P1)."""
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .tokens import verification_token


def verification_link(request, user):
    """Builds the full link, e.g. https://site/accounts/verify/MQ/abc123.../"""
    uid = urlsafe_base64_encode(force_bytes(user.pk))   # the account id, made safe for a web address
    token = verification_token.make_token(user)         # the secret part
    return request.build_absolute_uri(reverse('accounts:verify', args=[uid, token]))


def send_verification_email(request, user):
    context = {'user': user, 'link': verification_link(request, user)}
    body = render_to_string('accounts/email/verify_email.txt', context)
    send_mail('Confirm your Lost and Found account', body, None, [user.email])
