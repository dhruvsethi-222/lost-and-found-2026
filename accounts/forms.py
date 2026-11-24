"""
Forms for signing up and logging in.

A form does three jobs:
  1. it lists the fields shown on the page,
  2. it checks what was typed (validation),
  3. it turns good data into a saved record.
"""
import re

from django import forms
from django.conf import settings
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from core.forms import style_form

from .models import Role, User


def check_campus_email(email, allowed_endings):
    """
    NFR-01: only campus emails may sign up - if campus email endings are set in the .env file.
    If no endings are set (an empty list), any email may sign up; it must still be verified.
    Returns the email in small letters, or raises an error to show under the field.
    """
    email = email.strip().lower()
    ending = email.split('@')[-1]                 # the part after the @
    if allowed_endings and ending not in allowed_endings:
        raise ValidationError(f'Use your campus email ending in @{allowed_endings[0]}.')
    if User.objects.filter(email=email).exists():
        raise ValidationError('An account with this email already exists. Log in instead.')
    return email


def example_email(allowed_endings):
    """The grey example shown inside the email box."""
    if allowed_endings:
        return 'name@' + allowed_endings[0]
    return 'name@example.com'


class RegistrationForm(forms.ModelForm):
    """
    The parts of signing up that Students and Staff share: the two password boxes
    and the password checks. The two forms below add their own fields.
    """

    role = None      # each form below sets this; it is never read from the page

    password1 = forms.CharField(label='Password', strip=False,
                                widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
                                help_text='At least 8 characters, not only numbers.')
    password2 = forms.CharField(label='Confirm password', strip=False,
                                widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))

    class Meta:
        model = User
        fields = ['name', 'email']

    def clean(self):
        """Checks that need more than one field."""
        cleaned = super().clean()
        password1 = cleaned.get('password1')
        password2 = cleaned.get('password2')
        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'The two passwords do not match.')
        if password1:
            # Django's password rules (AUTH_PASSWORD_VALIDATORS in settings.py):
            # at least 8 characters, not a common password, not only numbers.
            trial_user = User(name=cleaned.get('name', ''), email=cleaned.get('email', ''))
            try:
                password_validation.validate_password(password1, trial_user)
            except ValidationError as error:
                self.add_error('password1', error)
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.role                                 # fixed by the form
        user.is_verified = False                              # until the email link is clicked
        user.set_password(self.cleaned_data['password1'])     # SY-P1: stores the hash only
        if commit:
            user.save()                                       # ST-S1 / SF-S1
        return user


class StudentRegistrationForm(RegistrationForm):
    """Student sign-up (ST-I1): name, student email, admission number, password."""

    role = Role.STUDENT

    class Meta:
        model = User
        fields = ['name', 'email', 'admission_no']
        labels = {'name': 'Full name', 'email': 'Student email', 'admission_no': 'Admission number'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # let Django build the form as usual
        self.fields['admission_no'].required = True
        # Hints for the browser, so most mistakes are caught before the form is sent.
        self.fields['admission_no'].widget.attrs.update({
            'pattern': r'\d{4,8}', 'inputmode': 'numeric',
            'title': 'Digits only, for example 227034', 'placeholder': 'e.g. 227034'})
        self.fields['name'].widget.attrs['placeholder'] = 'e.g. Jane Wanjiru'
        self.fields['email'].widget.attrs['placeholder'] = example_email(settings.STUDENT_EMAIL_DOMAINS)
        style_form(self)

    def clean_email(self):
        return check_campus_email(self.cleaned_data['email'], settings.STUDENT_EMAIL_DOMAINS)

    def clean_admission_no(self):
        value = self.cleaned_data['admission_no'].strip()
        if not re.fullmatch(r'\d{4,8}', value):               # 4 to 8 digits
            raise ValidationError('Use digits only, for example 227034.')
        return value


class StaffRegistrationForm(RegistrationForm):
    """Staff sign-up (SF-I1): name, staff email, staff ID, department, password."""

    role = Role.STAFF

    class Meta:
        model = User
        fields = ['name', 'email', 'staff_no', 'department']
        labels = {'name': 'Full name', 'email': 'Staff email', 'staff_no': 'Staff ID'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # let Django build the form as usual
        self.fields['staff_no'].required = True
        self.fields['department'].required = True
        self.fields['staff_no'].widget.attrs.update({
            'pattern': r'[A-Za-z0-9\-]{2,20}',
            'title': 'Letters and numbers, for example S1043', 'placeholder': 'e.g. S1043'})
        self.fields['email'].widget.attrs['placeholder'] = example_email(settings.STAFF_EMAIL_DOMAINS)
        style_form(self)

    def clean_email(self):
        return check_campus_email(self.cleaned_data['email'], settings.STAFF_EMAIL_DOMAINS)

    def clean_staff_no(self):
        value = self.cleaned_data['staff_no'].strip().upper()
        if not re.fullmatch(r'[A-Z0-9\-]{2,20}', value):      # 2 to 20 letters, numbers or dashes
            raise ValidationError('Use letters and numbers only, for example S1043.')
        if User.objects.filter(staff_no=value).exists():
            raise ValidationError('An account with this staff ID already exists.')
        return value


class CampusLoginForm(AuthenticationForm):
    """
    Log in for Students and Staff (ST-P2, SF-P2).
    AuthenticationForm is Django's ready-made log-in form: it checks the email and
    password. We add two more checks in confirm_login_allowed().
    """

    username = forms.EmailField(label='Email',
                                widget=forms.EmailInput(attrs={'autofocus': True, 'autocomplete': 'email'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # let Django build the form as usual
        style_form(self)

    def confirm_login_allowed(self, user):
        """Django calls this after the email and password were found to be correct."""
        super().confirm_login_allowed(user)       # refuses switched-off accounts
        if user.role == Role.ADMIN:
            raise ValidationError('Security officers log in on the Security desk log-in page.')
        if not user.is_verified:
            raise ValidationError('Your email is not verified yet. Open the link we emailed you, then log in.')


class DeskLoginForm(AuthenticationForm):
    """Log in for the Admin (AD-I1, AD-P1), on its own page."""

    username = forms.EmailField(label='Email',
                                widget=forms.EmailInput(attrs={'autofocus': True, 'autocomplete': 'email'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # let Django build the form as usual
        style_form(self)

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if user.role != Role.ADMIN:
            raise ValidationError('This page is for security officers. '
                                  'Students and Staff log in on the main log-in page.')


class ResendVerificationForm(forms.Form):
    """One box: the email to send a new verification link to."""

    email = forms.EmailField(label='Your campus email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # let Django build the form as usual
        style_form(self)
