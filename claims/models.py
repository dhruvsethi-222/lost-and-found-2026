"""
Claims: a Student or Staff member says a found item is theirs, and the Admin decides.

Class diagram: Claim.  Database table: claim.
The Admin's decision is stored on the claim itself: who decided, when, and why (AD-S3, NFR-04).
"""
from django.conf import settings
from django.db import models


class Claim(models.Model):

    class Status(models.TextChoices):
        PENDING = 'pending', 'Under review'                       # waiting for the Admin
        MORE_EVIDENCE = 'more_evidence', 'More details needed'    # the Admin asked a question
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        CLOSED = 'closed', 'Closed'                               # another claim for the item was approved

    found_item = models.ForeignKey('items.FoundItem', on_delete=models.PROTECT, related_name='claims')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='claims')
    # What makes it theirs (ST-I3, SF-I3), then any follow-up questions and answers.
    # Each entry is at most 500 characters (checked in claims/forms.py); the whole conversation can be longer.
    answers = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    # The decision (AD-S3). Empty until the Admin decides.
    decided_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
                                   related_name='claims_decided')
    reason = models.TextField(max_length=500, blank=True)         # AD-I4
    decided_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'claim'
        ordering = ['-created_at']
        constraints = [
            # one person can claim the same item only once
            models.UniqueConstraint(fields=['found_item', 'user'], name='one_claim_per_person_per_item'),
        ]

    def __str__(self):
        return f'Claim {self.pk} by {self.user.name} for found item {self.found_item_id}'

    @property
    def is_open(self):
        """True while the Admin can still decide. A final decision can never be changed (NFR-04)."""
        return self.status in (self.Status.PENDING, self.Status.MORE_EVIDENCE)
