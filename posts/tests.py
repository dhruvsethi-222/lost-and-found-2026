"""
Tests for posts and replies.
Each test name starts with the requirement it proves.  Run:  python manage.py test posts
"""
from django.test import TestCase
from django.urls import reverse

from core.testing import make_admin, make_staff, make_student
from posts.models import Post


class PostTests(TestCase):
    def setUp(self):
        self.student = make_student()
        self.client.force_login(self.student)

    def test_ST_P7_student_publishes_a_post_and_it_is_stored(self):
        response = self.client.post(reverse('posts:list'),
                                    {'text': 'Has anyone seen a blue umbrella near the library?'}, follow=True)
        post = Post.objects.get()                                             # ST-S4
        self.assertEqual((post.user, post.reply_to), (self.student, None))
        self.assertContains(response, 'Has anyone seen a blue umbrella')

    def test_SF_P7_staff_publishes_a_post(self):
        staff = make_staff()
        self.client.force_login(staff)
        self.client.post(reverse('posts:list'), {'text': 'A grey jacket was left in room 3.'})
        self.assertEqual(Post.objects.get().user, staff)                     # SF-S4

    def test_ST_P7_reply_to_a_post(self):
        post = Post.objects.create(user=make_staff(), text='A grey jacket was left in room 3.')
        self.client.post(reverse('posts:reply', args=[post.pk]), {'text': 'Thank you, it is mine.'})
        reply = Post.objects.get(reply_to=post)
        self.assertEqual(reply.user, self.student)
        page = self.client.get(reverse('posts:list'))
        self.assertContains(page, 'Thank you, it is mine.')

    def test_ST_I4_a_post_needs_text_and_is_at_most_280_characters(self):
        self.client.post(reverse('posts:list'), {'text': ''})
        self.client.post(reverse('posts:list'), {'text': 'x' * 281})
        self.assertFalse(Post.objects.exists())

    def test_a_reply_cannot_be_replied_to(self):
        post = Post.objects.create(user=self.student, text='Lost keys')
        answer = Post.objects.create(user=self.student, reply_to=post, text='Found them')
        response = self.client.post(reverse('posts:reply', args=[answer.pk]), {'text': 'Great'})
        self.assertEqual(response.status_code, 404)

    def test_newest_posts_come_first_10_on_a_page(self):
        for number in range(12):
            Post.objects.create(user=self.student, text=f'Post number {number}')
        page = self.client.get(reverse('posts:list')).context['page']
        self.assertEqual(len(page.object_list), 10)
        self.assertEqual(page.object_list[0].text, 'Post number 11')

    def test_NFR01_admin_and_logged_out_visitors_cannot_use_posts(self):
        self.client.force_login(make_admin())
        self.assertEqual(self.client.get(reverse('posts:list')).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(reverse('posts:list')).status_code, 302)

    def test_posts_are_shown_as_text_not_as_html(self):
        self.client.post(reverse('posts:list'), {'text': '<script>alert(1)</script>'})
        page = self.client.get(reverse('posts:list'))
        self.assertNotContains(page, '<script>alert(1)</script>')            # NFR-01: no cross-site scripting
        self.assertContains(page, '&lt;script&gt;')
