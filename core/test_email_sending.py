"""
Tests for sending emails: through the Brevo email API, and what happens when an email cannot be sent.
No real email is sent: the call to Brevo is caught before it leaves the computer.
Run:  python manage.py test core.test_email_sending
"""
import json
from unittest.mock import MagicMock, patch

import requests

from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from claims.models import Claim
from core.testing import make_admin, make_student
from handover.tests import approved_claim

SIGN_UP = {'name': 'Dhruv Test', 'email': 'dhruv.test@strathmore.edu', 'admission_no': '100060',
           'password1': 'Campus-Pass-2026', 'password2': 'Campus-Pass-2026'}
BREVO = override_settings(EMAIL_BACKEND='anymail.backends.brevo.EmailBackend',
                          DEFAULT_FROM_EMAIL='Lost and Found <sender@example.com>',
                          ANYMAIL={'BREVO_API_KEY': 'test-key-not-real', 'REQUESTS_TIMEOUT': 10},
                          STUDENT_EMAIL_DOMAINS=['strathmore.edu'], STAFF_EMAIL_DOMAINS=['strathmore.edu'])
BROKEN = override_settings(EMAIL_BACKEND='core.testing.BrokenEmailBackend',
                           STUDENT_EMAIL_DOMAINS=['strathmore.edu'], STAFF_EMAIL_DOMAINS=['strathmore.edu'])


def brevo_answer():
    """What Brevo answers when it accepts an email."""
    answer = MagicMock(status_code=201)
    answer.json.return_value = {'messageId': '<123@smtp-relay.mailin.fr>'}
    answer.text = '{"messageId": "<123@smtp-relay.mailin.fr>"}'
    return answer


class BrevoEmailTests(TestCase):
    @BREVO
    def test_sign_up_sends_the_verification_link_through_the_brevo_api(self):
        with patch('requests.Session.request', return_value=brevo_answer()) as call:
            response = self.client.post(reverse('accounts:register'), SIGN_UP, follow=True)
        self.assertContains(response, 'Check your email')
        self.assertNotContains(response, 'could not be sent')
        asked = call.call_args.kwargs                       # what the system sent to Brevo
        sent = json.loads(asked['data'])
        self.assertEqual((asked['method'], asked['url']), ('POST', 'https://api.brevo.com/v3/smtp/email'))
        self.assertEqual(asked['headers']['api-key'], 'test-key-not-real')
        self.assertEqual(sent['to'], [{'email': 'dhruv.test@strathmore.edu'}])
        self.assertEqual(sent['sender'], {'email': 'sender@example.com', 'name': 'Lost and Found'})
        self.assertEqual(sent['subject'], 'Confirm your Lost and Found account')
        self.assertIn('/accounts/verify/', sent['textContent'])

    @BREVO
    def test_no_internet_does_not_break_sign_up(self):
        with patch('requests.Session.request', side_effect=requests.ConnectionError('No internet connection')), \
                self.assertLogs('core.mail', 'WARNING'):
            response = self.client.post(reverse('accounts:register'), SIGN_UP, follow=True)
        self.assertTrue(User.objects.filter(email='dhruv.test@strathmore.edu').exists())
        self.assertContains(response, 'the verification email could not be sent just now')

    @BREVO
    def test_brevo_refusing_the_email_does_not_break_sign_up(self):
        refused = MagicMock(status_code=401, reason='Unauthorized', text='{"code":"unauthorized","message":"Key not found"}')
        refused.json.return_value = {'code': 'unauthorized', 'message': 'Key not found'}
        with patch('requests.Session.request', return_value=refused), self.assertLogs('core.mail', 'WARNING') as log:
            response = self.client.post(reverse('accounts:register'), SIGN_UP, follow=True)
        self.assertIn('could not be sent', log.output[0])
        self.assertTrue(User.objects.filter(email='dhruv.test@strathmore.edu').exists())
        self.assertContains(response, 'the verification email could not be sent just now')


class MadeUpAccountTests(TestCase):
    """With Brevo switched on, the demo and sample accounts never get real emails: they are printed instead."""

    @BREVO
    def test_demo_and_sample_addresses_are_printed_not_sent(self):
        from core.mail import send_email
        for address in ('jane@strathmore.edu', 'sample.kevin.mwangi@strathmore.edu'):
            with patch('requests.Session.request') as call, patch('sys.stdout') as window:
                self.assertTrue(send_email('Your claim: approved', 'Hello', address))
            call.assert_not_called()                                  # nothing went to Brevo
            self.assertIn(address, ''.join(str(c.args[0]) for c in window.write.call_args_list))

    @BREVO
    def test_real_addresses_still_go_to_brevo(self):
        from core.mail import send_email
        with patch('requests.Session.request', return_value=brevo_answer()) as call:
            self.assertTrue(send_email('Your claim: approved', 'Hello', 'dhruv.test@strathmore.edu'))
        call.assert_called_once()

    def test_on_a_laptop_demo_accounts_get_their_emails_as_before(self):
        from django.core import mail

        from core.mail import send_email
        send_email('Your claim: approved', 'Hello', 'jane@strathmore.edu')
        self.assertEqual(mail.outbox[0].to, ['jane@strathmore.edu'])


@BROKEN
class EmailFailureTests(TestCase):
    """With no internet the action is still saved, and the page says the email was not sent."""

    def test_sign_up_is_saved_and_the_person_is_told_to_send_it_again(self):
        with self.assertLogs('core.mail', 'WARNING'):
            response = self.client.post(reverse('accounts:register'), SIGN_UP, follow=True)
        self.assertTrue(User.objects.filter(email='dhruv.test@strathmore.edu', is_verified=False).exists())
        self.assertContains(response, 'Wait a minute, then press')
        self.assertContains(response, 'send it again')

    def test_resend_gives_the_same_answer_as_always(self):
        make_student(email='amina@strathmore.edu', verified=False, admission_no='100003')
        with self.assertLogs('core.mail', 'WARNING'):
            response = self.client.post(reverse('accounts:resend'), {'email': 'amina@strathmore.edu'}, follow=True)
        self.assertContains(response, 'Check your email')

    def test_a_claim_decision_is_saved_and_the_admin_is_told_the_email_failed(self):
        officer = make_admin()
        claim = approved_claim(officer, make_student())
        claim.status = Claim.Status.PENDING
        claim.save()
        self.client.force_login(officer)
        with self.assertLogs('core.mail', 'WARNING'):
            response = self.client.post(reverse('claims:desk_verify', args=[claim.pk]),
                                        {'decision': 'reject', 'reason': 'Details do not match'}, follow=True)
        claim.refresh_from_db()
        self.assertEqual(claim.status, Claim.Status.REJECTED)
        self.assertContains(response, 'the email to the claimant could not be sent')

    def test_a_hand_over_is_saved_and_the_admin_is_told_the_receipt_failed(self):
        officer = make_admin()
        claim = approved_claim(officer, make_student())
        self.client.force_login(officer)
        with self.assertLogs('core.mail', 'WARNING'):
            response = self.client.post(reverse('handover:record', args=[claim.pk]), {'collector_id': '227034'}, follow=True)
        self.assertContains(response, 'The item is now Returned')
        self.assertContains(response, 'The receipt email could not be sent')
