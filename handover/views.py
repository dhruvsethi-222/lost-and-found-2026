"""
Pages for the hand-over (Admin only).

  /handover/                  items waiting to be collected, and recent hand-overs
  /handover/<claim id>/       record the hand-over of one approved claim (AD-I5, AD-P8)

Every view starts with the same two checks: logged in, and the right role
(explained at the top of core/views.py).
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import Role
from claims.models import Claim
from items.models import FoundItem

from .emails import send_hand_over_receipt
from .forms import HandOverForm
from .models import HandOver


@login_required(login_url='accounts:desk_login')
def hand_over_list(request):
    """Approved claims whose item is waiting at the desk, and the latest hand-overs."""
    if request.user.role != Role.ADMIN:
        raise PermissionDenied

    waiting = (Claim.objects.filter(status=Claim.Status.APPROVED, found_item__status=FoundItem.Status.CLAIMED)
               .select_related('user', 'found_item').order_by('decided_at'))
    recent = HandOver.objects.select_related('claim__user', 'claim__found_item', 'released_by')[:10]
    return render(request, 'handover/hand_over_list.html', {'waiting': waiting, 'recent': recent})


@login_required(login_url='accounts:desk_login')
def record_hand_over(request, claim_id):
    """
    AD-P8: record the hand-over.
    A hand-over is possible only for an approved claim whose item is still at the desk.
    """
    if request.user.role != Role.ADMIN:
        raise PermissionDenied

    claim = get_object_or_404(Claim.objects.select_related('user', 'found_item'), pk=claim_id)
    item = claim.found_item

    # Already handed over: show the record instead of the form.
    if HandOver.objects.filter(claim=claim).exists():
        messages.info(request, 'This item has already been handed over. The record cannot be changed.')
        return redirect('items:desk_found_detail', pk=item.pk)

    # No item leaves the desk without an approved claim.
    if claim.status != Claim.Status.APPROVED or item.status != FoundItem.Status.CLAIMED:
        messages.error(request, 'Only an approved claim can be handed over.')
        return redirect('claims:desk_verify', claim_id=claim.pk)

    if request.method == 'POST':
        form = HandOverForm(request.POST, claimant=claim.user)
        if form.is_valid():
            # NFR-07: the hand-over and the item's new status are saved together, or not at all.
            with transaction.atomic():
                hand_over = HandOver.objects.create(claim=claim, released_by=request.user,
                                                    collector_id=form.cleaned_data['collector_id'])   # AD-S4
                item.status = FoundItem.Status.RETURNED                                               # AD-S5
                item.save()
            send_hand_over_receipt(hand_over)
            messages.success(request, f'Handed over to {claim.user.name}. The item is now Returned.')
            return redirect('handover:list')
    else:
        form = HandOverForm(claimant=claim.user)
    return render(request, 'handover/record_hand_over.html', {'form': form, 'claim': claim, 'item': item})
