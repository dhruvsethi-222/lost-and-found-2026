"""The /system-admin/ site (system owner only): look at the saved matches."""
from django.contrib import admin

from .models import Match


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'report', 'found_item', 'score', 'rank')
