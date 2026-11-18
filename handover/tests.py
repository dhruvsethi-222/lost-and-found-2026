"""
Tests for the hand-over.
Each test name starts with the requirement it proves.  Run:  python manage.py test handover
"""
import shutil
import tempfile

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from claims.models import Claim
from core.testing import make_admin, make_staff, make_student, photo
from handover.models import HandOver
from items.models import FoundItem, VerificationDetail


def approved_claim(officer, owner):
    """An item at the desk with an approved claim, as Dev 2 leaves it."""
    item = FoundItem.objects.create(recorded_by=officer, category='wallet', description='Black leather wallet',
                                    place='library', date_found=timezone.localdate(), photo='found_items/x.png',
                                    status=FoundItem.Status.CLAIMED)
    VerificationDetail.objects.create(found_item=item, contents='Student ID card')
    return Claim.objects.create(found_item=item, user=owner, answers='My ID is inside', status='approved',
                                decided_by=officer, reason='Details match', decided_at=timezone.now())


class HandOverTests(TestCase):
    def setUp(self):
        self.officer = make_admin()
        self.student = make_student()                  # admission number 227034
        self.claim = approved_claim(self.officer, self.student)
        self.client.force_login(self.officer)

    def hand_over(self, collector_id='227034', claim=None):
        return self.client.post(reverse('handover:record', args=[(claim or self.claim).pk]),
                                {'collector_id': collector_id}, follow=True)

    def test_the_approved_claim_is_waiting_for_collection(self):
        page = self.client.get(reverse('handover:list'))
        self.assertContains(page, 'Jane Wanjiru')
        self.assertContains(page, reverse('handover:record', args=[self.claim.pk]))

    def test_AD_P8_record_the_hand_over_and_the_item_becomes_returned(self):
        response = self.hand_over()
        record = HandOver.objects.get()                                      # AD-S4
        self.assertEqual((record.claim, record.released_by, record.collector_id),
                         (self.claim, self.officer, '227034'))               # AD-I5
        self.assertIsNotNone(record.date)                                    # NFR-04: the date
        self.claim.found_item.refresh_from_db()
        self.assertEqual(self.claim.found_item.status, FoundItem.Status.RETURNED)   # AD-S5
        self.assertContains(response, 'The item is now Returned')

    def test_AD_I5_only_the_claimants_own_id_is_accepted(self):
        response = self.hand_over(collector_id='999999')
        self.assertContains(response, "does not match the claimant&#x27;s ID")
        self.assertFalse(HandOver.objects.exists())
        self.claim.found_item.refresh_from_db()
        self.assertEqual(self.claim.found_item.status, FoundItem.Status.CLAIMED)

    def test_staff_ids_are_matched_without_caring_about_capital_letters(self):
        staff = make_staff()                                                 # staff ID S1043
        claim = approved_claim(self.officer, staff)
        self.hand_over(collector_id='s1043', claim=claim)
        self.assertEqual(HandOver.objects.get().collector_id, 'S1043')

    def test_the_owner_gets_a_receipt_email(self):
        self.hand_over()
        email = mail.outbox[0]
        self.assertEqual(email.to, [self.student.email])
        self.assertIn('was collected from the security desk', email.body)
        self.assertIn('Grace Achieng', email.body)

    def test_my_page_shows_the_claim_as_collected(self):
        self.hand_over()
        self.client.force_login(self.student)
        self.assertContains(self.client.get(reverse('core:my_page')), 'You collected it on')

    def test_no_item_is_released_without_an_approved_claim(self):
        for status in ('pending', 'more_evidence', 'rejected', 'closed'):
            self.claim.status = status
            self.claim.save()
            self.hand_over()
            self.assertFalse(HandOver.objects.exists(), status)

    def test_NFR04_a_hand_over_is_recorded_once_and_cannot_be_changed(self):
        self.hand_over()
        response = self.hand_over(collector_id='227034')
        self.assertContains(response, 'already been handed over')
        self.assertEqual(HandOver.objects.count(), 1)
        self.client.force_login(self.officer)
        record = HandOver.objects.get()
        admin_url = reverse('admin:handover_handover_change', args=[record.pk])
        self.officer.is_staff = self.officer.is_superuser = True     # even the system owner cannot change it
        self.officer.save()
        self.client.post(admin_url, {'collector_id': '000000'})
        record.refresh_from_db()
        self.assertEqual(record.collector_id, '227034')

    def test_NFR07_the_hand_over_and_the_returned_status_are_saved_together(self):
        # Force the second step (saving the item) to fail: the hand-over must not be saved either.
        original_save = FoundItem.save

        def failing_save(item, *args, **kwargs):
            if item.status == FoundItem.Status.RETURNED:
                raise RuntimeError('server fault')
            return original_save(item, *args, **kwargs)

        FoundItem.save = failing_save
        try:
            with self.assertRaises(RuntimeError):
                self.hand_over()
        finally:
            FoundItem.save = original_save
        self.assertFalse(HandOver.objects.exists())

    def test_NFR01_students_and_staff_cannot_record_a_hand_over(self):
        for person in (self.student, make_staff()):
            self.client.force_login(person)
            self.assertEqual(self.client.get(reverse('handover:list')).status_code, 403)
            self.assertEqual(self.client.get(reverse('handover:record', args=[self.claim.pk])).status_code, 403)

    def test_the_verify_page_links_to_the_hand_over(self):
        page = self.client.get(reverse('claims:desk_verify', args=[self.claim.pk]))
        self.assertContains(page, 'Record hand-over')
        self.hand_over()
        page = self.client.get(reverse('claims:desk_verify', args=[self.claim.pk]))
        self.assertContains(page, 'ID 227034 checked')


MEDIA = tempfile.mkdtemp()      # test photos go to a throw-away folder


@override_settings(MEDIA_ROOT=MEDIA)
class WholeJourneyTest(TestCase):
    """
    Integration test (Chapter 3): one lost wallet goes through the whole system, using the real pages:
    report -> record found item -> match -> claim -> verify -> approve -> hand-over.
    """

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA, ignore_errors=True)
        super().tearDownClass()

    def test_a_lost_wallet_goes_from_report_to_hand_over(self):
        officer = make_admin()
        jane = make_student()
        today = timezone.localdate().isoformat()

        # Jane reports her lost wallet.
        self.client.force_login(jane)
        self.client.post(reverse('items:report'), {'type': 'lost', 'category': 'wallet', 'place': 'library',
                                                   'description': 'Black leather wallet', 'date': today})

        # The Admin records the wallet that was handed in. It matches Jane's report and she is emailed.
        self.client.force_login(officer)
        self.client.post(reverse('items:desk_record_found'), {
            'item-category': 'wallet', 'item-description': 'Black leather wallet', 'item-place': 'library',
            'item-date_found': today, 'item-photo': photo(), 'private-contents': 'Student ID of Jane'})
        item = FoundItem.objects.get()
        self.assertEqual(item.matches.get().report.user, jane)
        self.assertIn('possible match', mail.outbox[-1].subject)

        # Jane claims it.
        self.client.force_login(jane)
        self.client.post(reverse('claims:new', args=[item.pk]), {'answers': 'My student ID is inside'})
        claim = Claim.objects.get()

        # The Admin approves the claim, then hands the wallet over.
        self.client.force_login(officer)
        self.client.post(reverse('claims:desk_verify', args=[claim.pk]), {'decision': 'approve', 'reason': 'ID matches'})
        self.client.post(reverse('handover:record', args=[claim.pk]), {'collector_id': '227034'})

        item.refresh_from_db()
        claim.refresh_from_db()
        self.assertEqual((claim.status, item.status), ('approved', FoundItem.Status.RETURNED))
        self.assertEqual(claim.hand_over.released_by, officer)
        self.assertEqual([email.subject for email in mail.outbox],
                         ['A possible match for your lost item', 'Your claim: approved', 'You have collected your item'])
