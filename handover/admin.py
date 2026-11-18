"""
The /system-admin/ site (system owner only): hand-overs can be looked at, never changed.
NFR-04: a hand-over cannot be edited or deleted from any screen.
"""
from django.contrib import admin

from .models import HandOver


@admin.register(HandOver)
class HandOverAdmin(admin.ModelAdmin):
    list_display = ('id', 'claim', 'collector_id', 'released_by', 'date')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
