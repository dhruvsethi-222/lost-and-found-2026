"""
Shared pages.

  /          home page (everyone)
  /start/    after logging in: sends each kind of account to its own page
  /my/       My page (Students and Staff)
  /desk/     Security desk (Admin)

How pages are protected (NFR-01), used the same way in every views.py:
  1. @login_required sends visitors who are not logged in to the log-in page.
  2. The first lines of the view check the role. A wrong role raises
     PermissionDenied, which shows the "Access denied" page (templates/403.html).
"""
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.utils import timezone

from accounts.models import Role
from claims.models import Claim
from items.models import FoundItem, ItemReport
from matching.models import Match


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
    claims = Claim.objects.filter(user=request.user).select_related('found_item')

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
    """The Admin's dashboard: pending claims (AD-O1), ranked matches (AD-O2), counts and the latest reports."""
    if request.user.role != Role.ADMIN:
        raise PermissionDenied

    today = timezone.localdate()
    week_ago = timezone.now() - timedelta(days=7)
    in_custody = FoundItem.Status.IN_CUSTODY
    context = {
        'pending_claims': Claim.objects.filter(status=Claim.Status.PENDING).count(),
        'ranked_matches': Match.objects.filter(found_item__status=in_custody).count(),
        'in_custody': FoundItem.objects.filter(status=FoundItem.Status.IN_CUSTODY).count(),
        'recorded_today': FoundItem.objects.filter(created_at__date=today).count(),
        'lost_this_week': ItemReport.objects.filter(type='lost', created_at__gte=week_ago).count(),
        'found_this_week': ItemReport.objects.filter(type='found', created_at__gte=week_ago).count(),
        'latest_reports': ItemReport.objects.select_related('user')[:5],
    }
    return render(request, 'core/desk.html', context)
