"""
Tests for matching and the match alert email.
Each test name starts with the requirement it proves.  Run:  python manage.py test matching
"""
import shutil
import tempfile
import time
from datetime import timedelta

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from core.testing import make_admin, make_staff, make_student, photo
from items.models import FoundItem, ItemReport, VerificationDetail
from matching.matcher import keywords, match_lost_report, score_pair
from matching.models import Match

MEDIA = tempfile.mkdtemp()      # test photos go to a throw-away folder
TODAY = timezone.localdate()


def lost(user, category='wallet', description='Black leather wallet', place='library', date=None):
    return ItemReport.objects.create(user=user, type='lost', category=category, description=description,
                                     place=place, date=date or TODAY)


def found(officer, category='wallet', description='Black leather wallet', place='library', date=None, **private):
    item = FoundItem.objects.create(recorded_by=officer, category=category, description=description, place=place,
                                    date_found=date or TODAY, photo='found_items/x.png')
    VerificationDetail.objects.create(found_item=item, contents=private.get('contents', 'Student ID card'))
    return item


class ScoreTests(TestCase):
    def setUp(self):
        self.student = make_student()
        self.officer = make_admin()

    def test_SY_P2_keywords_are_the_useful_words_of_a_description(self):
        self.assertEqual(keywords('The black, leather wallet.'), ['black', 'leather', 'wallet'])

    def test_SY_P2_same_category_place_date_and_words_scores_highest(self):
        score = score_pair(lost(self.student), found(self.officer))
        self.assertEqual(score, 95)             # 40 category + 20 place + 20 date + 15 for three shared words

    def test_SY_P2_a_different_category_is_never_a_match(self):
        self.assertEqual(score_pair(lost(self.student), found(self.officer, category='phone')), 0)

    def test_SY_P2_date_further_apart_scores_lower(self):
        report = lost(self.student, description='x')
        same_day = score_pair(report, found(self.officer, description='y'))
        week_later = score_pair(report, found(self.officer, description='y', date=TODAY - timedelta(days=6)))
        self.assertEqual((same_day, week_later), (80, 70))

    def test_SY_P2_same_category_alone_is_not_saved_as_a_match(self):
        found(self.officer, description='Brown purse', place='cafeteria', date=TODAY - timedelta(days=60))
        self.assertEqual(match_lost_report(lost(self.student)), 0)
        self.assertFalse(Match.objects.exists())
        self.assertEqual(len(mail.outbox), 0)   # no match, no email


@override_settings(MEDIA_ROOT=MEDIA)
class MatchingFlowTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.student = make_student()
        self.officer = make_admin()

    def report_lost(self, **changes):
        data = {'type': 'lost', 'category': 'wallet', 'description': 'Black leather wallet',
                'date': TODAY.isoformat(), 'place': 'library'}
        data.update(changes)
        return self.client.post(reverse('items:report'), data, follow=True)

    def record_found(self, **changes):
        data = {'item-category': 'wallet', 'item-description': 'Black leather wallet', 'item-place': 'library',
                'item-date_found': TODAY.isoformat(), 'item-photo': photo(),
                'private-contents': 'SECRET student ID of Jane'}
        data.update(changes)
        return self.client.post(reverse('items:desk_record_found'), data, follow=True)

    def test_SY_I1_a_new_lost_report_is_matched_and_stored(self):
        item = found(self.officer)
        self.client.force_login(self.student)
        response = self.report_lost()
        match = Match.objects.get()                                           # SY-S1
        self.assertEqual((match.report.user, match.found_item, match.rank), (self.student, item, 1))
        self.assertContains(response, 'we found a possible match')

    def test_ST_O3_student_gets_a_match_alert_email_without_private_details(self):
        found(self.officer, contents='SECRET student ID of Jane')
        self.client.force_login(self.student)
        self.report_lost()
        self.assertEqual(len(mail.outbox), 1)                                 # SY-O2 / EM-P2
        email = mail.outbox[0]
        self.assertEqual(email.to, [self.student.email])
        self.assertIn('may match the wallet or purse you reported lost', email.body)
        self.assertNotIn('SECRET', email.body)                                # NFR-02

    def test_SY_I1_a_new_found_item_is_matched_with_waiting_lost_reports(self):
        report = lost(self.student)
        self.client.force_login(self.officer)
        response = self.record_found()
        match = Match.objects.get()
        self.assertEqual(match.report, report)
        self.assertContains(response, 'Lost reports that match: 1')
        self.assertEqual(mail.outbox[0].to, [self.student.email])             # the owner is told

    def test_SF_O3_staff_gets_a_match_alert_too(self):
        staff = make_staff()
        lost(staff, category='laptop', description='Grey laptop', place='staff_offices')
        self.client.force_login(self.officer)
        self.record_found(**{'item-category': 'laptop', 'item-description': 'Grey laptop', 'item-place': 'staff_offices'})
        self.assertEqual(mail.outbox[0].to, [staff.email])

    def test_NFR03_same_category_place_and_date_is_ranked_first(self):
        other = make_student(email='brian@students.campus.ac.ke', admission_no='227035')
        weaker = lost(other, description='Wallet', place='cafeteria', date=TODAY - timedelta(days=2))
        best = lost(self.student, description='Wallet')                       # same category, place and date
        self.client.force_login(self.officer)
        self.record_found(**{'item-description': 'Wallet'})
        ranks = {match.report: match.rank for match in Match.objects.all()}   # SY-P3
        self.assertEqual((ranks[best], ranks[weaker]), (1, 2))

    def test_AD_O2_admin_sees_the_ranked_matches(self):
        lost(self.student)
        self.client.force_login(self.officer)
        self.record_found()
        item = FoundItem.objects.get()
        page = self.client.get(reverse('items:desk_found_detail', args=[item.pk]))        # AD-P3
        self.assertContains(page, 'Ranked matches')
        self.assertContains(page, '95 / 100')
        self.assertContains(self.client.get(reverse('items:desk_matches')), self.student.name)
        self.assertEqual(self.client.get(reverse('core:desk')).context['ranked_matches'], 1)

    def test_ST_O3_my_page_shows_the_match_with_a_claim_button_and_no_private_details(self):
        item = found(self.officer, contents='SECRET student ID of Jane')
        self.client.force_login(self.student)
        self.report_lost()
        page = self.client.get(reverse('core:my_page'))
        self.assertContains(page, 'A match was found for your lost wallet or purse')
        self.assertContains(page, reverse('claims:new', args=[item.pk]))
        self.assertContains(page, 'Matched')                                  # the report's status
        self.assertNotContains(page, 'SECRET')

    def test_NFR01_students_cannot_open_the_ranked_matches(self):
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(reverse('items:desk_matches')).status_code, 403)

    def test_SF_O5_staff_gets_a_hand_in_confirmation_when_the_admin_records_the_office_item(self):
        staff = make_staff()
        report = ItemReport.objects.create(user=staff, type='found', category='bottle',
                                           description='Green metal bottle', place='staff_offices', date=TODAY)
        self.client.force_login(self.officer)
        self.record_found(**{'item-category': 'bottle', 'item-description': 'Green metal bottle',
                             'item-place': 'staff_offices', 'item-handed_in_report': report.pk})
        self.assertEqual(FoundItem.objects.get().handed_in_report, report)
        self.assertEqual(mail.outbox[0].to, [staff.email])
        self.assertIn('security desk has received the bottle or flask', mail.outbox[0].body)
        self.client.force_login(staff)
        self.assertContains(self.client.get(reverse('core:my_page')), 'Handed in')        # SF-R1

    def test_a_found_report_that_is_not_handed_in_yet_says_so(self):
        ItemReport.objects.create(user=self.student, type='found', category='umbrella',
                                  description='Blue umbrella', place='cafeteria', date=TODAY)
        self.client.force_login(self.student)
        self.assertContains(self.client.get(reverse('core:my_page')), 'Not yet at the security desk')


class MatchingSpeedTests(TestCase):
    def test_NFR05_matching_and_the_ranked_list_with_1000_items_take_under_3_seconds(self):
        officer = make_admin()
        student = make_student()
        FoundItem.objects.bulk_create([
            FoundItem(recorded_by=officer, category='wallet', description=f'Black wallet number {number}',
                      place='library', date_found=TODAY, photo='found_items/x.png')
            for number in range(1000)])

        start = time.perf_counter()
        saved = match_lost_report(lost(student))
        matching_seconds = time.perf_counter() - start
        self.assertEqual(saved, 1000)
        self.assertLess(matching_seconds, 3)

        self.client.force_login(officer)
        start = time.perf_counter()
        response = self.client.get(reverse('items:desk_matches'))
        page_seconds = time.perf_counter() - start
        self.assertEqual(len(response.context['page'].object_list), 15)      # one page of 15
        self.assertLess(page_seconds, 3)
