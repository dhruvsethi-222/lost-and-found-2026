"""
Pages for items.
  /items/report/                      Students and Staff report a lost or found item
  /items/desk/found/new/              Admin records a found item with its private details
  /items/desk/found/                  Admin: list of found items
  /items/desk/found/<id>/             Admin: one found item, with its private details
  /items/desk/reports/                Admin: reports sent in by Students and Staff
"""
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import admin_only, student_or_staff

from .forms import FoundItemForm, ItemReportForm, VerificationDetailForm
from .models import FoundItem, ItemReport


@student_or_staff
def report_item(request):
    """ST-P3 / ST-P4 (Student) and SF-P3 / SF-P4 (Staff)."""
    role = request.user.role
    if request.method == 'POST':
        form = ItemReportForm(request.POST, role=role)
        if form.is_valid():
            report = form.save(commit=False)
            report.user = request.user          # the report belongs to whoever is logged in
            report.save()                       # ST-S2 / SF-S2
            if report.type == ItemReport.Type.LOST:
                messages.success(request, 'Your lost item is reported. We will email you if a match is found.')
            else:
                messages.success(request, 'Thank you. Please take the item to the security desk.')
            return redirect('core:my_page')
    else:
        start_type = request.GET.get('type') if request.GET.get('type') in ('lost', 'found') else 'lost'
        form = ItemReportForm(role=role, initial={'type': start_type})
    return render(request, 'items/report_form.html', {'form': form})


@admin_only
def record_found_item(request):
    """AD-P2: the found item and its private details are saved together (AD-S1, AD-S2)."""
    if request.method == 'POST':
        item_form = FoundItemForm(request.POST, request.FILES, prefix='item')
        detail_form = VerificationDetailForm(request.POST, prefix='private')
        if item_form.is_valid() and detail_form.is_valid():
            with transaction.atomic():           # both saved, or neither (NFR-07)
                item = item_form.save(commit=False)
                item.recorded_by = request.user
                item.save()
                detail = detail_form.save(commit=False)
                detail.found_item = item
                detail.save()
            messages.success(request, 'Found item saved with its private details.')
            return redirect('items:desk_found_detail', pk=item.pk)
    else:
        item_form = FoundItemForm(prefix='item')
        detail_form = VerificationDetailForm(prefix='private')
    return render(request, 'items/desk_record_found.html', {'item_form': item_form, 'detail_form': detail_form})


@admin_only
def found_item_list(request):
    status = request.GET.get('status', FoundItem.Status.IN_CUSTODY)
    items = FoundItem.objects.select_related('recorded_by')
    if status in FoundItem.Status.values:
        items = items.filter(status=status)
    page = Paginator(items, 15).get_page(request.GET.get('page'))
    return render(request, 'items/desk_found_list.html',
                  {'page': page, 'status': status, 'statuses': FoundItem.Status.choices})


@admin_only
def found_item_detail(request, pk):
    item = get_object_or_404(FoundItem.objects.select_related('recorded_by', 'verification_detail'), pk=pk)
    return render(request, 'items/desk_found_detail.html', {'item': item})


@admin_only
def report_list(request):
    """What Students and Staff have reported, so the desk knows what to expect."""
    kind = request.GET.get('type', '')
    reports = ItemReport.objects.select_related('user')
    if kind in ItemReport.Type.values:
        reports = reports.filter(type=kind)
    page = Paginator(reports, 15).get_page(request.GET.get('page'))
    return render(request, 'items/desk_reports.html', {'page': page, 'kind': kind})
