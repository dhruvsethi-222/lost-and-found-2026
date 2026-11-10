"""
Shared pages:
  /          home page
  /start/    after logging in, sends each role to its own page
  /my/       My page (Students and Staff)
  /desk/     Security desk dashboard (Admin)
"""
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from accounts.decorators import admin_only, student_or_staff
from accounts.models import Role
from items.models import FoundItem, ItemReport


def home(request):
    return render(request, 'core/home.html')


@login_required
def after_login(request):
    if request.user.role == Role.ADMIN:
        return redirect('core:desk')
    return redirect('core:my_page')


@student_or_staff
def my_page(request):
    reports = request.user.item_reports.all()          # only this person's own reports
    return render(request, 'core/my_page.html', {'reports': reports})


@admin_only
def desk(request):
    """AD-O1 (dashboard). Claims, matches and expired items are added in Dev 2 and Dev 3."""
    today = timezone.localdate()
    week_ago = timezone.now() - timedelta(days=7)
    context = {
        'in_custody': FoundItem.objects.filter(status=FoundItem.Status.IN_CUSTODY).count(),
        'recorded_today': FoundItem.objects.filter(created_at__date=today).count(),
        'lost_this_week': ItemReport.objects.filter(type='lost', created_at__gte=week_ago).count(),
        'found_this_week': ItemReport.objects.filter(type='found', created_at__gte=week_ago).count(),
        'latest_reports': ItemReport.objects.select_related('user')[:5],
    }
    return render(request, 'core/desk.html', context)
