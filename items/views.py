"""
Pages for items.

  /items/report/             Students and Staff report a lost or found item
  /items/desk/found/new/     Admin records a found item with its private details
  /items/desk/found/         Admin: list of found items
  /items/desk/found/<id>/    Admin: one found item, with its private details
  /items/desk/reports/       Admin: reports sent in by Students and Staff

Every view starts with the same two checks: logged in, and the right role
(explained at the top of core/views.py).
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import Role

from .forms import FoundItemForm, ItemReportForm, VerificationDetailForm
from .models import FoundItem, ItemReport


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
            messages.success(request, 'Found item saved with its private details.')
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
    """Admin: one found item with its private details. No other page shows them (NFR-02)."""
    if request.user.role != Role.ADMIN:
        raise PermissionDenied

    item = get_object_or_404(FoundItem.objects.select_related('recorded_by', 'verification_detail'), pk=pk)
    return render(request, 'items/desk_found_detail.html', {'item': item})


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
