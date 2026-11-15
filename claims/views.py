"""
Pages for claims.

  /claims/new/<found item id>/     Student or Staff claims an item (ST-P6, SF-P6)
  /claims/<claim id>/add-details/  the claimant answers a request for more evidence
  /claims/desk/                    Admin: list of claims (AD-O1)
  /claims/desk/<claim id>/         Admin: the claim beside the private details, and the decision
                                   (AD-P4, AD-O3, AD-P5, AD-P6, AD-P7)

Every view starts with the same two checks: logged in, and the right role
(explained at the top of core/views.py).
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import Role
from items.models import FoundItem
from matching.models import Match

from .emails import send_claim_decision
from .forms import ClaimForm, DecisionForm, MoreDetailsForm
from .models import Claim


# --------------------------------------------------------------------------- Student and Staff

@login_required
def submit_claim(request, found_item_id):
    """ST-P6 / SF-P6: claim an item that is at the security desk."""
    if request.user.role not in (Role.STUDENT, Role.STAFF):
        raise PermissionDenied

    # Only items still at the desk can be claimed. Anything else gives "Page not found".
    item = get_object_or_404(FoundItem, pk=found_item_id, status=FoundItem.Status.IN_CUSTODY)

    # One person can claim the same item only once.
    if Claim.objects.filter(found_item=item, user=request.user).exists():
        messages.info(request, 'You have already claimed this item. Its status is below.')
        return redirect('core:my_page')

    if request.method == 'POST':
        form = ClaimForm(request.POST)
        if form.is_valid():
            Claim.objects.create(found_item=item, user=request.user,
                                 answers=form.cleaned_data['answers'])        # ST-S3 / SF-S3
            messages.success(request, 'Your claim was sent. A security officer will check it.')
            return redirect('core:my_page')
    else:
        form = ClaimForm()
    return render(request, 'claims/claim_form.html', {'form': form, 'item': item})


@login_required
def add_details(request, claim_id):
    """The claimant adds details after the Admin requested more evidence."""
    if request.user.role not in (Role.STUDENT, Role.STAFF):
        raise PermissionDenied

    # user=request.user: nobody can open another person's claim.
    claim = get_object_or_404(Claim, pk=claim_id, user=request.user, status=Claim.Status.MORE_EVIDENCE)

    if request.method == 'POST':
        form = MoreDetailsForm(request.POST)
        if form.is_valid():
            # Keep the whole conversation in the answers, so nothing is lost (NFR-04).
            today = timezone.localdate().strftime('%d %b %Y')
            claim.answers += (f'\n\nSecurity asked ({claim.decided_by.name}, {today}): {claim.reason}'
                              f'\nClaimant added ({today}): {form.cleaned_data["details"]}')
            claim.status = Claim.Status.PENDING          # back to the Admin
            claim.save()
            messages.success(request, 'Thank you. Your claim is back with the security desk.')
            return redirect('core:my_page')
    else:
        form = MoreDetailsForm()
    return render(request, 'claims/add_details.html', {'form': form, 'claim': claim})


# --------------------------------------------------------------------------- Admin

@login_required(login_url='accounts:desk_login')
def claim_list(request):
    """AD-O1: the Admin's list of claims. It opens on the claims that are waiting."""
    if request.user.role != Role.ADMIN:
        raise PermissionDenied

    status = request.GET.get('status', 'pending')
    claims = Claim.objects.select_related('found_item', 'user')
    if status in Claim.Status.values:                 # ignore anything that is not a real status
        claims = claims.filter(status=status)
    page = Paginator(claims, 15).get_page(request.GET.get('page'))
    return render(request, 'claims/desk_claim_list.html',
                  {'page': page, 'status': status, 'statuses': Claim.Status.choices})


@login_required(login_url='accounts:desk_login')
def verify_claim(request, claim_id):
    """
    AD-P4: the Admin verifies a claim.
    The page shows what the claimant said beside the private details (AD-O3).
    The three buttons are Approve (AD-P5), Reject (AD-P6) and Ask more (AD-P7).
    """
    if request.user.role != Role.ADMIN:
        raise PermissionDenied

    claim = get_object_or_404(
        Claim.objects.select_related('user', 'found_item__verification_detail', 'decided_by'), pk=claim_id)
    item = claim.found_item

    if request.method == 'POST':
        form = DecisionForm(request.POST)
        decision = request.POST.get('decision')       # which of the three buttons was pressed

        # NFR-04: a claim that already has a final decision can never be decided again.
        if not claim.is_open:
            messages.error(request, 'This claim already has a final decision. It cannot be changed.')
            return redirect('claims:desk_verify', claim_id=claim.pk)

        # An item that has left the desk cannot be given to anybody.
        if decision == 'approve' and item.status != FoundItem.Status.IN_CUSTODY:
            messages.error(request, 'This item is no longer in custody, so the claim cannot be approved.')
            return redirect('claims:desk_verify', claim_id=claim.pk)

        if form.is_valid() and decision in ('approve', 'reject', 'more'):
            reason = form.cleaned_data['reason']
            if decision == 'approve':
                closed_claims = approve_claim(claim, request.user, reason)
                for closed_claim in closed_claims:            # tell the other claimants too
                    send_claim_decision(closed_claim)
                messages.success(request, 'Claim approved. The claimant has been emailed to collect the item.')
            elif decision == 'reject':
                save_decision(claim, Claim.Status.REJECTED, request.user, reason)
                messages.success(request, 'Claim rejected. The claimant has been emailed.')
            else:
                save_decision(claim, Claim.Status.MORE_EVIDENCE, request.user, reason)
                messages.success(request, 'The claimant has been emailed and asked for more details.')
            send_claim_decision(claim)                        # EM-P3
            return redirect('claims:desk_list')
    else:
        form = DecisionForm()

    # AD-O2: does one of the claimant's own lost reports match this item? It helps the decision.
    claimant_match = Match.objects.filter(found_item=item, report__user=claim.user).order_by('rank').first()
    other_open_claims = Claim.objects.filter(found_item=item, status__in=['pending', 'more_evidence']).exclude(pk=claim.pk).count()

    return render(request, 'claims/desk_verify.html', {
        'claim': claim, 'item': item, 'form': form,
        'claimant_match': claimant_match, 'other_open_claims': other_open_claims})


def save_decision(claim, status, officer, reason):
    """AD-S3: stores the decision with the officer, the time and the reason (NFR-04)."""
    claim.status = status
    claim.decided_by = officer
    claim.reason = reason
    claim.decided_at = timezone.now()
    claim.save()


def approve_claim(claim, officer, reason):
    """
    AD-P5: approve a claim.
    Three things must happen together, or not at all (NFR-07), so they are in one transaction:
      1. the claim is approved,
      2. the item's status becomes Claimed, so it leaves the search and nobody else can claim it,
      3. any other open claims for the same item are closed. There can never be two approved
         claims for one item.
    Returns the claims that were closed, so their owners can be emailed.
    """
    item = claim.found_item
    with transaction.atomic():
        save_decision(claim, Claim.Status.APPROVED, officer, reason)

        item.status = FoundItem.Status.CLAIMED
        item.save()

        closed_claims = list(Claim.objects.filter(found_item=item, status__in=['pending', 'more_evidence'])
                             .select_related('user', 'found_item'))
        for other in closed_claims:
            save_decision(other, Claim.Status.CLOSED, officer, 'Another claim for this item was approved.')
    return closed_claims
