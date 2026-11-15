"""
The /system-admin/ site (system owner only): claims can be looked at, never changed.
NFR-04: a decision cannot be edited or deleted from any screen.
"""
from django.contrib import admin

from .models import Claim


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ('id', 'found_item', 'user', 'status', 'decided_by', 'decided_at')
    list_filter = ('status',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
