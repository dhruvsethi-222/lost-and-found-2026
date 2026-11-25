"""
Posts and replies (the user tweet and response module).

Class diagram: Post.  Database table: post.
A post with reply_to empty is a new post. A post with reply_to set is a reply to that post.
"""
from django.conf import settings
from django.db import models


class Post(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='posts')
    reply_to = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    text = models.TextField(max_length=500)            # ST-I4 / SF-I4: short, like a tweet
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'post'
        ordering = ['-date']

    def __str__(self):
        return f'Post {self.pk} by {self.user.name}'
