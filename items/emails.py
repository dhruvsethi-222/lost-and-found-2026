"""The hand-in confirmation email for Staff (SF-O5)."""
from django.template.loader import render_to_string

from core.mail import send_email


def send_hand_in_confirmation(found_item):
    """Tells the Staff member that the item they logged has been received at the security desk."""
    report = found_item.handed_in_report
    text = render_to_string('items/email/hand_in_confirmation.txt',
                            {'report': report, 'found_item': found_item})
    return send_email('Security has received the item you handed in', text, report.user.email)
