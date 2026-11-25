"""
The matching algorithm (SY-I1, SY-P2, SY-P3, SY-S1, SY-O1, SY-O2).

It has no pages of its own. Two views call it:
  - items/views.py -> report_item         calls match_lost_report()  for a new lost report
  - items/views.py -> record_found_item   calls match_found_item()   for a new found item

It runs once for each new record, not every time a page is opened (NFR-05).

How two records are compared (SY-P2). The score is out of 100:
    category   the same            40 points   (a different category is never a match)
    place      the same            20 points
    date       0 days apart        20 points,  up to 3 days 15,  up to 7 days 10,  up to 30 days 5
    keywords   5 points for each word the two descriptions share, up to 20 points

A pair is saved as a match when its score is at least MATCH_MINIMUM_SCORE (50).
So the same category alone is not enough: the place, the date or the words must agree too.
"""
from django.conf import settings

from items.choices import Place
from items.models import FoundItem, ItemReport

from .emails import send_match_alert
from .models import Match

# Small words that say nothing about an item.
WORDS_TO_SKIP = ['the', 'and', 'with', 'for', 'has', 'was', 'had', 'its', 'that', 'this', 'inside']


def keywords(text):
    """Turns a description into a list of useful words: 'Black leather wallet.' -> ['black', 'leather', 'wallet']"""
    words = []
    for word in text.lower().split():
        word = word.strip('.,;:!?()"\'')              # remove punctuation around the word
        if len(word) >= 3 and word not in WORDS_TO_SKIP and word not in words:
            words.append(word)
    return words


def same_place(report, found_item):
    """
    Same place? The dropdown choices must be the same.
    When both chose "Other", the typed locations must also be the same,
    after removing spaces at both ends and ignoring capital letters.
    Choosing "Other" on both forms is not enough on its own.
    """
    if report.place != found_item.place:
        return False
    if report.place != Place.OTHER:
        return True
    mine = report.place_other.strip().lower()
    theirs = found_item.place_other.strip().lower()
    return mine != '' and mine == theirs


def score_pair(report, found_item):
    """SY-P2: how alike are a lost report and a found item? Returns 0 to 100."""
    # 1. Category: must be the same.
    if report.category != found_item.category:
        return 0
    score = 40

    # 2. Place
    if same_place(report, found_item):
        score += 20

    # 3. Date: how many days between the day it was lost and the day it was found
    days_apart = abs((found_item.date_found - report.date).days)
    if days_apart == 0:
        score += 20
    elif days_apart <= 3:
        score += 15
    elif days_apart <= 7:
        score += 10
    elif days_apart <= 30:
        score += 5

    # 4. Keywords: words that are in both descriptions
    found_words = keywords(found_item.description)
    shared_words = 0
    for word in keywords(report.description):
        if word in found_words:
            shared_words += 1
    score += min(shared_words * 5, 20)

    return score


def rank_matches(found_item):
    """SY-P3: numbers the matches of one found item 1, 2, 3... with the highest score first."""
    position = 1
    for match in Match.objects.filter(found_item=found_item).order_by('-score', 'id'):
        if match.rank != position:
            match.rank = position
            match.save()
        position += 1


def match_lost_report(report):
    """
    Called when a Student or Staff member reports a lost item.
    Compares the report with every item at the security desk in the same category.
    Returns how many matches were saved.
    """
    candidates = FoundItem.objects.filter(status=FoundItem.Status.IN_CUSTODY, category=report.category)
    new_matches = []
    for found_item in candidates:
        score = score_pair(report, found_item)
        if score >= settings.MATCH_MINIMUM_SCORE:
            new_matches.append(Match(report=report, found_item=found_item, score=score))
    Match.objects.bulk_create(new_matches)            # SY-S1: save them all in one go

    for match in new_matches:                         # SY-P3: give each found item's list its order
        rank_matches(match.found_item)

    if new_matches:
        send_match_alert(report)                      # SY-O2 -> ST-O3 / SF-O3
    return len(new_matches)


def match_found_item(found_item):
    """
    Called when the Admin records a found item.
    Compares the item with every lost report in the same category.
    Returns how many matches were saved.
    """
    candidates = ItemReport.objects.filter(type='lost', category=found_item.category).select_related('user')
    new_matches = []
    for report in candidates:
        score = score_pair(report, found_item)
        if score >= settings.MATCH_MINIMUM_SCORE:
            new_matches.append(Match(report=report, found_item=found_item, score=score))
    Match.objects.bulk_create(new_matches)            # SY-S1

    rank_matches(found_item)                          # SY-P3

    for match in new_matches:                         # SY-O2: tell each owner
        send_match_alert(match.report)
    return len(new_matches)
