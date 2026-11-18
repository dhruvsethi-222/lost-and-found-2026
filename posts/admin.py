"""The /system-admin/ site (system owner only): look at posts, and remove one if it breaks the rules."""
from django.contrib import admin

from .models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'reply_to', 'text', 'date')
    search_fields = ('text', 'user__name')
