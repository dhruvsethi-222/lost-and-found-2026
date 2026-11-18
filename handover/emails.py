"""The hand-over receipt email: tells the owner that the item was collected, when and from whom."""
from django.core.mail import send_mail
from django.template.loader import render_to_string


def send_hand_over_receipt(hand_over):
    claim = hand_over.claim
    text = render_to_string('handover/email/hand_over_receipt.txt', {'hand_over': hand_over, 'claim': claim})
    send_mail('You have collected your item', text, None, [claim.user.email])
