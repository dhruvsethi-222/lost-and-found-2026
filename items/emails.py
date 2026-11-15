"""The hand-in confirmation email for Staff (SF-O5)."""
from django.core.mail import send_mail
from django.template.loader import render_to_string


def send_hand_in_confirmation(found_item):
    """Tells the Staff member that the item they logged has been received at the security desk."""
    report = found_item.handed_in_report
    text = render_to_string('items/email/hand_in_confirmation.txt',
                            {'report': report, 'found_item': found_item})
    send_mail('Security has received the item you handed in', text, None, [report.user.email])
