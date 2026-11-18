"""Tests for reporting items and the Admin intake of found items."""
import shutil
import tempfile
from datetime import timedelta

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from core.testing import make_admin, make_staff, make_student, photo
from items.models import FoundItem, ItemReport, VerificationDetail

MEDIA = tempfile.mkdtemp()      # test photos go to a throw-away folder


def report_data(**changes):
    data = {'type': 'lost', 'category': 'wallet', 'description': 'Black leather wallet',
            'date': timezone.localdate().isoformat(), 'place': 'library'}
    data.update(changes)
    return data


class ReportItemTests(TestCase):
    def setUp(self):
        self.student = make_student()
        self.client.force_login(self.student)

    def test_ST_P3_student_reports_a_lost_item(self):
        response = self.client.post(reverse('items:report'), report_data())
        self.assertRedirects(response, reverse('core:my_page'))
        report = ItemReport.objects.get()                                     # ST-S2
        self.assertEqual((report.user, report.type, report.category), (self.student, 'lost', 'wallet'))

    def test_ST_P4_student_reports_a_found_item(self):
        self.client.post(reverse('items:report'), report_data(type='found', category='umbrella'))
        self.assertEqual(ItemReport.objects.get().kind_label, 'Found')

    def test_SF_P3_staff_reports_a_lost_item_and_sees_it_on_my_page(self):
        staff = make_staff()
        self.client.force_login(staff)
        self.client.post(reverse('items:report'), report_data(category='laptop', description='Grey laptop'))
        report = ItemReport.objects.get()                                     # SF-S2
        self.assertEqual((report.user, report.type), (staff, 'lost'))
        self.assertContains(self.client.get(reverse('core:my_page')), 'Grey laptop')     # SF-R1

    def test_SF_P4_staff_logs_an_office_found_item(self):
        self.client.force_login(make_staff())
        page = self.client.get(reverse('items:report'))
        self.assertContains(page, 'Found in my office')
        self.client.post(reverse('items:report'), report_data(type='found', place='staff_offices'))
        self.assertEqual(ItemReport.objects.get().kind_label, 'Office item')

    def test_NFR03_future_date_is_rejected(self):
        tomorrow = (timezone.localdate() + timedelta(days=1)).isoformat()
        response = self.client.post(reverse('items:report'), report_data(date=tomorrow))
        self.assertContains(response, 'cannot be in the future')
        self.assertFalse(ItemReport.objects.exists())

    def test_NFR03_missing_field_or_unknown_category_is_rejected(self):
        self.client.post(reverse('items:report'), report_data(description=''))
        self.client.post(reverse('items:report'), report_data(category='spaceship'))
        self.assertFalse(ItemReport.objects.exists())

    def test_my_page_shows_only_my_own_reports(self):
        other = make_student(email='brian@students.campus.ac.ke', admission_no='227035')
        ItemReport.objects.create(user=other, **{**report_data(description='Brian blue bag'), 'date': timezone.localdate()})
        self.client.post(reverse('items:report'), report_data())
        page = self.client.get(reverse('core:my_page'))
        self.assertContains(page, 'Black leather wallet')
        self.assertNotContains(page, 'Brian blue bag')

    def test_admin_does_not_use_the_student_report_page(self):
        self.client.force_login(make_admin())
        self.assertEqual(self.client.get(reverse('items:report')).status_code, 403)


@override_settings(MEDIA_ROOT=MEDIA)
class RecordFoundItemTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.officer = make_admin()
        self.client.force_login(self.officer)

    def post(self, **private):
        data = {'item-category': 'wallet', 'item-description': 'Black leather wallet', 'item-place': 'library',
                'item-date_found': timezone.localdate().isoformat(), 'item-photo': photo(),
                'private-serial_no': '', 'private-marks': '', 'private-contents': 'Student ID'}
        data.update({f'private-{k}': v for k, v in private.items()})
        return self.client.post(reverse('items:desk_record_found'), data)

    def test_AD_P2_admin_records_found_item_with_private_details(self):
        response = self.post()
        item = FoundItem.objects.get()                                        # AD-S1
        self.assertRedirects(response, reverse('items:desk_found_detail', args=[item.pk]))
        self.assertEqual((item.recorded_by, item.status), (self.officer, FoundItem.Status.IN_CUSTODY))
        self.assertEqual(item.verification_detail.contents, 'Student ID')     # AD-S2
        self.assertTrue(item.photo.name.startswith('found_items/'))

    def test_AD_I3_at_least_one_private_detail_is_needed(self):
        response = self.post(contents='')
        self.assertContains(response, 'Enter at least one private detail')
        self.assertFalse(FoundItem.objects.exists())                         # nothing half-saved

    def test_NFR03_a_file_that_is_not_an_image_is_rejected(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        data = {'item-category': 'wallet', 'item-description': 'x', 'item-place': 'library',
                'item-date_found': timezone.localdate().isoformat(),
                'item-photo': SimpleUploadedFile('virus.png', b'not really an image', content_type='image/png'),
                'private-contents': 'ID'}
        response = self.client.post(reverse('items:desk_record_found'), data)
        self.assertContains(response, 'Upload a valid image')
        self.assertFalse(FoundItem.objects.exists())

    def test_AD_O_admin_sees_private_details_on_the_item_page(self):
        self.post(serial_no='SN-778')
        page = self.client.get(reverse('items:desk_found_detail', args=[FoundItem.objects.get().pk]))
        self.assertContains(page, 'SN-778')

    def test_composition_private_details_are_deleted_with_the_item(self):
        self.post()
        FoundItem.objects.get().delete()
        self.assertFalse(VerificationDetail.objects.exists())

    def test_desk_lists_and_dashboard_count_the_item(self):
        self.post()
        self.assertContains(self.client.get(reverse('items:desk_found_list')), 'Black leather wallet')
        self.assertEqual(self.client.get(reverse('core:desk')).context['in_custody'], 1)
        self.assertEqual(self.client.get(reverse('items:desk_reports')).status_code, 200)

    def test_NFR01_students_cannot_record_found_items(self):
        self.client.force_login(make_student())
        self.assertEqual(self.post().status_code, 403)
        self.assertFalse(FoundItem.objects.exists())


class DisposalTests(TestCase):
    """AD-P9, AD-S5 and NFR-02: items past the retention period (90 days) are disposed of."""

    def setUp(self):
        self.officer = make_admin()
        self.client.force_login(self.officer)

    def item(self, days_ago, status=FoundItem.Status.IN_CUSTODY):
        item = FoundItem.objects.create(recorded_by=self.officer, category='umbrella', description='Blue umbrella',
                                        place='cafeteria', photo='found_items/x.png', status=status,
                                        date_found=timezone.localdate() - timedelta(days=days_ago))
        VerificationDetail.objects.create(found_item=item, marks='SECRET broken handle')
        return item

    def dispose(self, item, reason='Donated to the campus charity drive'):
        return self.client.post(reverse('items:desk_dispose', args=[item.pk]), {'reason': reason}, follow=True)

    def test_NFR02_an_item_past_its_retention_period_appears_in_the_expired_list(self):
        old = self.item(days_ago=91)
        soon = self.item(days_ago=80)              # expires in 10 days
        fresh = self.item(days_ago=5)
        page = self.client.get(reverse('items:desk_expired'))
        self.assertEqual(list(page.context['expired']), [old])
        self.assertEqual(list(page.context['expiring_soon']), [soon])
        self.assertNotIn(fresh, page.context['expiring_soon'])
        self.assertEqual(self.client.get(reverse('core:desk')).context['expired_items'], 1)

    def test_the_last_day_of_the_retention_period_is_not_expired_yet(self):
        self.assertFalse(self.item(days_ago=90).is_expired)
        self.assertTrue(self.item(days_ago=91).is_expired)

    def test_AD_P9_dispose_of_an_expired_item_with_officer_date_and_reason(self):
        item = self.item(days_ago=100)
        self.dispose(item)
        item.refresh_from_db()
        self.assertEqual(item.status, FoundItem.Status.DISPOSED)                       # AD-S5
        self.assertEqual((item.disposed_by, item.disposal_reason),
                         (self.officer, 'Donated to the campus charity drive'))      # NFR-04
        self.assertIsNotNone(item.disposed_at)

    def test_NFR02_private_details_are_deleted_when_an_item_is_disposed_of(self):
        item = self.item(days_ago=100)
        self.dispose(item)
        self.assertFalse(VerificationDetail.objects.filter(found_item=item).exists())
        page = self.client.get(reverse('items:desk_found_detail', args=[item.pk]))
        self.assertContains(page, 'private details were deleted')
        self.assertNotContains(page, 'SECRET')

    def test_an_item_that_has_not_expired_cannot_be_disposed_of(self):
        item = self.item(days_ago=10)
        self.dispose(item)
        item.refresh_from_db()
        self.assertEqual(item.status, FoundItem.Status.IN_CUSTODY)

    def test_only_items_in_custody_can_be_disposed_of(self):
        item = self.item(days_ago=200, status=FoundItem.Status.CLAIMED)     # the owner is coming to collect it
        self.dispose(item)
        item.refresh_from_db()
        self.assertEqual(item.status, FoundItem.Status.CLAIMED)

    def test_an_item_with_open_claims_cannot_be_disposed_of(self):
        from claims.models import Claim
        item = self.item(days_ago=100)
        Claim.objects.create(found_item=item, user=make_student(), answers='Mine')
        response = self.dispose(item)
        self.assertContains(response, 'Decide them before disposing')
        item.refresh_from_db()
        self.assertEqual(item.status, FoundItem.Status.IN_CUSTODY)

    def test_NFR04_a_disposal_needs_a_reason(self):
        item = self.item(days_ago=100)
        self.dispose(item, reason='')
        item.refresh_from_db()
        self.assertEqual(item.status, FoundItem.Status.IN_CUSTODY)

    def test_NFR04_a_disposed_item_cannot_be_disposed_of_again(self):
        item = self.item(days_ago=100)
        self.dispose(item)
        self.dispose(item, reason='Changed the reason')
        item.refresh_from_db()
        self.assertEqual(item.disposal_reason, 'Donated to the campus charity drive')

    def test_NFR01_students_and_staff_cannot_dispose_of_items(self):
        item = self.item(days_ago=100)
        for person in (make_student(), make_staff()):
            self.client.force_login(person)
            self.assertEqual(self.client.get(reverse('items:desk_expired')).status_code, 403)
            self.assertEqual(self.dispose(item).status_code, 403)
