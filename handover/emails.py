"""The hand-over receipt email: tells the owner that the item was collected, when and from whom."""
from django.template.loader import render_to_string

from core.mail import send_email


def send_hand_over_receipt(hand_over):
    claim = hand_over.claim
    text = render_to_string('handover/email/hand_over_receipt.txt', {'hand_over': hand_over, 'claim': claim})
    return send_email('You have collected your item', text, claim.user.email)
