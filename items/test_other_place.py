"""
Tests for the "Other" place: the "Specify the location" box on reports and on Record found item.
Run:  python manage.py test items.test_other_place
"""
import shutil
import tempfile
from datetime import timedelta

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from core.testing import make_admin, make_staff, make_student, photo
from items.models import FoundItem, ItemReport, VerificationDetail
from matching.matcher import same_place, score_pair

MEDIA = tempfile.mkdtemp()
TODAY = timezone.localdate()


def report_data(**changes):
    data = {'type': 'lost', 'category': 'wallet', 'description': 'Black leather wallet',
            'date': TODAY.isoformat(), 'place': 'other', 'place_other': 'Outside Lecture Hall B'}
    data.update(changes)
    return data


def found_item(officer, place='other', place_other='', status=FoundItem.Status.IN_CUSTODY):
    item = FoundItem.objects.create(recorded_by=officer, category='wallet', description='Black leather wallet',
                                    place=place, place_other=place_other, date_found=TODAY,
                                    photo='found_items/x.png', status=status)
    VerificationDetail.objects.create(found_item=item, contents='Student ID')
    return item


class ReportOtherPlaceTests(TestCase):
    """Students and Staff: lost and found reports."""

    def setUp(self):
        self.student = make_student()
        self.client.force_login(self.student)

    def send(self, **changes):
        return self.client.post(reverse('items:report'), report_data(**changes))

    def test_the_report_page_has_the_specify_the_location_box(self):
        page = self.client.get(reverse('items:report'))
        self.assertContains(page, 'Specify the location')
        self.assertContains(page, 'data-other-place-for="id_place"')
        self.assertContains(page, 'name="place_other" maxlength="500"')

    def test_other_with_a_blank_location_is_refused(self):
        for blank in ('', '    '):
            response = self.send(place_other=blank)
            self.assertContains(response, 'Specify the location, e.g. Outside Lecture Hall B.')
        self.assertFalse(ItemReport.objects.exists())

    def test_other_with_a_typed_location_is_saved_separately_and_shown(self):
        self.assertRedirects(self.send(place_other='  Outside Lecture Hall B  '), reverse('core:my_page'))
        report = ItemReport.objects.get()
        self.assertEqual((report.place, report.place_other), ('other', 'Outside Lecture Hall B'))
        self.assertContains(self.client.get(reverse('core:my_page')), 'Outside Lecture Hall B')

    def test_the_typed_location_is_at_most_500_characters(self):
        self.assertContains(self.send(place_other='a' * 501), 'at most 500 characters')
        self.send(place_other='a' * 500)
        self.assertEqual(len(ItemReport.objects.get().place_other), 500)

    def test_a_regular_place_empties_the_box_before_saving(self):
        self.send(place='library', place_other='Outside Lecture Hall B')
        report = ItemReport.objects.get()
        self.assertEqual((report.place, report.place_other, report.place_label), ('library', '', 'Library'))

    def test_staff_can_use_other_too(self):
        self.client.force_login(make_staff())
        self.send(type='found', place_other='Room 4 in the Business School')
        self.assertEqual(ItemReport.objects.get().place_label, 'Room 4 in the Business School')

    def test_the_security_desk_sees_the_typed_location_in_reports(self):
        self.send()
        self.client.force_login(make_admin())
        self.assertContains(self.client.get(reverse('items:desk_reports')), 'Outside Lecture Hall B')


@override_settings(MEDIA_ROOT=MEDIA)
class RecordFoundItemOtherPlaceTests(TestCase):
    """The Security Desk's Record found item form."""

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.officer = make_admin()
        self.client.force_login(self.officer)

    def record(self, **changes):
        data = {'item-category': 'wallet', 'item-description': 'Black leather wallet', 'item-place': 'other',
                'item-place_other': 'Outside Lecture Hall B', 'item-date_found': TODAY.isoformat(),
                'item-photo': photo(), 'private-serial_no': '', 'private-marks': '', 'private-contents': 'Student ID'}
        data.update(changes)
        return self.client.post(reverse('items:desk_record_found'), data)

    def test_the_page_has_the_specify_the_location_box(self):
        page = self.client.get(reverse('items:desk_record_found'))
        self.assertContains(page, 'data-other-place-for="id_item-place"')
        self.assertContains(page, 'name="item-place_other" maxlength="500"')

    def test_other_with_a_blank_location_is_refused(self):
        self.assertContains(self.record(**{'item-place_other': '   '}), 'Specify the location')
        self.assertFalse(FoundItem.objects.exists())

    def test_other_with_a_typed_location_is_saved_and_shown_on_the_desk_pages(self):
        self.record()
        item = FoundItem.objects.get()
        self.assertEqual((item.place, item.place_other), ('other', 'Outside Lecture Hall B'))
        self.assertContains(self.client.get(reverse('items:desk_found_list')), 'Outside Lecture Hall B')
        self.assertContains(self.client.get(reverse('items:desk_found_detail', args=[item.pk])),
                            'Outside Lecture Hall B')

    def test_a_regular_place_empties_the_box_before_saving(self):
        self.record(**{'item-place': 'cafeteria'})
        self.assertEqual(FoundItem.objects.get().place_other, '')


class OlderRecordsAndSearchTests(TestCase):
    def setUp(self):
        self.officer = make_admin()
        self.student = make_student()

    def test_older_records_saved_as_other_without_a_location_still_show_other(self):
        item = found_item(self.officer, place_other='')
        self.assertEqual(item.place_label, 'Other')
        self.client.force_login(self.officer)
        self.assertContains(self.client.get(reverse('items:desk_found_detail', args=[item.pk])), 'Other')

    def test_search_finds_an_item_by_words_in_its_typed_location(self):
        wanted = found_item(self.officer, place_other='Outside Lecture Hall B')
        found_item(self.officer, place='library')
        found_item(self.officer, place_other='Lecture Hall B steps', status=FoundItem.Status.RETURNED)  # not at the desk
        self.client.force_login(self.student)
        page = self.client.get(reverse('search:search'), {'q': 'hall'})
        self.assertEqual(list(page.context['page'].object_list), [wanted])
        self.assertContains(page, 'Outside Lecture Hall B')


class OtherPlaceMatchingTests(TestCase):
    """Same-place points (20) for "Other" only when the typed locations are the same."""

    def setUp(self):
        self.officer = make_admin()
        self.student = make_student()

    def pair(self, report_place, report_other, item_place, item_other):
        report = ItemReport(user=self.student, type='lost', category='wallet', description='Blue umbrella',
                            date=TODAY - timedelta(days=40), place=report_place, place_other=report_other)
        item = FoundItem(recorded_by=self.officer, category='wallet', description='Black bag',
                         place=item_place, place_other=item_other, date_found=TODAY)
        return report, item

    def test_the_same_typed_location_matches_after_trimming_spaces_and_ignoring_capitals(self):
        report, item = self.pair('other', '  outside LECTURE hall b ', 'other', 'Outside Lecture Hall B')
        self.assertTrue(same_place(report, item))
        self.assertEqual(score_pair(report, item), 40 + 20)      # category + place (dates too far, no shared words)

    def test_different_typed_locations_get_no_place_points(self):
        report, item = self.pair('other', 'Outside Lecture Hall B', 'other', 'Outside Lecture Hall C')
        self.assertFalse(same_place(report, item))
        self.assertEqual(score_pair(report, item), 40)

    def test_choosing_other_on_both_with_no_typed_location_is_not_a_match(self):
        report, item = self.pair('other', '', 'other', '')
        self.assertFalse(same_place(report, item))

    def test_regular_places_still_match_as_before(self):
        self.assertTrue(same_place(*self.pair('library', '', 'library', '')))
        self.assertFalse(same_place(*self.pair('library', '', 'cafeteria', '')))
        self.assertFalse(same_place(*self.pair('other', 'Library', 'library', '')))

    def test_a_saved_found_item_ranks_the_report_with_the_same_typed_location_first(self):
        from matching.models import Match
        same = ItemReport.objects.create(user=self.student, type='lost', category='wallet',
                                         description='Black leather wallet', date=TODAY,
                                         place='other', place_other='outside lecture hall b')
        other = ItemReport.objects.create(user=make_staff(), type='lost', category='wallet',
                                          description='Black leather wallet', date=TODAY,
                                          place='other', place_other='Parking lot C')
        from matching.matcher import match_found_item
        match_found_item(found_item(self.officer, place_other='Outside Lecture Hall B'))
        scores = {m.report_id: m.score for m in Match.objects.all()}
        self.assertEqual(scores[same.pk] - scores[other.pk], 20)
