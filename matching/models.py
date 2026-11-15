"""
Matching: the table that links a lost report to a found item that may be the same thing.

Class diagram: Match.  Database table: match.
One lost report can match many found items, and one found item can match many
lost reports. Each pair is one row, with its score and its rank.
"""
from django.db import models


class Match(models.Model):
    report = models.ForeignKey('items.ItemReport', on_delete=models.CASCADE, related_name='matches')
    found_item = models.ForeignKey('items.FoundItem', on_delete=models.CASCADE, related_name='matches')
    score = models.DecimalField(max_digits=5, decimal_places=2)     # 0 to 100; higher = more alike
    rank = models.IntegerField(default=1)                           # 1 = the best match for this found item

    class Meta:
        db_table = 'match'
        ordering = ['found_item', 'rank']
        constraints = [
            # the same pair is stored only once
            models.UniqueConstraint(fields=['report', 'found_item'], name='one_match_per_pair'),
        ]

    def __str__(self):
        return f'Lost report {self.report_id} and found item {self.found_item_id}: {self.score} points'
