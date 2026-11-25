"""
Tests for:  python manage.py add_sample_data   (and --remove)
Run:  python manage.py test core.test_sample_data
"""
import shutil
import tempfile
from io import StringIO
from unittest.mock import patch

from django.core import mail
from django.core.files.storage import FileSystemStorage
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from claims.models import Claim
from core.testing import make_admin, make_student
from handover.models import HandOver
from items.models import FoundItem, ItemReport
from matching.models import Match
from posts.models import Post

MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA)
class SampleDataTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.folder = tempfile.mkdtemp()                       # private report photos go here in the tests
        patcher = patch.object(ItemReport._meta.get_field('photo'), 'storage', FileSystemStorage(location=self.folder))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(shutil.rmtree, self.folder, ignore_errors=True)
        self.officer = make_admin()
        self.jane = make_student()                              # someone who was there before

    def add(self):
        call_command('add_sample_data', stdout=StringIO())

    def test_it_fills_every_part_of_the_site_without_sending_emails(self):
        self.add()
        self.assertEqual(User.objects.filter(email__startswith='sample.').count(), 10)
        self.assertEqual(FoundItem.objects.count(), 34)
        self.assertEqual(FoundItem.objects.filter(status=FoundItem.Status.IN_CUSTODY).count(), 26)
        self.assertEqual(ItemReport.objects.count(), 25)
        self.assertEqual(set(Claim.objects.values_list('status', flat=True)),
                         {'pending', 'more_evidence', 'approved', 'rejected', 'closed'})
        self.assertEqual(HandOver.objects.count(), 3)
        self.assertEqual(Post.objects.count(), 10)
        self.assertGreater(Match.objects.count(), 20)
        self.assertEqual(ItemReport.objects.exclude(photo='').count(), 3)
        self.assertEqual(mail.outbox, [])                       # no match alerts or other emails

    def test_the_pages_show_the_sample_items(self):
        self.add()
        self.client.force_login(self.jane)
        page = self.client.get(reverse('search:search'))
        self.assertEqual(page.context['page'].paginator.count, 26)       # every item still at the desk
        self.client.force_login(self.officer)
        self.assertContains(self.client.get(reverse('items:desk_expired')), 'Blue umbrella')
        self.assertContains(self.client.get(reverse('items:desk_matches')), 'Kevin Mwangi')
        self.assertContains(self.client.get(reverse('claims:desk_list')), 'Faith Wanjiku')

    def test_items_keep_the_day_they_were_recorded(self):
        self.add()
        self.client.force_login(self.officer)
        page = self.client.get(reverse('core:desk'))
        self.assertEqual(page.context['recorded_today'], 1)        # only the ID card found today

    def test_same_typed_other_place_gets_the_place_points(self):
        self.add()
        keys = Match.objects.get(report__user__email='sample.mercy.njeri@strathmore.edu',
                                 found_item__place_other='Chapel steps')      # she typed "chapel steps"
        self.assertEqual(keys.score, 100)

    def test_it_runs_only_once(self):
        self.add()
        with self.assertRaises(CommandError):
            self.add()

    def test_it_needs_a_security_officer(self):
        self.officer.delete()
        with self.assertRaises(CommandError):
            self.add()

    def test_remove_takes_out_only_the_sample_data(self):
        before = (User.objects.count(), FoundItem.objects.count(), ItemReport.objects.count())
        self.add()
        call_command('add_sample_data', '--remove', stdout=StringIO())
        self.assertEqual((User.objects.count(), FoundItem.objects.count(), ItemReport.objects.count()), before)
        self.assertEqual((Claim.objects.count(), Match.objects.count(), Post.objects.count()), (0, 0, 0))
        self.assertTrue(User.objects.filter(pk=self.jane.pk).exists())
