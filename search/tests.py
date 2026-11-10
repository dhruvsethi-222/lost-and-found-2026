"""Tests for searching found items, including the privacy rule (NFR-02)."""
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.testing import make_admin, make_staff, make_student
from items.models import FoundItem, VerificationDetail


def found(officer, category, description, place, status=FoundItem.Status.IN_CUSTODY, **private):
    item = FoundItem.objects.create(recorded_by=officer, category=category, description=description, place=place,
                                    date_found=timezone.localdate(), photo='found_items/x.png', status=status)
    VerificationDetail.objects.create(found_item=item, **private)
    return item


class SearchTests(TestCase):
    def setUp(self):
        officer = make_admin()
        found(officer, 'wallet', 'Black leather wallet', 'library', serial_no='SN-SECRET-1', contents='Student ID card')
        found(officer, 'phone', 'Blue phone with cracked screen', 'student_centre', marks='Sticker of a lion')
        found(officer, 'wallet', 'Brown wallet', 'cafeteria', status=FoundItem.Status.RETURNED)
        self.client.force_login(make_student())

    def search(self, **params):
        return self.client.get(reverse('search:search'), params)

    def test_ST_P5_search_by_words_finds_the_black_wallet(self):
        response = self.search(q='black wallet')
        self.assertContains(response, 'Black leather wallet')                 # ST-O2
        self.assertNotContains(response, 'Blue phone')

    def test_search_by_place_word_and_by_filters(self):
        self.assertContains(self.search(q='library'), 'Black leather wallet')
        self.assertContains(self.search(category='phone'), 'Blue phone')
        self.assertNotContains(self.search(place='library'), 'Blue phone')

    def test_only_items_still_at_the_desk_are_shown(self):
        self.assertNotContains(self.search(q='wallet'), 'Brown wallet')        # already returned

    def test_NFR02_private_details_never_appear(self):
        for params in ({}, {'q': 'wallet'}, {'q': 'phone'}, {'category': 'wallet'}):
            response = self.search(**params)
            for secret in ('SN-SECRET-1', 'Student ID card', 'Sticker of a lion'):
                self.assertNotContains(response, secret)

    def test_NFR02_searching_for_a_private_detail_finds_nothing(self):
        for secret_word in ('SN-SECRET-1', 'lion', 'card'):
            self.assertEqual(self.search(q=secret_word).context['page'].paginator.count, 0)

    def test_SF_P5_staff_can_search_too(self):
        self.client.force_login(make_staff())
        self.assertContains(self.search(q='phone'), 'Blue phone')

    def test_logged_out_visitors_must_log_in_to_search(self):
        self.client.logout()
        self.assertEqual(self.search().status_code, 302)
