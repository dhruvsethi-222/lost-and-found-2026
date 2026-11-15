"""
Items: what Students and Staff report, and what the Admin holds at the security desk.

Database schema tables: item_report, found_item, verification_detail.
"""
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from accounts.models import Role

from .choices import Category, Place


def not_in_future(value):
    """NFR-03: an item cannot be lost or found on a date that has not happened yet."""
    if value > timezone.localdate():
        raise ValidationError('The date cannot be in the future.')


def photo_path(instance, filename):
    """Saves each photo under a random name, so nobody can guess the address of a photo."""
    return f'found_items/{uuid4().hex}{Path(filename).suffix.lower()}'


class ItemReport(models.Model):
    """A lost or found report made by a Student or a Staff member (class ItemReport, table item_report)."""

    class Type(models.TextChoices):
        LOST = 'lost', 'Lost'
        FOUND = 'found', 'Found'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='item_reports')
    type = models.CharField(max_length=5, choices=Type.choices)
    category = models.CharField(max_length=40, choices=Category.choices)
    description = models.TextField(max_length=500)
    date = models.DateField(validators=[not_in_future])
    place = models.CharField(max_length=80, choices=Place.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'item_report'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['category', 'date']), models.Index(fields=['place'])]   # NFR-05

    def __str__(self):
        # Also the text shown in the "handed in by" dropdown on the Record found item page.
        return (f'{self.kind_label}: {self.get_category_display()}, {self.get_place_display()}, '
                f'{self.date:%d %b %Y}, reported by {self.user.name}')

    @property
    def kind_label(self):
        """How the report is named on screen: Lost, Found, or Office item for Staff (SF-P4)."""
        if self.type == 'found' and self.user.role == Role.STAFF:
            return 'Office item'
        return self.get_type_display()

    @property
    def status_label(self):
        """What My page shows beside a report (ST-R1, SF-R1)."""
        if self.type == 'lost':
            if self.matches.exists():                 # rows in the match table for this report
                return 'Matched'
            return 'No match yet'
        if self.received_items.exists():              # the Admin recorded the item at the desk
            return 'Handed in'
        return 'Not yet at the security desk'


class FoundItem(models.Model):
    """The physical item held at the security desk (class FoundItem, table found_item)."""

    class Status(models.TextChoices):
        IN_CUSTODY = 'in_custody', 'In custody'
        CLAIMED = 'claimed', 'Claimed'
        RETURNED = 'returned', 'Returned'
        DISPOSED = 'disposed', 'Disposed'

    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                    related_name='found_items_recorded', limit_choices_to={'role': Role.ADMIN})
    category = models.CharField(max_length=40, choices=Category.choices)
    description = models.TextField(max_length=500)
    place = models.CharField(max_length=80, choices=Place.choices)
    date_found = models.DateField(validators=[not_in_future])
    photo = models.ImageField(upload_to=photo_path)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.IN_CUSTODY)
    # The found report this item came from, if a Student or Staff member reported it first (SF-O5).
    handed_in_report = models.ForeignKey(ItemReport, on_delete=models.PROTECT, null=True, blank=True,
                                         related_name='received_items', limit_choices_to={'type': 'found'})
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'found_item'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['category', 'date_found']), models.Index(fields=['place']),
                   models.Index(fields=['status'])]

    def __str__(self):
        return f'{self.get_category_display()} found at {self.get_place_display()} on {self.date_found:%d %b %Y}'


class VerificationDetail(models.Model):
    """
    Private details only the real owner would know (class VerificationDetail, table verification_detail).
    Composition: the details belong to one found item and are deleted with it (on_delete=CASCADE).
    Only Admin pages ever read this table (NFR-02).
    """

    found_item = models.OneToOneField(FoundItem, on_delete=models.CASCADE, related_name='verification_detail')
    serial_no = models.CharField('Serial number', max_length=80, blank=True)
    marks = models.TextField('Marks', blank=True, help_text='Scratches, stickers, a torn corner.')
    contents = models.TextField('What is inside it', blank=True, help_text='e.g. student ID, two keys.')

    class Meta:
        db_table = 'verification_detail'

    def __str__(self):
        return f'Private details of found item {self.found_item_id}'
