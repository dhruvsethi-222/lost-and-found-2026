"""
Hand-over: the record of an item going back to its owner.

Class diagram: HandOver.  Database table: hand_over.
A claim "ends in" at most one hand-over, so claim is a one-to-one link.
The record is never changed or deleted (NFR-04).
"""
from django.conf import settings
from django.db import models


class HandOver(models.Model):
    claim = models.OneToOneField('claims.Claim', on_delete=models.PROTECT, related_name='hand_over')
    released_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                    related_name='hand_overs_recorded')     # the officer
    collector_id = models.CharField(max_length=30)                          # AD-I5: the ID card shown
    date = models.DateTimeField(auto_now_add=True)                          # when it was handed over

    class Meta:
        db_table = 'hand_over'
        ordering = ['-date']

    def __str__(self):
        return f'Hand-over of claim {self.claim_id} on {self.date:%d %b %Y}'
