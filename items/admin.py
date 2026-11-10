from django.contrib import admin

from .models import FoundItem, ItemReport, VerificationDetail


class VerificationDetailInline(admin.StackedInline):
    model = VerificationDetail
    can_delete = False


@admin.register(FoundItem)
class FoundItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'place', 'date_found', 'status', 'recorded_by')
    list_filter = ('status', 'category', 'place')
    inlines = [VerificationDetailInline]


@admin.register(ItemReport)
class ItemReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'category', 'place', 'date', 'user')
    list_filter = ('type', 'category', 'place')
