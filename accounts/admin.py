"""The /system-admin/ site (system owner only): see and switch off accounts."""
from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'role', 'is_verified', 'is_active', 'date_joined')
    list_filter = ('role', 'is_verified', 'is_active')
    search_fields = ('email', 'name', 'admission_no', 'staff_no', 'officer_no')
    readonly_fields = ('password', 'last_login', 'date_joined')
    fields = ('name', 'email', 'role', 'admission_no', 'staff_no', 'department', 'officer_no',
              'is_verified', 'is_active', 'is_staff', 'is_superuser', 'password', 'last_login', 'date_joined')

    def has_delete_permission(self, request, obj=None):
        return False          # accounts are switched off (is_active), never deleted
