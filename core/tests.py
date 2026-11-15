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

    def test_template_notes_never_show_on_a_page(self):
        # A {# note #} in a template must stay on one line, or it shows up on the page.
        for name in ('accounts:register', 'accounts:register_staff', 'accounts:login',
                     'accounts:desk_login', 'accounts:resend'):
            self.assertNotContains(self.client.get(reverse(name)), '{#')
        self.client.force_login(make_student())
        for name in ('items:report', 'search:search', 'core:my_page'):
            self.assertNotContains(self.client.get(reverse(name)), '{#')
        self.client.force_login(make_admin())
        for name in ('items:desk_record_found', 'items:desk_found_list', 'items:desk_reports', 'core:desk',
                     'items:desk_matches', 'claims:desk_list'):
            self.assertNotContains(self.client.get(reverse(name)), '{#')
