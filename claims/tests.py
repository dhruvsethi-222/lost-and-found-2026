"""
Tests for claims and the Admin's verification decision.
Each test name starts with the requirement it proves.  Run:  python manage.py test claims
"""
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from claims.models import Claim
from core.testing import make_admin, make_staff, make_student
from items.models import FoundItem, ItemReport, VerificationDetail
from matching.matcher import match_found_item

TODAY = timezone.localdate()


def found(officer, status=FoundItem.Status.IN_CUSTODY):
    item = FoundItem.objects.create(recorded_by=officer, category='wallet', description='Black leather wallet',
                                    place='library', date_found=TODAY, photo='found_items/x.png', status=status)
    VerificationDetail.objects.create(found_item=item, contents='SECRET student ID of Jane', marks='Torn corner')
    return item


class SubmitClaimTests(TestCase):
    def setUp(self):
        self.officer = make_admin()
        self.student = make_student()
        self.item = found(self.officer)
        self.client.force_login(self.student)

    def claim(self, item=None, answers='Brown leather inside, my student ID is in it'):
        return self.client.post(reverse('claims:new', args=[(item or self.item).pk]), {'answers': answers}, follow=True)

    def test_search_results_have_a_claim_button(self):
        page = self.client.get(reverse('search:search'))
        self.assertContains(page, reverse('claims:new', args=[self.item.pk]))

    def test_ST_P6_student_submits_a_claim_and_it_is_stored(self):
        response = self.claim()
        claim = Claim.objects.get()                                           # ST-S3
        self.assertEqual((claim.user, claim.found_item, claim.status), (self.student, self.item, 'pending'))
        self.assertIn('student ID', claim.answers)                            # ST-I3
        self.assertContains(response, 'Your claim was sent')

    def test_ST_O4_student_sees_the_claim_status_on_my_page(self):
        self.claim()
        page = self.client.get(reverse('core:my_page'))
        self.assertContains(page, 'My claims')
        self.assertContains(page, 'Under review')

    def test_SF_P6_staff_submits_a_claim_and_sees_its_status(self):
        staff = make_staff()
        self.client.force_login(staff)
        self.claim(answers='It has my office key inside')
        self.assertEqual(Claim.objects.get().user, staff)                     # SF-S3
        self.assertContains(self.client.get(reverse('core:my_page')), 'Under review')     # SF-O4

    def test_ST_I3_a_claim_needs_an_answer(self):
        self.claim(answers='')
        self.assertFalse(Claim.objects.exists())

    def test_the_claim_page_shows_public_details_only(self):
        page = self.client.get(reverse('claims:new', args=[self.item.pk]))
        self.assertContains(page, 'Black leather wallet')
        self.assertNotContains(page, 'SECRET')                                # NFR-02
        self.assertNotContains(page, 'Torn corner')

    def test_the_same_person_cannot_claim_an_item_twice(self):
        self.claim()
        response = self.claim()
        self.assertContains(response, 'already claimed this item')
        self.assertEqual(Claim.objects.count(), 1)
        self.assertContains(self.client.get(reverse('search:search')), 'Claimed by you')

    def test_an_item_that_left_the_desk_cannot_be_claimed(self):
        returned = found(self.officer, status=FoundItem.Status.RETURNED)
        response = self.client.post(reverse('claims:new', args=[returned.pk]), {'answers': 'Mine'})
        self.assertEqual(response.status_code, 404)

    def test_NFR01_admin_and_logged_out_visitors_cannot_claim(self):
        self.client.force_login(self.officer)
        self.assertEqual(self.client.get(reverse('claims:new', args=[self.item.pk])).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(reverse('claims:new', args=[self.item.pk])).status_code, 302)

    def test_my_page_shows_only_my_own_claims(self):
        other = make_student(email='brian@strathmore.edu', admission_no='227035')
        Claim.objects.create(found_item=self.item, user=other, answers='Brian says it has a red zip')
        self.assertNotContains(self.client.get(reverse('core:my_page')), 'red zip')


class VerifyClaimTests(TestCase):
    def setUp(self):
        self.officer = make_admin()
        self.student = make_student()
        self.item = found(self.officer)
        self.claim = Claim.objects.create(found_item=self.item, user=self.student,
                                          answers='My student ID is inside')
        self.client.force_login(self.officer)

    def decide(self, decision, reason='Details match', claim=None):
        return self.client.post(reverse('claims:desk_verify', args=[(claim or self.claim).pk]),
                                {'decision': decision, 'reason': reason}, follow=True)

    def test_AD_O1_dashboard_and_list_show_the_pending_claim(self):
        self.assertEqual(self.client.get(reverse('core:desk')).context['pending_claims'], 1)
        self.assertContains(self.client.get(reverse('claims:desk_list')), self.student.name)

    def test_AD_O3_admin_sees_the_claim_beside_the_private_details(self):
        page = self.client.get(reverse('claims:desk_verify', args=[self.claim.pk]))      # AD-P4
        self.assertContains(page, 'My student ID is inside')
        self.assertContains(page, 'SECRET student ID of Jane')

    def test_AD_O2_the_claim_page_shows_the_claimants_ranked_match(self):
        ItemReport.objects.create(user=self.student, type='lost', category='wallet',
                                  description='Black leather wallet', place='library', date=TODAY)
        match_found_item(self.item)
        page = self.client.get(reverse('claims:desk_verify', args=[self.claim.pk]))
        self.assertContains(page, 'score 95 out of 100, rank 1')

    def test_NFR02_students_and_staff_cannot_open_the_verification_pages(self):
        for person in (self.student, make_staff()):
            self.client.force_login(person)
            self.assertEqual(self.client.get(reverse('claims:desk_verify', args=[self.claim.pk])).status_code, 403)
            self.assertEqual(self.client.get(reverse('claims:desk_list')).status_code, 403)

    def test_AD_P5_approve_stores_the_decision_and_the_item_becomes_claimed(self):
        self.decide('approve')
        self.claim.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual((self.claim.status, self.claim.decided_by, self.claim.reason),       # AD-S3
                         ('approved', self.officer, 'Details match'))
        self.assertIsNotNone(self.claim.decided_at)                                           # NFR-04
        self.assertEqual(self.item.status, FoundItem.Status.CLAIMED)

    def test_EM_P3_the_claimant_is_emailed_the_decision_and_when_to_collect(self):
        self.decide('approve')
        email = mail.outbox[0]
        self.assertEqual(email.to, [self.student.email])
        self.assertIn('Decision: Approved', email.body)
        self.assertIn('Collect the item from the security desk', email.body)
        self.assertNotIn('SECRET', email.body)

    def test_an_approved_item_leaves_the_search_and_my_page_says_when_to_collect(self):
        self.decide('approve')
        self.client.force_login(self.student)
        self.assertNotContains(self.client.get(reverse('search:search')), 'Black leather wallet')
        self.assertContains(self.client.get(reverse('core:my_page')), 'Collect it from the security desk')

    def test_AD_P6_reject_stores_the_reason_and_the_item_stays_at_the_desk(self):
        self.decide('reject', reason='The contents described are wrong')
        self.claim.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual((self.claim.status, self.claim.decided_by), ('rejected', self.officer))
        self.assertEqual(self.item.status, FoundItem.Status.IN_CUSTODY)
        self.assertIn('Decision: Rejected', mail.outbox[0].body)
        self.client.force_login(self.student)
        self.assertContains(self.client.get(reverse('core:my_page')), 'The contents described are wrong')

    def test_AD_P7_request_more_evidence_and_the_claimant_answers(self):
        self.decide('more', reason='What colour is the lining?')
        self.claim.refresh_from_db()
        self.assertEqual(self.claim.status, 'more_evidence')
        self.assertIn('add the details the officer asked for', mail.outbox[0].body)

        self.client.force_login(self.student)
        self.assertContains(self.client.get(reverse('core:my_page')), 'What colour is the lining?')
        self.client.post(reverse('claims:add_details', args=[self.claim.pk]), {'details': 'The lining is red'})
        self.claim.refresh_from_db()
        self.assertEqual(self.claim.status, 'pending')                        # back with the Admin
        for text in ('My student ID is inside', 'What colour is the lining?', 'The lining is red'):
            self.assertIn(text, self.claim.answers)                           # nothing is lost

    def test_AD_I4_a_decision_needs_a_reason(self):
        response = self.decide('approve', reason='')
        self.claim.refresh_from_db()
        self.assertEqual(self.claim.status, 'pending')
        self.assertContains(response, 'This field is required')

    def test_NFR04_a_final_decision_cannot_be_changed(self):
        self.decide('reject', reason='Wrong contents')
        response = self.decide('approve', reason='Changed my mind')
        self.claim.refresh_from_db()
        self.assertEqual((self.claim.status, self.claim.reason), ('rejected', 'Wrong contents'))
        self.assertContains(response, 'cannot be changed')
        self.assertNotContains(response, 'name="decision"')                   # the buttons are gone

    def test_only_one_claim_can_be_approved_for_an_item(self):
        other = make_student(email='brian@strathmore.edu', admission_no='227035')
        second = Claim.objects.create(found_item=self.item, user=other, answers='It is mine')
        self.decide('approve')
        second.refresh_from_db()
        self.assertEqual(second.status, 'closed')                             # closed when the first was approved
        self.assertEqual(sorted(email.to[0] for email in mail.outbox), sorted([self.student.email, other.email]))
        self.decide('approve', claim=second)
        self.assertEqual(Claim.objects.filter(found_item=self.item, status='approved').count(), 1)

    def test_one_member_cannot_answer_for_another_members_claim(self):
        self.decide('more', reason='What colour is the lining?')
        other = make_student(email='brian@strathmore.edu', admission_no='227035')
        self.client.force_login(other)
        response = self.client.post(reverse('claims:add_details', args=[self.claim.pk]), {'details': 'Red'})
        self.assertEqual(response.status_code, 404)

    def test_an_unknown_button_changes_nothing(self):
        self.decide('delete')
        self.claim.refresh_from_db()
        self.assertEqual(self.claim.status, 'pending')
