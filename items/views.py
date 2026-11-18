"""
Pages for items.

  /items/report/             Students and Staff report a lost or found item
  /items/desk/found/new/     Admin records a found item with its private details
  /items/desk/found/         Admin: list of found items
  /items/desk/found/<id>/    Admin: one found item, with its private details
  /items/desk/reports/       Admin: reports sent in by Students and Staff
  /items/desk/matches/       Admin: ranked matches between lost reports and found items
  /items/desk/expired/       Admin: items past their retention period, and items expiring soon
  /items/desk/found/<id>/dispose/   Admin: dispose of an expired item (AD-P9)

Every view starts with the same two checks: logged in, and the right role
(explained at the top of core/views.py).
"""
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import Role
from claims.models import Claim
from matching.matcher import match_found_item, match_lost_report
from matching.models import Match

from .emails import send_hand_in_confirmation
from .forms import DisposeForm, FoundItemForm, ItemReportForm, VerificationDetailForm
from .models import FoundItem, ItemReport, VerificationDetail


@login_required
def report_item(request):
    """Report a lost item (ST-P3, SF-P3) or a found item (ST-P4, SF-P4)."""
    if request.user.role not in (Role.STUDENT, Role.STAFF):
        raise PermissionDenied

    role = request.user.role
    if request.method == 'POST':                      # the form was sent
        form = ItemReportForm(request.POST, role=role)
        if form.is_valid():
            report = form.save(commit=False)          # build the report, do not save yet
            report.user = request.user                # it belongs to whoever is logged in
            report.save()                             # ST-S2 / SF-S2
            if report.type == 'lost':
                # SY-I1: the matching algorithm reads the new report straight away
                matches_found = match_lost_report(report)
                if matches_found:
                    messages.success(request, 'Your lost item is reported, and we found a possible match. '
                                              'See it below.')
                else:
                    messages.success(request, 'Your lost item is reported. We will email you if a match is found.')
            else:
                messages.success(request, 'Thank you. Please take the item to the security desk.')
            return redirect('core:my_page')
    else:                                             # the page was just opened
        # ?type=found in the address opens the form on the "found" tab
        start_type = 'found' if request.GET.get('type') == 'found' else 'lost'
        form = ItemReportForm(role=role, initial={'type': start_type})
    return render(request, 'items/report_form.html', {'form': form})


@login_required(login_url='accounts:desk_login')
def record_found_item(request):
    """
    AD-P2: the Admin records a found item.
    The page has two forms: the public part (AD-I2) and the private part (AD-I3).
    """
    if request.user.role != Role.ADMIN:
        raise PermissionDenied

    if request.method == 'POST':
        # prefix= keeps the two forms' fields apart on the page (item-..., private-...)
        item_form = FoundItemForm(request.POST, request.FILES, prefix='item')
        detail_form = VerificationDetailForm(request.POST, prefix='private')
        if item_form.is_valid() and detail_form.is_valid():
            # NFR-07: both records are saved, or neither is
            with transaction.atomic():
                item = item_form.save(commit=False)
                item.recorded_by = request.user
                item.save()                           # AD-S1
                detail = detail_form.save(commit=False)
                detail.found_item = item
                detail.save()                         # AD-S2

            # SF-O5: a Staff member logged this item first, so confirm the hand-in
            if item.handed_in_report and item.handed_in_report.user.role == Role.STAFF:
                send_hand_in_confirmation(item)

            # SY-I1: the matching algorithm compares the new item with the lost reports
            matches_found = match_found_item(item)
            if matches_found == 0:
                messages.success(request, 'Found item saved with its private details. No lost report matches it yet.')
            else:
                messages.success(request, f'Found item saved with its private details. Lost reports that match: '
                                          f'{matches_found}. Each owner has been emailed.')
            return redirect('items:desk_found_detail', pk=item.pk)
    else:
        item_form = FoundItemForm(prefix='item')
        detail_form = VerificationDetailForm(prefix='private')
    return render(request, 'items/desk_record_found.html',
                  {'item_form': item_form, 'detail_form': detail_form})


@login_required(login_url='accounts:desk_login')
def found_item_list(request):
    """Admin: found items, filtered by status, 15 on a page."""
    if request.user.role != Role.ADMIN:
        raise PermissionDenied

    status = request.GET.get('status', 'in_custody')
    items = FoundItem.objects.select_related('recorded_by')
    if status in FoundItem.Status.values:             # ignore anything that is not a real status
        items = items.filter(status=status)
    page = Paginator(items, 15).get_page(request.GET.get('page'))
    return render(request, 'items/desk_found_list.html',
                  {'page': page, 'status': status, 'statuses': FoundItem.Status.choices})


@login_required(login_url='accounts:desk_login')
def found_item_detail(request, pk):
    """Admin: one found item with its private details, its ranked matches and its claims."""
    if request.user.role != Role.ADMIN:
        raise PermissionDenied

    item = get_object_or_404(FoundItem.objects.select_related('recorded_by', 'disposed_by'), pk=pk)
    # AD-P3 / AD-O2: the lost reports that match this item, best first
    matches = Match.objects.filter(found_item=item).select_related('report__user').order_by('rank')
    return render(request, 'items/desk_found_detail.html', {'item': item, 'matches': matches})


@login_required(login_url='accounts:desk_login')
def report_list(request):
    """Admin: what Students and Staff have reported, so the desk knows what to expect."""
    if request.user.role != Role.ADMIN:
        raise PermissionDenied

    kind = request.GET.get('type', '')
    reports = ItemReport.objects.select_related('user')
    if kind in ('lost', 'found'):
        reports = reports.filter(type=kind)
    page = Paginator(reports, 15).get_page(request.GET.get('page'))
    return render(request, 'items/desk_reports.html', {'page': page, 'kind': kind})


@login_required(login_url='accounts:desk_login')
def match_list(request):
    """AD-P3 / AD-O2: every ranked match for the items still at the desk, 15 on a page."""
    if request.user.role != Role.ADMIN:
        raise PermissionDenied

    matches = (Match.objects.filter(found_item__status=FoundItem.Status.IN_CUSTODY)
               .select_related('found_item', 'report__user')
               .order_by('-found_item__created_at', 'rank'))
    page = Paginator(matches, 15).get_page(request.GET.get('page'))
    return render(request, 'items/desk_matches.html', {'page': page})


@login_required(login_url='accounts:desk_login')
def expired_list(request):
    """
    NFR-02: items still in custody after the retention period (RETENTION_DAYS) can be disposed of.
    Items that will expire within EXPIRING_SOON_DAYS are listed too, so the desk can plan.
    """
    if request.user.role != Role.ADMIN:
        raise PermissionDenied

    # An item is kept until date_found + RETENTION_DAYS (see FoundItem.retention_ends), so:
    #   expired:        date_found is before  today - RETENTION_DAYS
    #   expiring soon:  date_found is within EXPIRING_SOON_DAYS after that day
    oldest_kept = timezone.localdate() - timedelta(days=settings.RETENTION_DAYS)
    soon_limit = oldest_kept + timedelta(days=settings.EXPIRING_SOON_DAYS)
    in_custody = FoundItem.objects.filter(status=FoundItem.Status.IN_CUSTODY).order_by('date_found')
    return render(request, 'items/desk_expired.html', {
        'expired': in_custody.filter(date_found__lt=oldest_kept),
        'expiring_soon': in_custody.filter(date_found__gte=oldest_kept, date_found__lte=soon_limit),
        'retention_days': settings.RETENTION_DAYS,
    })


@login_required(login_url='accounts:desk_login')
def dispose_item(request, pk):
    """
    AD-P9: dispose of an expired item. AD-S5: its status is stored as Disposed.
    Saved with the officer, the time and the reason, and never changed again (NFR-04).
    """
    if request.user.role != Role.ADMIN:
        raise PermissionDenied

    item = get_object_or_404(FoundItem, pk=pk)

    # Only an item still in custody and past its retention period can be disposed of.
    if not item.is_expired:
        messages.error(request, 'Only an item in custody that is past its retention period can be disposed of.')
        return redirect('items:desk_found_detail', pk=item.pk)

    # An owner may still be waiting for a decision: decide the open claims first.
    if Claim.objects.filter(found_item=item, status__in=['pending', 'more_evidence']).exists():
        messages.error(request, 'This item has open claims. Decide them before disposing of the item.')
        return redirect('items:desk_found_detail', pk=item.pk)

    if request.method == 'POST':
        form = DisposeForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                item.status = FoundItem.Status.DISPOSED          # AD-S5
                item.disposed_by = request.user
                item.disposed_at = timezone.now()
                item.disposal_reason = form.cleaned_data['reason']
                item.save()
                # NFR-02: the private details are personal data, so they are deleted with the item.
                VerificationDetail.objects.filter(found_item=item).delete()
            messages.success(request, 'The item is disposed of and its private details are deleted.')
            return redirect('items:desk_expired')
    else:
        form = DisposeForm()
    return render(request, 'items/desk_dispose.html', {'item': item, 'form': form})
