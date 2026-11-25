"""The /system-admin/ site (system owner only): look at item records."""
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import FoundItem, ItemReport, VerificationDetail


class VerificationDetailInline(admin.StackedInline):
    model = VerificationDetail
    can_delete = False


@admin.register(FoundItem)
class FoundItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'place', 'place_other', 'date_found', 'status', 'recorded_by')
    list_filter = ('status', 'category', 'place')
    inlines = [VerificationDetailInline]


@admin.register(ItemReport)
class ItemReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'category', 'place', 'place_other', 'date', 'user')
    list_filter = ('type', 'category', 'place')
    # The report photo is private: it is not edited here, only opened through the protected page.
    exclude = ('photo',)
    readonly_fields = ('report_photo',)

    @admin.display(description='Report photo')
    def report_photo(self, report):
        if not report.photo:
            return 'No photo'
        return format_html('<a href="{}">View report photo</a>', reverse('items:report_photo', args=[report.pk]))
