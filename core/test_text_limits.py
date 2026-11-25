"""
Tests for the agreed 500-character limit on every text box people type into.
Each box takes 500 characters and refuses 501, on the server and with maxlength="500" in the page.
Run:  python manage.py test core.test_text_limits
"""
import shutil
import tempfile
from datetime import timedelta

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from claims.models import Claim
from core.testing import make_admin, make_student, photo
from items.models import FoundItem, ItemReport, VerificationDetail
from posts.models import Post

MEDIA = tempfile.mkdtemp()
OK = 'a' * 500           # the longest text allowed
TOO_LONG = 'a' * 501     # one character too many
TODAY = timezone.localdate()


def found_item(officer, days_ago=0):
    item = FoundItem.objects.create(recorded_by=officer, category='wallet', description='Black wallet',
                                    place='library', photo='found_items/x.png',
                                    date_found=TODAY - timedelta(days=days_ago))
    VerificationDetail.objects.create(found_item=item, contents='Student ID')
    return item


class StudentTextLimitTests(TestCase):
    def setUp(self):
        self.officer = make_admin()
        self.student = make_student()
        self.client.force_login(self.student)

    def report(self, description):
        return self.client.post(reverse('items:report'), {
            'type': 'lost', 'category': 'wallet', 'description': description,
            'date': TODAY.isoformat(), 'place': 'library'})

    def test_report_description_takes_500_and_refuses_501(self):
        self.assertContains(self.report(TOO_LONG), 'at most 500 characters')
        self.assertFalse(ItemReport.objects.exists())
        self.report(OK)
        self.assertEqual(len(ItemReport.objects.get().description), 500)

    def test_report_page_limits_the_description_box(self):
        self.assertContains(self.client.get(reverse('items:report')), 'maxlength="500"')

    def test_post_and_reply_take_500_and_refuse_501(self):
        self.client.post(reverse('posts:list'), {'text': TOO_LONG})
        self.assertFalse(Post.objects.exists())
        self.client.post(reverse('posts:list'), {'text': OK})
        post = Post.objects.get()
        self.client.post(reverse('posts:reply', args=[post.pk]), {'text': TOO_LONG})
        self.assertEqual(post.replies.count(), 0)
        self.client.post(reverse('posts:reply', args=[post.pk]), {'text': OK})
        self.assertEqual(post.replies.count(), 1)
        page = self.client.get(reverse('posts:list'))
        self.assertContains(page, 'maxlength="500"', count=2)       # the new post box and the reply box

    def test_search_takes_500_and_refuses_501(self):
        found_item(self.officer)
        page = self.client.get(reverse('search:search'), {'q': TOO_LONG})
        self.assertContains(page, 'at most 500 characters')
        page = self.client.get(reverse('search:search'), {'q': 'wallet'})
        self.assertContains(page, 'maxlength="500"')
        self.assertEqual(page.context['page'].paginator.count, 1)

    def test_first_claim_answer_takes_500_and_refuses_501(self):
        item = found_item(self.officer)
        self.client.post(reverse('claims:new', args=[item.pk]), {'answers': TOO_LONG})
        self.assertFalse(Claim.objects.exists())
        self.client.post(reverse('claims:new', args=[item.pk]), {'answers': OK})
        self.assertEqual(len(Claim.objects.get().answers), 500)

    def test_each_follow_up_has_its_own_limit_and_the_whole_conversation_is_kept(self):
        item = found_item(self.officer)
        claim = Claim.objects.create(found_item=item, user=self.student, answers=OK)
        for round_number in (1, 2):
            claim.status, claim.reason, claim.decided_by = Claim.Status.MORE_EVIDENCE, 'What colour is it?', self.officer
            claim.save()
            response = self.client.post(reverse('claims:add_details', args=[claim.pk]), {'details': TOO_LONG})
            self.assertContains(response, 'at most 500 characters')
            self.client.post(reverse('claims:add_details', args=[claim.pk]), {'details': 'b' * 500})
            claim.refresh_from_db()
            self.assertEqual(claim.status, Claim.Status.PENDING)
        self.assertTrue(claim.answers.startswith(OK))                 # the first answer is still there
        self.assertEqual(claim.answers.count('b' * 500), 2)           # and both follow-ups
        self.assertGreater(len(claim.answers), 1500)                  # the whole conversation is longer than 500
        claim.full_clean()                                            # and it is still a valid claim


@override_settings(MEDIA_ROOT=MEDIA)
class AdminTextLimitTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.officer = make_admin()
        self.client.force_login(self.officer)

    def record(self, **changes):
        data = {'item-category': 'wallet', 'item-description': 'Black wallet', 'item-place': 'library',
                'item-date_found': TODAY.isoformat(), 'item-photo': photo(),
                'private-serial_no': '', 'private-marks': '', 'private-contents': 'Student ID'}
        data.update(changes)
        return self.client.post(reverse('items:desk_record_found'), data)

    def test_found_item_description_and_private_details_take_500_and_refuse_501(self):
        for field in ('item-description', 'private-serial_no', 'private-marks', 'private-contents'):
            response = self.record(**{field: TOO_LONG})
            self.assertContains(response, 'at most 500 characters', msg_prefix=field)
        self.assertFalse(FoundItem.objects.exists())
        self.record(**{'item-description': OK, 'private-serial_no': OK, 'private-marks': OK, 'private-contents': OK})
        detail = FoundItem.objects.get().verification_detail
        self.assertEqual((len(detail.serial_no), len(detail.marks), len(detail.contents)), (500, 500, 500))

    def test_record_found_item_page_limits_every_text_box(self):
        page = self.client.get(reverse('items:desk_record_found'))
        self.assertContains(page, 'maxlength="500"', count=5)     # description, other place, serial, marks, contents

    def test_decision_reason_takes_500_and_refuses_501(self):
        claim = Claim.objects.create(found_item=found_item(self.officer), user=make_student(), answers='Mine')
        url = reverse('claims:desk_verify', args=[claim.pk])
        response = self.client.post(url, {'decision': 'reject', 'reason': TOO_LONG})
        self.assertContains(response, 'at most 500 characters')
        claim.refresh_from_db()
        self.assertEqual(claim.status, Claim.Status.PENDING)
        self.client.post(url, {'decision': 'reject', 'reason': OK})
        claim.refresh_from_db()
        self.assertEqual((claim.status, len(claim.reason)), (Claim.Status.REJECTED, 500))

    def test_disposal_reason_takes_500_and_refuses_501(self):
        item = found_item(self.officer, days_ago=200)
        url = reverse('items:desk_dispose', args=[item.pk])
        self.assertContains(self.client.post(url, {'reason': TOO_LONG}), 'at most 500 characters')
        item.refresh_from_db()
        self.assertEqual(item.status, FoundItem.Status.IN_CUSTODY)
        self.client.post(url, {'reason': OK})
        item.refresh_from_db()
        self.assertEqual((item.status, len(item.disposal_reason)), (FoundItem.Status.DISPOSED, 500))

    def test_accounts_search_box_is_limited(self):
        self.assertContains(self.client.get(reverse('accounts:desk_accounts')), 'maxlength="500"')
