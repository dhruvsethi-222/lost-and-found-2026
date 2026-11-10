"""
Views for accounts. A view receives the browser's request and returns a page.
"""
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode

from .emails import send_verification_email
from .forms import (CampusLoginForm, DeskLoginForm, ResendVerificationForm, StaffRegistrationForm,
                    StudentRegistrationForm)
from .models import Role, User
from .tokens import verification_token

REGISTRATION_FORMS = {Role.STUDENT: StudentRegistrationForm, Role.STAFF: StaffRegistrationForm}


def register(request, role):
    """Sign up as a Student or as Staff (ST-P1, SF-P1). There is no way to sign up as an Admin."""
    if request.user.is_authenticated:
        return redirect('core:after_login')
    form_class = REGISTRATION_FORMS[role]
    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            user = form.save()                       # ST-S1 / SF-S1: account stored, not verified
            send_verification_email(request, user)   # ST-O1 / SF-O1: email with the link
            request.session['verify_email'] = user.email
            return redirect('accounts:verification_sent')
    else:
        form = form_class()
    return render(request, 'accounts/register.html', {'form': form, 'role': role})


def verification_sent(request):
    return render(request, 'accounts/verification_sent.html', {'email': request.session.get('verify_email')})


def verify_email(request, uidb64, token):
    """The page the email link opens: checks the token and sets the account verified."""
    try:
        user = User.objects.get(pk=force_str(urlsafe_base64_decode(uidb64)))
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and verification_token.check_token(user, token):
        user.is_verified = True
        user.save(update_fields=['is_verified'])
        messages.success(request, 'Your email is verified. You can log in now.')
        return redirect('accounts:login')
    if user is not None and user.is_verified:
        messages.info(request, 'This account is already verified. Log in below.')
        return redirect('accounts:login')
    return render(request, 'accounts/verify_failed.html', status=400)


def resend_verification(request):
    """Sends a fresh link. The answer is the same whether or not the email exists (privacy)."""
    form = ResendVerificationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = User.objects.filter(email=form.cleaned_data['email'].lower(), is_verified=False,
                                   role__in=[Role.STUDENT, Role.STAFF]).first()
        if user:
            send_verification_email(request, user)
        request.session['verify_email'] = form.cleaned_data['email'].lower()
        return redirect('accounts:verification_sent')
    return render(request, 'accounts/resend.html', {'form': form})


class CampusLoginView(LoginView):
    """Log in for Students and Staff."""
    template_name = 'accounts/login.html'
    authentication_form = CampusLoginForm
    redirect_authenticated_user = True


class DeskLoginView(LoginView):
    """Separate log-in page for the Admin (security officer)."""
    template_name = 'accounts/desk_login.html'
    authentication_form = DeskLoginForm
    redirect_authenticated_user = True
