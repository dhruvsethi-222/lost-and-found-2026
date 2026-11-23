"""Tests for the shared pages, the Admin's reports and the backup."""
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from claims.models import Claim
from core.testing import make_admin, make_student
from core.views import period
from handover.models import HandOver
from items.models import FoundItem, ItemReport


class PageTests(TestCase):
    def test_home_page_opens_for_everyone(self):
        response = self.client.get(reverse('core:home'))
        self.assertContains(response, 'Lost something on campus?')

    def test_menu_matches_the_role(self):
        self.client.force_login(make_student())
        self.assertContains(self.client.get(reverse('core:my_page')), 'Report an item')
        self.client.force_login(make_admin())
        response = self.client.get(reverse('core:desk'))
        self.assertContains(response, 'Record found item')
        self.assertNotContains(response, 'Report an item')

    def test_unknown_page_gives_404(self):
        self.assertEqual(self.client.get('/no-such-page/').status_code, 404)

    def test_template_notes_never_show_on_a_page(self):
        # A {# note #} in a template must stay on one line, or it shows up on the page.
        for name in ('accounts:register', 'accounts:register_staff', 'accounts:login',
                     'accounts:desk_login', 'accounts:resend'):
            self.assertNotContains(self.client.get(reverse(name)), '{#')
        self.client.force_login(make_student())
        for name in ('items:report', 'search:search', 'core:my_page', 'posts:list'):
            self.assertNotContains(self.client.get(reverse(name)), '{#')
        self.client.force_login(make_admin())
        for name in ('items:desk_record_found', 'items:desk_found_list', 'items:desk_reports', 'core:desk',
                     'items:desk_matches', 'claims:desk_list', 'items:desk_expired', 'handover:list',
                     'accounts:desk_accounts', 'core:reports'):
            self.assertNotContains(self.client.get(reverse(name)), '{#')


class ReportsTests(TestCase):
    """AD-R1: the Admin's reports, and NFR-04: the audit log."""

    def setUp(self):
        self.officer = make_admin()
        self.student = make_student()
        today = timezone.localdate()
        # Three lost reports: two in the Library, one in the Cafeteria.
        for place, category in (('library', 'wallet'), ('library', 'phone'), ('cafeteria', 'wallet')):
            ItemReport.objects.create(user=self.student, type='lost', category=category, description='x',
                                      place=place, date=today)
        # One item received, then claimed, approved and handed over.
        self.item = FoundItem.objects.create(recorded_by=self.officer, category='wallet', description='Black wallet',
                                             place='library', date_found=today, photo='found_items/x.png',
                                             status=FoundItem.Status.RETURNED)
        claim = Claim.objects.create(found_item=self.item, user=self.student, answers='Mine', status='approved',
                                     decided_by=self.officer, reason='Details match', decided_at=timezone.now())
        HandOver.objects.create(claim=claim, released_by=self.officer, collector_id='227034')
        # One old item disposed of today.
        FoundItem.objects.create(recorded_by=self.officer, category='umbrella', description='Blue umbrella',
                                 place='cafeteria', date_found=today - timedelta(days=120), photo='found_items/x.png',
                                 status=FoundItem.Status.DISPOSED, disposed_by=self.officer,
                                 disposed_at=timezone.now(), disposal_reason='Donated')
        self.client.force_login(self.officer)

    def test_AD_R1_counts_items_received_returned_and_disposed(self):
        context = self.client.get(reverse('core:reports')).context
        self.assertEqual((context['received'], context['returned'], context['disposed'], context['lost_reported']),
                         (2, 1, 1, 3))
        self.assertEqual((context['approved'], context['pending_now']), (1, 0))

    def test_AD_R1_shows_where_most_items_are_lost(self):
        context = self.client.get(reverse('core:reports')).context
        self.assertEqual(context['top_places'][0], ('Library', 2))
        self.assertEqual(context['top_categories'][0], ('Wallet or purse', 2))

    def test_NFR04_the_audit_log_lists_every_decision_hand_over_and_disposal(self):
        page = self.client.get(reverse('core:reports'))
        kinds = [entry['what'] for entry in page.context['audit_log']]
        self.assertCountEqual(kinds, ['Claim approved', 'Handed over', 'Disposed'])
        for entry in page.context['audit_log']:
            self.assertEqual(entry['officer'], self.officer)        # who
            self.assertIsNotNone(entry['when'])                     # when
            self.assertTrue(entry['reason'])                        # why
        self.assertContains(page, 'Details match')

    def test_AD_R1_the_period_can_be_changed(self):
        last_year = timezone.localdate() - timedelta(days=365)
        context = self.client.get(reverse('core:reports'), {'date_from': last_year.isoformat(),
                                                            'date_to': (last_year + timedelta(days=7)).isoformat()}).context
        self.assertEqual((context['received'], context['returned'], context['lost_reported']), (0, 0, 0))

    def test_from_must_be_before_to(self):
        today = timezone.localdate()
        page = self.client.get(reverse('core:reports'), {'date_from': today.isoformat(),
                                                         'date_to': (today - timedelta(days=3)).isoformat()})
        self.assertContains(page, 'must be on or before')

    def test_AD_R1_a_period_covers_whole_days_in_campus_time(self):
        # 23:30 on the last day is inside the period; 00:10 the next morning is not.
        start, end = period(date(2026, 11, 1), date(2026, 11, 2))
        late_evening = timezone.make_aware(datetime(2026, 11, 2, 23, 30))
        next_morning = timezone.make_aware(datetime(2026, 11, 3, 0, 10))
        self.assertTrue(start <= late_evening <= end)
        self.assertFalse(start <= next_morning <= end)

    def test_NFR01_students_cannot_see_the_reports(self):
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(reverse('core:reports')).status_code, 403)


class BackupTests(TestCase):
    """NFR-07: a backup of the database can be restored."""

    def test_NFR07_a_backup_can_be_restored(self):
        officer = make_admin()
        student = make_student()
        ItemReport.objects.create(user=student, type='lost', category='wallet', description='Black wallet',
                                  place='library', date=timezone.localdate())

        # 1. Back up: Django's dumpdata writes every record to a file.
        with tempfile.TemporaryDirectory() as folder:
            backup = Path(folder) / 'backup.json'
            call_command('dumpdata', 'accounts', 'items', '--output', str(backup), verbosity=0)

            # 2. Something goes wrong and the records are lost.
            ItemReport.objects.all().delete()
            User.objects.all().delete()
            self.assertFalse(ItemReport.objects.exists())

            # 3. Restore: loaddata reads the file back in.
            call_command('loaddata', str(backup), verbosity=0)

        self.assertEqual(ItemReport.objects.get().description, 'Black wallet')
        self.assertTrue(User.objects.filter(email=officer.email).exists())
