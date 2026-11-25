"""
Tests for accounts. Each test name starts with the requirement it proves (e.g. ST_P1),
so it matches the test register (TC-ST-P1).  Run:  python manage.py test
"""
import os
import re
from io import StringIO
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from accounts.models import Admin, Role, Staff, Student, User
from config.settings import email_endings
from core.testing import PASSWORD, make_admin, make_staff, make_student

STUDENT_FORM = {'name': 'Jane Wanjiru', 'email': 'jane@strathmore.edu', 'admission_no': '227034',
                'password1': PASSWORD, 'password2': PASSWORD}
STAFF_FORM = {'name': 'Peter Otieno', 'email': 'otieno@strathmore.edu', 'staff_no': 's1043',
              'department': 'Computing', 'password1': PASSWORD, 'password2': PASSWORD}


def link_in(email):
    return re.search(r'https?://\S+', email.body).group(0)


# The agreed rule. Fixed here so an old .env file on a laptop cannot change what the tests check.
STRATHMORE_ONLY = override_settings(STUDENT_EMAIL_DOMAINS=['strathmore.edu'], STAFF_EMAIL_DOMAINS=['strathmore.edu'])


@STRATHMORE_ONLY
class RegistrationTests(TestCase):
    def test_ST_P1_student_registers_and_gets_verification_email(self):
        response = self.client.post(reverse('accounts:register'), STUDENT_FORM)
        self.assertRedirects(response, reverse('accounts:verification_sent'))
        user = User.objects.get(email='jane@strathmore.edu')
        self.assertEqual(user.role, Role.STUDENT)                      # ST-S1
        self.assertFalse(user.is_verified)
        self.assertEqual(len(mail.outbox), 1)                          # ST-O1 / EM-P1
        self.assertIn('/accounts/verify/', mail.outbox[0].body)

    def test_SY_P1_password_is_stored_only_as_a_hash(self):
        self.client.post(reverse('accounts:register'), STUDENT_FORM)
        user = User.objects.get(email='jane@strathmore.edu')
        self.assertNotEqual(user.password, PASSWORD)
        self.assertTrue(user.password.startswith('pbkdf2_sha256$'))
        self.assertTrue(user.check_password(PASSWORD))

    def test_SF_P1_staff_registers_with_staff_id_and_department(self):
        self.client.post(reverse('accounts:register_staff'), STAFF_FORM)
        user = User.objects.get(email='otieno@strathmore.edu')
        self.assertEqual((user.role, user.staff_no, user.department), (Role.STAFF, 'S1043', 'Computing'))        # SF-S1
        self.assertEqual(len(mail.outbox), 1)                          # SF-O1 / EM-P1
        self.assertEqual(mail.outbox[0].to, ['otieno@strathmore.edu'])

    def test_NFR01_only_exact_strathmore_emails_can_register(self):
        for email in ('jane@gmail.com', 'jane@sub.strathmore.edu', 'jane@strathmore.edu.ke'):
            response = self.client.post(reverse('accounts:register'), {**STUDENT_FORM, 'email': email})
            self.assertContains(response, 'Use your campus email ending in @strathmore.edu')
            response = self.client.post(reverse('accounts:register_staff'), {**STAFF_FORM, 'email': email})
            self.assertContains(response, 'Use your campus email ending in @strathmore.edu')
        self.assertFalse(User.objects.exists())

    def test_NFR01_capital_letters_in_the_email_are_accepted_and_saved_small(self):
        self.client.post(reverse('accounts:register'), {**STUDENT_FORM, 'email': 'Jane@Strathmore.EDU'})
        self.assertTrue(User.objects.filter(email='jane@strathmore.edu').exists())

    def test_NFR01_sign_up_pages_show_the_strathmore_example(self):
        for page in ('accounts:register', 'accounts:register_staff'):
            self.assertContains(self.client.get(reverse(page)), 'placeholder="name@strathmore.edu"')

    def test_NFR01_the_system_warns_when_env_allows_other_endings(self):
        from accounts.checks import check_email_endings
        self.assertEqual(check_email_endings(None), [])
        with self.settings(STUDENT_EMAIL_DOMAINS=['students.campus.ac.ke']):
            warnings = check_email_endings(None)
        self.assertEqual(len(warnings), 1)
        self.assertIn('STUDENT_EMAIL_DOMAINS=strathmore.edu', warnings[0].hint)

    def test_NFR01_a_blank_env_line_still_means_strathmore_only(self):
        with patch.dict(os.environ, {'STUDENT_EMAIL_DOMAINS': ''}):
            self.assertEqual(email_endings('STUDENT_EMAIL_DOMAINS'), ['strathmore.edu'])
        with patch.dict(os.environ, {'STUDENT_EMAIL_DOMAINS': 'Strathmore.edu, example.org'}):
            self.assertEqual(email_endings('STUDENT_EMAIL_DOMAINS'), ['strathmore.edu', 'example.org'])

    def test_NFR03_admission_number_must_be_digits(self):
        response = self.client.post(reverse('accounts:register'), {**STUDENT_FORM, 'admission_no': 'ABC12'})
        self.assertContains(response, 'Use digits only')

    def test_NFR03_duplicate_email_and_admission_number_are_refused(self):
        make_student()
        response = self.client.post(reverse('accounts:register'), STUDENT_FORM)
        self.assertContains(response, 'already exists')
        response = self.client.post(reverse('accounts:register'), {**STUDENT_FORM, 'email': 'other@strathmore.edu'})
        self.assertContains(response, 'admission number already exists')

    def test_NFR01_weak_or_mismatched_passwords_are_refused(self):
        response = self.client.post(reverse('accounts:register'), {**STUDENT_FORM, 'password1': '12345678', 'password2': '12345678'})
        self.assertContains(response, 'too common')
        response = self.client.post(reverse('accounts:register'), {**STUDENT_FORM, 'password2': 'Different-Pass-1'})
        self.assertContains(response, 'do not match')
        self.assertFalse(User.objects.exists())

    def test_NFR01_registration_can_never_create_an_admin(self):
        self.client.post(reverse('accounts:register'), {**STUDENT_FORM, 'role': 'admin', 'is_staff': 'on'})
        user = User.objects.get()
        self.assertEqual(user.role, Role.STUDENT)
        self.assertFalse(user.is_staff)


@STRATHMORE_ONLY
class VerificationTests(TestCase):
    def test_verification_link_verifies_the_account_once(self):
        self.client.post(reverse('accounts:register'), STUDENT_FORM)
        link = link_in(mail.outbox[0])
        response = self.client.get(link)
        self.assertRedirects(response, reverse('accounts:login'))
        self.assertTrue(User.objects.get().is_verified)
        response = self.client.get(link, follow=True)                 # second click: already verified
        self.assertContains(response, 'already verified')

    def test_the_link_stops_working_after_the_first_log_in(self):
        self.client.post(reverse('accounts:register'), STUDENT_FORM)
        link = link_in(mail.outbox[0])
        self.client.get(link)                                          # verify
        self.client.post(reverse('accounts:login'), {'username': STUDENT_FORM['email'], 'password': PASSWORD})
        user = User.objects.get()
        token = link.rstrip('/').split('/')[-1]
        self.assertFalse(default_token_generator.check_token(user, token))

    def test_a_made_up_link_is_refused(self):
        make_student(verified=False)
        response = self.client.get(reverse('accounts:verify', args=['MQ', 'made-up-token']))
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.get().is_verified)

    def test_resend_sends_a_new_link_only_to_unverified_accounts(self):
        make_student(verified=False)
        self.client.post(reverse('accounts:resend'), {'email': 'jane@strathmore.edu'})
        self.assertEqual(len(mail.outbox), 1)
        self.client.post(reverse('accounts:resend'), {'email': 'nobody@strathmore.edu'})
        self.assertEqual(len(mail.outbox), 1)                          # same answer, no email sent


class LoginTests(TestCase):
    def login(self, url_name, email):
        return self.client.post(reverse(url_name), {'username': email, 'password': PASSWORD})

    def test_ST_P2_unverified_student_cannot_log_in(self):
        make_student(verified=False)
        response = self.login('accounts:login', 'jane@strathmore.edu')
        self.assertContains(response, 'not verified yet')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_ST_P2_verified_student_logs_in_to_my_page(self):
        make_student()
        response = self.login('accounts:login', 'jane@strathmore.edu')
        self.assertRedirects(response, reverse('core:after_login'), target_status_code=302)
        self.assertRedirects(self.client.get(reverse('core:after_login')), reverse('core:my_page'))

    def test_SF_P2_verified_staff_logs_in(self):
        make_staff()
        self.login('accounts:login', 'otieno@strathmore.edu')
        self.assertIn('_auth_user_id', self.client.session)

    def test_wrong_password_is_refused(self):
        make_student()
        response = self.client.post(reverse('accounts:login'), {'username': 'jane@strathmore.edu', 'password': 'wrong'})
        self.assertContains(response, 'correct email and password')

    def test_AD_P1_admin_logs_in_on_the_desk_page_only(self):
        make_admin()
        response = self.login('accounts:login', 'achieng@strathmore.edu')
        self.assertContains(response, 'Security desk log-in page')
        response = self.login('accounts:desk_login', 'achieng@strathmore.edu')
        self.assertRedirects(response, reverse('core:after_login'), target_status_code=302)
        self.assertRedirects(self.client.get(reverse('core:after_login')), reverse('core:desk'))

    def test_students_cannot_log_in_on_the_desk_page(self):
        make_student()
        response = self.login('accounts:desk_login', 'jane@strathmore.edu')
        self.assertContains(response, 'This page is for security officers')

    def test_log_out(self):
        make_student()
        self.login('accounts:login', 'jane@strathmore.edu')
        self.client.post(reverse('accounts:logout'))
        self.assertNotIn('_auth_user_id', self.client.session)


class RoleAccessTests(TestCase):
    def test_NFR01_student_or_staff_opening_an_admin_page_is_refused(self):
        for person in (make_student(), make_staff()):
            self.client.force_login(person)
            self.assertEqual(self.client.get(reverse('core:desk')).status_code, 403)
            self.assertEqual(self.client.get(reverse('items:desk_record_found')).status_code, 403)

    def test_NFR01_admin_cannot_open_student_pages(self):
        self.client.force_login(make_admin())
        self.assertEqual(self.client.get(reverse('core:my_page')).status_code, 403)

    def test_NFR01_logged_out_visitors_are_sent_to_the_right_login_page(self):
        response = self.client.get(reverse('core:desk'))
        self.assertRedirects(response, reverse('accounts:desk_login') + '?next=/desk/')
        response = self.client.get(reverse('core:my_page'))
        self.assertRedirects(response, reverse('accounts:login') + '?next=/my/')

    def test_NFR01_session_ends_after_15_minutes_idle(self):
        self.assertEqual(settings.SESSION_COOKIE_AGE, 900)
        self.assertTrue(settings.SESSION_SAVE_EVERY_REQUEST)


class ModelTests(TestCase):
    def test_NFR08_student_staff_and_admin_classes_list_only_their_own_role(self):
        make_student(); make_staff(); make_admin()
        self.assertEqual(list(Student.objects.values_list('role', flat=True)), ['student'])
        self.assertEqual(list(Staff.objects.values_list('role', flat=True)), ['staff'])
        self.assertEqual(list(Admin.objects.values_list('role', flat=True)), ['admin'])
        self.assertEqual(User.objects.count(), 3)

    def test_createofficer_command_makes_a_verified_admin(self):
        call_command('createofficer', email='Desk@strathmore.edu', name='Desk Officer', officer_no='SO-9',
                     password=PASSWORD, stdout=StringIO())
        officer = User.objects.get(email='desk@strathmore.edu')
        self.assertEqual((officer.role, officer.is_verified), (Role.ADMIN, True))

    def test_superuser_is_an_admin(self):
        owner = User.objects.create_superuser('owner@strathmore.edu', PASSWORD, name='Owner')
        self.assertTrue(owner.is_admin_officer and owner.is_staff and owner.is_superuser)


class ManageAccountsTests(TestCase):
    """AD-P10: the Admin manages Student and Staff accounts."""

    def setUp(self):
        self.officer = make_admin()
        self.student = make_student()
        self.staff = make_staff()
        self.client.force_login(self.officer)

    def test_AD_P10_admin_sees_and_searches_student_and_staff_accounts(self):
        page = self.client.get(reverse('accounts:desk_accounts'))
        self.assertContains(page, 'Jane Wanjiru')
        self.assertContains(page, 'Peter Otieno')
        self.assertNotContains(page, 'achieng@strathmore.edu')          # Admin accounts are not listed
        found = self.client.get(reverse('accounts:desk_accounts'), {'q': '227034'}).context['page'].object_list
        self.assertEqual(list(found), [self.student])
        staff_only = self.client.get(reverse('accounts:desk_accounts'), {'role': 'staff'}).context['page'].object_list
        self.assertEqual(list(staff_only), [self.staff])

    def test_AD_P10_a_switched_off_account_cannot_log_in_and_can_be_switched_on_again(self):
        self.client.post(reverse('accounts:desk_account_switch', args=[self.student.pk]))
        self.student.refresh_from_db()
        self.assertFalse(self.student.is_active)
        self.assertTrue(User.objects.filter(pk=self.student.pk).exists())      # never deleted
        self.client.logout()
        response = self.client.post(reverse('accounts:login'), {'username': self.student.email, 'password': PASSWORD})
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.client.force_login(self.officer)
        self.client.post(reverse('accounts:desk_account_switch', args=[self.student.pk]))
        self.student.refresh_from_db()
        self.assertTrue(self.student.is_active)

    def test_a_switched_off_account_is_logged_out_straight_away(self):
        member = Client()
        member.force_login(self.student)
        self.client.post(reverse('accounts:desk_account_switch', args=[self.student.pk]))
        self.assertEqual(member.get(reverse('core:my_page')).status_code, 302)    # sent to the log-in page

    def test_AD_P10_admin_can_verify_an_email_by_hand(self):
        unverified = make_student(email='brian@strathmore.edu', admission_no='227035', verified=False)
        self.client.post(reverse('accounts:desk_account_verify', args=[unverified.pk]))
        unverified.refresh_from_db()
        self.assertTrue(unverified.is_verified)

    def test_admin_accounts_cannot_be_changed_from_this_page(self):
        other_officer = make_admin(email='otieno.k@strathmore.edu', officer_no='SO-002')
        response = self.client.post(reverse('accounts:desk_account_switch', args=[other_officer.pk]))
        self.assertEqual(response.status_code, 404)
        other_officer.refresh_from_db()
        self.assertTrue(other_officer.is_active)

    def test_opening_the_switch_address_in_the_browser_changes_nothing(self):
        self.client.get(reverse('accounts:desk_account_switch', args=[self.student.pk]))
        self.student.refresh_from_db()
        self.assertTrue(self.student.is_active)

    def test_NFR01_students_and_staff_cannot_manage_accounts(self):
        for person in (self.student, self.staff):
            self.client.force_login(person)
            self.assertEqual(self.client.get(reverse('accounts:desk_accounts')).status_code, 403)
            self.assertEqual(self.client.post(reverse('accounts:desk_account_switch', args=[self.staff.pk])).status_code, 403)


class DemoAccountMoveTests(TestCase):
    """The demo accounts move to @strathmore.edu in place; anything unclear is left for a person to check."""

    def test_demo_accounts_keep_their_id_password_and_reports(self):
        from django.utils import timezone

        from accounts.demo_accounts import move_demo_accounts
        from items.models import ItemReport
        jane = make_student(email='jane@students.campus.ac.ke', admission_no='100001')
        grace = make_admin(email='achieng@campus.ac.ke')
        report = ItemReport.objects.create(user=jane, type='lost', category='wallet', description='Black wallet',
                                           date=timezone.localdate(), place='library')
        self.assertEqual(move_demo_accounts(User), [])
        jane.refresh_from_db()
        grace.refresh_from_db()
        self.assertEqual((jane.email, grace.email), ('jane@strathmore.edu', 'achieng@strathmore.edu'))
        self.assertTrue(jane.check_password(PASSWORD))                        # same password
        self.assertEqual(ItemReport.objects.get(pk=report.pk).user, jane)     # same report, still linked

    def test_an_address_already_in_use_is_not_taken(self):
        from accounts.demo_accounts import move_demo_accounts
        old = make_student(email='jane@students.campus.ac.ke', admission_no='100001')
        make_student(email='jane@strathmore.edu', admission_no='100009')
        notes = move_demo_accounts(User)
        old.refresh_from_db()
        self.assertEqual(old.email, 'jane@students.campus.ac.ke')
        self.assertIn('already used by another account', notes[0])

    def test_an_account_that_is_not_the_demo_one_is_flagged_not_changed(self):
        from accounts.demo_accounts import move_demo_accounts
        someone = make_staff(email='otieno@campus.ac.ke')
        someone.name = 'Someone Else'
        someone.save()
        notes = move_demo_accounts(User)
        someone.refresh_from_db()
        self.assertEqual(someone.email, 'otieno@campus.ac.ke')
        self.assertIn('Check it by hand', notes[0])
