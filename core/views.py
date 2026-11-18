"""
Shared pages.

  /          home page (everyone)
  /start/    after logging in: sends each kind of account to its own page
  /my/       My page (Students and Staff)
  /desk/     Security desk (Admin)
  /reports/  Reports for the Admin (AD-R1)

How pages are protected (NFR-01), used the same way in every views.py:
  1. @login_required sends visitors who are not logged in to the log-in page.
  2. The first lines of the view check the role. A wrong role raises
     PermissionDenied, which shows the "Access denied" page (templates/403.html).
"""
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.shortcuts import redirect, render
from django.utils import timezone

from accounts.models import Role
from claims.models import Claim
from handover.models import HandOver
from items.choices import Category, Place
from items.models import FoundItem, ItemReport
from matching.models import Match

from .forms import ReportPeriodForm


def home(request):
    return render(request, 'core/home.html')


@login_required
def after_login(request):
    """Where to go straight after logging in."""
    if request.user.role == Role.ADMIN:
        return redirect('core:desk')
    return redirect('core:my_page')


@login_required
def my_page(request):
    """
    ST-R1 / SF-R1: a Student or Staff member sees only their own records:
    match alerts (ST-O3, SF-O3), claims with their status (ST-O4, SF-O4), and reports.
    """
    if request.user.role not in (Role.STUDENT, Role.STAFF):
        raise PermissionDenied

    reports = ItemReport.objects.filter(user=request.user)
    claims = Claim.objects.filter(user=request.user).select_related('found_item', 'hand_over')

    # Match alerts: items at the desk that match one of my lost reports and that I have not claimed yet.
    claimed_item_ids = [claim.found_item_id for claim in claims]
    alerts = (Match.objects.filter(report__user=request.user, found_item__status=FoundItem.Status.IN_CUSTODY)
              .exclude(found_item_id__in=claimed_item_ids)
              .select_related('report', 'found_item')
              .order_by('-score')[:5])

    return render(request, 'core/my_page.html', {
        'reports': reports, 'claims': claims, 'alerts': alerts,
        'collection_hours': settings.DESK_COLLECTION_HOURS})


@login_required(login_url='accounts:desk_login')
def desk(request):
    """
    The Admin's dashboard, as in the wireframe: pending claims (AD-O1), ranked matches (AD-O2),
    expired items to dispose of, items waiting for collection, and the latest reports.
    """
    if request.user.role != Role.ADMIN:
        raise PermissionDenied

    in_custody = FoundItem.Status.IN_CUSTODY
    oldest_kept = timezone.localdate() - timedelta(days=settings.RETENTION_DAYS)
    context = {
        'pending_claims': Claim.objects.filter(status=Claim.Status.PENDING).count(),
        'ranked_matches': Match.objects.filter(found_item__status=in_custody).count(),
        'expired_items': FoundItem.objects.filter(status=in_custody, date_found__lt=oldest_kept).count(),
        'waiting_collection': FoundItem.objects.filter(status=FoundItem.Status.CLAIMED).count(),
        'in_custody': FoundItem.objects.filter(status=in_custody).count(),
        'recorded_today': FoundItem.objects.filter(created_at__date=timezone.localdate()).count(),
        'latest_reports': ItemReport.objects.select_related('user')[:5],
    }
    return render(request, 'core/desk.html', context)


def top_five(reports, field, choices):
    """
    Counts the reports for each value of one field (place or category) and returns the five largest,
    e.g. [('Library', 12), ('Cafeteria', 7), ...].
    """
    rows = reports.values(field).annotate(total=Count('id')).order_by('-total')[:5]
    labels = dict(choices)
    return [(labels.get(row[field], row[field]), row['total']) for row in rows]


@login_required(login_url='accounts:desk_login')
def reports(request):
    """
    AD-R1: reports for a period the Admin chooses (the last 30 days to start with):
    items received, returned and disposed; claims; items expiring; where most items are lost;
    and the audit log of every decision, hand-over and disposal (NFR-04).
    """
    if request.user.role != Role.ADMIN:
        raise PermissionDenied

    today = timezone.localdate()
    form = ReportPeriodForm(request.GET or None, initial={'date_from': today - timedelta(days=30), 'date_to': today})
    if form.is_valid():
        date_from = form.cleaned_data['date_from']
        date_to = form.cleaned_data['date_to']
    else:
        date_from = today - timedelta(days=30)
        date_to = today

    # Everything below counts only what happened between date_from and date_to (both days included).
    received = FoundItem.objects.filter(created_at__date__range=(date_from, date_to))
    hand_overs = HandOver.objects.filter(date__date__range=(date_from, date_to)).select_related(
        'claim__user', 'claim__found_item', 'released_by')
    disposed = FoundItem.objects.filter(disposed_at__date__range=(date_from, date_to)).select_related('disposed_by')
    decisions = Claim.objects.filter(decided_at__date__range=(date_from, date_to)).select_related(
        'user', 'found_item', 'decided_by')
    lost_reports = ItemReport.objects.filter(type='lost', date__range=(date_from, date_to))

    # The audit log: one list of every decision, hand-over and disposal, newest first.
    audit_log = []
    for claim in decisions:
        audit_log.append({'when': claim.decided_at, 'what': f'Claim {claim.get_status_display().lower()}',
                          'item': claim.found_item, 'person': claim.user.name,
                          'officer': claim.decided_by, 'reason': claim.reason})
    for hand_over in hand_overs:
        audit_log.append({'when': hand_over.date, 'what': 'Handed over', 'item': hand_over.claim.found_item,
                          'person': hand_over.claim.user.name, 'officer': hand_over.released_by,
                          'reason': f'ID {hand_over.collector_id} checked'})
    for item in disposed:
        audit_log.append({'when': item.disposed_at, 'what': 'Disposed', 'item': item, 'person': '',
                          'officer': item.disposed_by, 'reason': item.disposal_reason})
    audit_log.sort(key=lambda entry: entry['when'], reverse=True)

    oldest_kept = today - timedelta(days=settings.RETENTION_DAYS)
    in_custody = FoundItem.objects.filter(status=FoundItem.Status.IN_CUSTODY)
    context = {
        'form': form, 'date_from': date_from, 'date_to': date_to,
        'received': received.count(),
        'returned': hand_overs.count(),
        'disposed': disposed.count(),
        'lost_reported': lost_reports.count(),
        'pending_now': Claim.objects.filter(status__in=['pending', 'more_evidence']).count(),
        'approved': decisions.filter(status=Claim.Status.APPROVED).count(),
        'rejected': decisions.filter(status=Claim.Status.REJECTED).count(),
        'closed': decisions.filter(status=Claim.Status.CLOSED).count(),
        'expired_now': in_custody.filter(date_found__lt=oldest_kept).count(),
        'expiring_soon': in_custody.filter(
            date_found__gte=oldest_kept,
            date_found__lte=oldest_kept + timedelta(days=settings.EXPIRING_SOON_DAYS)).count(),
        'top_places': top_five(lost_reports, 'place', Place.choices),
        'top_categories': top_five(lost_reports, 'category', Category.choices),
        'audit_log': audit_log,
    }
    return render(request, 'core/reports.html', context)
