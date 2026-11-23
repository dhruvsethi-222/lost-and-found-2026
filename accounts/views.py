"""
Pages for accounts. A "view" is a function that receives the browser's request
and returns a page.

  /accounts/register/              Student sign-up
  /accounts/register/staff/        Staff sign-up
  /accounts/verification-sent/     "Check your email"
  /accounts/verify/<id>/<token>/   the link inside the verification email
  /accounts/resend-verification/   send the link again
  /accounts/desk/                  Admin: manage Student and Staff accounts (AD-P10)
  /accounts/desk/<id>/switch/      Admin: switch an account off or back on
  /accounts/desk/<id>/verify/      Admin: mark an email as verified by hand

Log in and log out use Django's ready-made pages; see urls.py.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import urlsafe_base64_decode

from .emails import send_verification_email
from .forms import ResendVerificationForm, StaffRegistrationForm, StudentRegistrationForm
from .models import Role, User


def register(request, role):
    """Sign up as a Student (ST-P1) or as Staff (SF-P1). Nobody can sign up as an Admin."""
    # Somebody who is already logged in does not need to sign up.
    if request.user.is_authenticated:
        return redirect('core:after_login')

    # Pick the form for this kind of account. `role` comes from urls.py.
    if role == Role.STAFF:
        form_class = StaffRegistrationForm
    else:
        form_class = StudentRegistrationForm

    if request.method == 'POST':                      # the form was sent
        form = form_class(request.POST)
        if form.is_valid():
            user = form.save()                        # ST-S1 / SF-S1: saved, not yet verified
            send_verification_email(request, user)    # ST-O1 / SF-O1
            request.session['verify_email'] = user.email      # remembered for the next page
            return redirect('accounts:verification_sent')
    else:                                             # the page was just opened
        form = form_class()
    return render(request, 'accounts/register.html', {'form': form, 'role': role})


def verification_sent(request):
    """The "Check your email" page."""
    return render(request, 'accounts/verification_sent.html',
                  {'email': request.session.get('verify_email')})


def verify_email(request, uidb64, token):
    """The page the email link opens. It checks the link and marks the account as verified."""
    # 1. Find the account. The first part of the link is the account id.
    try:
        account_id = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=account_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    # 2. No such account: the link is wrong.
    if user is None:
        return render(request, 'accounts/verify_failed.html', status=400)

    # 3. Already verified: the link has been used, nothing more to do.
    if user.is_verified:
        messages.info(request, 'This account is already verified. Log in below.')
        return redirect('accounts:login')

    # 4. Check the secret code. It fails if it was changed or is older than 3 days.
    if default_token_generator.check_token(user, token):
        user.is_verified = True
        user.save()
        messages.success(request, 'Your email is verified. You can log in now.')
        return redirect('accounts:login')

    return render(request, 'accounts/verify_failed.html', status=400)


def resend_verification(request):
    """
    Sends a fresh link. The answer is the same whether or not the email has an
    account, so nobody can use this page to find out who is registered (privacy).
    """
    if request.method == 'POST':
        form = ResendVerificationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].lower()
            user = User.objects.filter(email=email, is_verified=False).exclude(role=Role.ADMIN).first()
            if user:
                send_verification_email(request, user)
            request.session['verify_email'] = email
            return redirect('accounts:verification_sent')
    else:
        form = ResendVerificationForm()
    return render(request, 'accounts/resend.html', {'form': form})


# --------------------------------------------------------------------------- Admin: manage accounts

@login_required(login_url='accounts:desk_login')
def account_list(request):
    """
    AD-P10: the Admin's list of Student and Staff accounts, 15 on a page.
    Search by name, email, admission number or staff ID, and filter by role.
    Admin accounts are not listed: only the system owner creates them (createofficer).
    """
    if request.user.role != Role.ADMIN:
        raise PermissionDenied

    accounts = User.objects.filter(role__in=[Role.STUDENT, Role.STAFF]).order_by('name')
    words = request.GET.get('q', '').strip()
    if words:
        # Q(...) | Q(...) means "this OR that": the words can be in the name, email or ID number
        accounts = accounts.filter(Q(name__icontains=words) | Q(email__icontains=words)
                                   | Q(admission_no__icontains=words) | Q(staff_no__icontains=words))
    role = request.GET.get('role', '')
    if role in (Role.STUDENT, Role.STAFF):
        accounts = accounts.filter(role=role)

    page = Paginator(accounts, 15).get_page(request.GET.get('page'))
    return render(request, 'accounts/desk_accounts.html',
                  {'page': page, 'q': words, 'role': role, 'extra': f'q={words}&role={role}'})


def student_or_staff_account(pk):
    """Finds a Student or Staff account. Admin accounts give "Page not found", so they cannot be changed here."""
    return get_object_or_404(User, pk=pk, role__in=[Role.STUDENT, Role.STAFF])


@login_required(login_url='accounts:desk_login')
def account_switch(request, pk):
    """
    Switches an account off, or back on. Accounts are never deleted, so their reports
    and claims stay on record. A switched-off account cannot log in.
    """
    if request.user.role != Role.ADMIN:
        raise PermissionDenied
    if request.method != 'POST':                      # only the button on the list can do this
        return redirect('accounts:desk_accounts')

    account = student_or_staff_account(pk)
    account.is_active = not account.is_active
    account.save()
    if account.is_active:
        messages.success(request, f'{account.name} can log in again.')
    else:
        messages.success(request, f'{account.name} is switched off and can no longer log in.')
    return redirect('accounts:desk_accounts')


@login_required(login_url='accounts:desk_login')
def account_verify(request, pk):
    """Marks an email as verified by hand, for someone who came to the desk with their ID card."""
    if request.user.role != Role.ADMIN:
        raise PermissionDenied
    if request.method != 'POST':
        return redirect('accounts:desk_accounts')

    account = student_or_staff_account(pk)
    account.is_verified = True
    account.save()
    messages.success(request, f'{account.name} is now verified and can log in.')
    return redirect('accounts:desk_accounts')
