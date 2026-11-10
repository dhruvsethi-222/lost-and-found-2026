"""Tests for the shared pages."""
from django.test import TestCase
from django.urls import reverse

from core.testing import make_admin, make_student


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
