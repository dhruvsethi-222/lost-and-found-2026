"""Forms for reporting items (Students, Staff) and recording found items (Admin)."""
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

from accounts.models import Role
from core.forms import BootstrapFormMixin

from .models import FoundItem, ItemReport, VerificationDetail


class DateInput(forms.DateInput):
    input_type = 'date'          # the browser shows a calendar


def first_choice(field, text):
    """Replaces Django's '---------' with 'Choose a ...', like the course forms."""
    field.choices = [('', text)] + [c for c in field.choices if c[0] != '']


class ItemReportForm(BootstrapFormMixin, forms.ModelForm):
    """Report an item (ST-I2, SF-I2). The two tab labels depend on who is reporting."""

    class Meta:
        model = ItemReport
        fields = ['type', 'category', 'description', 'date', 'place']
        widgets = {'type': forms.RadioSelect, 'date': DateInput(format='%Y-%m-%d'),
                   'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Colour, brand, marks'})}
        labels = {'type': 'What happened?', 'category': 'What is it?', 'description': 'Describe it',
                  'place': 'Where?'}

    def __init__(self, *args, role=Role.STUDENT, **kwargs):
        super().__init__(*args, **kwargs)
        found_label = 'Found in my office' if role == Role.STAFF else 'I found it'
        self.fields['type'].choices = [('lost', 'I lost it'), ('found', found_label)]
        first_choice(self.fields['category'], 'Choose a category')
        first_choice(self.fields['place'], 'Choose a place')
        if role == Role.STAFF:
            self.fields['place'].label = 'Office / hall or place'
        self.fields['date'].widget.attrs['max'] = timezone.localdate().isoformat()   # no future dates


class FoundItemForm(BootstrapFormMixin, forms.ModelForm):
    """The public part of a found item, entered by the Admin (AD-I2)."""

    class Meta:
        model = FoundItem
        fields = ['category', 'description', 'place', 'date_found', 'photo']
        widgets = {'date_found': DateInput(format='%Y-%m-%d'),
                   'description': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Colour, brand'})}
        labels = {'category': 'What is it?', 'description': 'Describe it', 'place': 'Where was it found?',
                  'date_found': 'Date found', 'photo': 'Photo'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        first_choice(self.fields['category'], 'Choose a category')
        first_choice(self.fields['place'], 'Choose a place')
        self.fields['date_found'].widget.attrs['max'] = timezone.localdate().isoformat()
        self.fields['photo'].widget.attrs['accept'] = 'image/*'

    def clean_photo(self):
        photo = self.cleaned_data['photo']
        if photo and photo.size > settings.MAX_PHOTO_MB * 1024 * 1024:
            raise ValidationError(f'The photo is too big. Use one under {settings.MAX_PHOTO_MB} MB.')
        return photo


class VerificationDetailForm(BootstrapFormMixin, forms.ModelForm):
    """The private part, entered by the Admin (AD-I3). At least one detail is needed to check claims later."""

    class Meta:
        model = VerificationDetail
        fields = ['serial_no', 'marks', 'contents']
        widgets = {'marks': forms.Textarea(attrs={'rows': 2}), 'contents': forms.Textarea(attrs={'rows': 2})}

    def clean(self):
        cleaned = super().clean()
        if not any((cleaned.get(f) or '').strip() for f in ('serial_no', 'marks', 'contents')):
            raise ValidationError('Enter at least one private detail. Claims are checked against these.')
        return cleaned
