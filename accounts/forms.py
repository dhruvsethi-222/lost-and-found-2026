"""
Forms for registering and logging in.

A form does three jobs: it lists the fields shown on the page, it checks what was
typed (validation), and it turns good data into a saved record.
"""
import re

from django import forms
from django.conf import settings
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from core.forms import BootstrapFormMixin

from .models import Role, User


class RegistrationForm(BootstrapFormMixin, forms.ModelForm):
    """What Student and Staff registration share (ST-I1, SF-I1). Never creates an Admin."""

    role = None                 # set by the two forms below
    email_domains_setting = None

    password1 = forms.CharField(label='Password', strip=False,
                                widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
                                help_text='At least 8 characters, not only numbers.')
    password2 = forms.CharField(label='Confirm password', strip=False,
                                widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))

    class Meta:
        model = User
        fields = ['name', 'email']
        labels = {'name': 'Full name'}

    def allowed_domains(self):
        return getattr(settings, self.email_domains_setting)

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        domain = email.rsplit('@', 1)[-1]
        if domain not in self.allowed_domains():
            raise ValidationError(f'Use your campus email ending in @{self.allowed_domains()[0]}.')
        if User.objects.filter(email=email).exists():
            raise ValidationError('An account with this email already exists. Log in instead.')
        return email

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get('password1'), cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', 'The two passwords do not match.')
        if p1:
            # Django's password rules (settings.AUTH_PASSWORD_VALIDATORS)
            trial = User(name=cleaned.get('name', ''), email=cleaned.get('email', ''))
            try:
                password_validation.validate_password(p1, trial)
            except ValidationError as error:
                self.add_error('password1', error)
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.role                     # fixed by the form, never taken from the page
        user.is_verified = False                  # stays False until the email link is clicked
        user.set_password(self.cleaned_data['password1'])   # stores the hash only
        if commit:
            user.save()
        return user


class StudentRegistrationForm(RegistrationForm):
    role = Role.STUDENT
    email_domains_setting = 'STUDENT_EMAIL_DOMAINS'

    class Meta(RegistrationForm.Meta):
        fields = ['name', 'email', 'admission_no']
        labels = {'name': 'Full name', 'email': 'Student email', 'admission_no': 'Admission number'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['admission_no'].required = True
        self.fields['admission_no'].widget.attrs.update({'pattern': r'\d{4,8}', 'inputmode': 'numeric',
                                                         'title': 'Digits only, for example 227034'})
        self.fields['email'].widget.attrs['placeholder'] = f'name@{self.allowed_domains()[0]}'
        self.fields['name'].widget.attrs['placeholder'] = 'e.g. Jane Wanjiru'
        self.fields['admission_no'].widget.attrs['placeholder'] = 'e.g. 227034'

    def clean_admission_no(self):
        value = self.cleaned_data['admission_no'].strip()
        if not re.fullmatch(r'\d{4,8}', value):
            raise ValidationError('Use digits only, for example 227034.')
        return value


class StaffRegistrationForm(RegistrationForm):
    role = Role.STAFF
    email_domains_setting = 'STAFF_EMAIL_DOMAINS'

    class Meta(RegistrationForm.Meta):
        fields = ['name', 'email', 'staff_no', 'department']
        labels = {'name': 'Full name', 'email': 'Staff email', 'staff_no': 'Staff ID'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['staff_no'].required = True
        self.fields['department'].required = True
        self.fields['staff_no'].widget.attrs.update({'pattern': r'[A-Za-z0-9\-]{2,20}',
                                                     'title': 'Letters and numbers, for example S1043'})
        self.fields['email'].widget.attrs['placeholder'] = f'name@{self.allowed_domains()[0]}'
        self.fields['staff_no'].widget.attrs['placeholder'] = 'e.g. S1043'

    def clean_staff_no(self):
        value = self.cleaned_data['staff_no'].strip().upper()
        if not re.fullmatch(r'[A-Z0-9\-]{2,20}', value):
            raise ValidationError('Use letters and numbers only, for example S1043.')
        if User.objects.filter(staff_no=value).exists():
            raise ValidationError('An account with this staff ID already exists.')
        return value


class CampusLoginForm(BootstrapFormMixin, AuthenticationForm):
    """Log in for Students and Staff (ST-P2, SF-P2). Refused until the email is verified."""

    allowed_roles = (Role.STUDENT, Role.STAFF)
    wrong_page_message = 'Security officers log in on the Security desk log-in page.'

    username = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'autofocus': True, 'autocomplete': 'email'}))

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)       # refuses switched-off accounts
        if user.role not in self.allowed_roles:
            raise ValidationError(self.wrong_page_message, code='wrong_page')
        if not user.is_verified:
            raise ValidationError('Your email is not verified yet. Open the link we emailed you, then log in.',
                                  code='unverified')


class DeskLoginForm(CampusLoginForm):
    """Log in for the Admin (AD-P1), on its own page."""

    allowed_roles = (Role.ADMIN,)
    wrong_page_message = 'This page is for security officers. Students and Staff log in on the main log-in page.'


class ResendVerificationForm(BootstrapFormMixin, forms.Form):
    email = forms.EmailField(label='Your campus email')
