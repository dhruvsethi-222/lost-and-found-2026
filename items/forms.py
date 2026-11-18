"""Forms for reporting items (Students, Staff) and recording found items (Admin)."""
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

from accounts.models import Role
from core.forms import style_form

from .models import FoundItem, ItemReport, VerificationDetail


class DateInput(forms.DateInput):
    """A date box that makes the browser show a calendar."""
    input_type = 'date'


def set_first_choice(field, text):
    """Replaces Django's '---------' at the top of a dropdown with e.g. 'Choose a category'."""
    real_choices = [choice for choice in field.choices if choice[0] != '']
    field.choices = [('', text)] + real_choices


class ItemReportForm(forms.ModelForm):
    """Report an item (ST-I2, SF-I2): type, category, description, date and place."""

    class Meta:
        model = ItemReport
        fields = ['type', 'category', 'description', 'date', 'place']
        widgets = {'type': forms.RadioSelect,
                   'date': DateInput(format='%Y-%m-%d'),
                   'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Colour, brand, marks'})}
        labels = {'type': 'What happened?', 'category': 'What is it?',
                  'description': 'Describe it', 'place': 'Where?'}

    def __init__(self, *args, role=Role.STUDENT, **kwargs):
        super().__init__(*args, **kwargs)
        # Staff see "Found in my office" (SF-P4); Students see "I found it" (ST-P4).
        if role == Role.STAFF:
            found_label = 'Found in my office'
            self.fields['place'].label = 'Office / hall or place'
        else:
            found_label = 'I found it'
        self.fields['type'].choices = [('lost', 'I lost it'), ('found', found_label)]
        set_first_choice(self.fields['category'], 'Choose a category')
        set_first_choice(self.fields['place'], 'Choose a place')
        # The calendar does not offer dates after today (NFR-03).
        self.fields['date'].widget.attrs['max'] = timezone.localdate().isoformat()
        style_form(self)


class FoundItemForm(forms.ModelForm):
    """The public part of a found item, entered by the Admin (AD-I2)."""

    class Meta:
        model = FoundItem
        fields = ['category', 'description', 'place', 'date_found', 'photo', 'handed_in_report']
        widgets = {'date_found': DateInput(format='%Y-%m-%d'),
                   'description': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Colour, brand'})}
        labels = {'category': 'What is it?', 'description': 'Describe it', 'place': 'Where was it found?',
                  'date_found': 'Date found', 'photo': 'Photo',
                  'handed_in_report': 'Was it reported as found by a Student or Staff member?'}
        help_texts = {'handed_in_report': 'Optional. Choosing the report marks it as handed in.'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        set_first_choice(self.fields['category'], 'Choose a category')
        set_first_choice(self.fields['place'], 'Choose a place')
        self.fields['date_found'].widget.attrs['max'] = timezone.localdate().isoformat()
        self.fields['photo'].widget.attrs['accept'] = 'image/*'      # the file picker shows images only
        # The dropdown lists only found reports that are not linked to an item yet.
        self.fields['handed_in_report'].queryset = (
            ItemReport.objects.filter(type='found', received_items__isnull=True).select_related('user'))
        self.fields['handed_in_report'].empty_label = 'No, it was brought straight to the desk'
        style_form(self)

    def clean_photo(self):
        """Refuses photos that are too big. Django has already checked it is a real image."""
        photo = self.cleaned_data['photo']
        if photo and photo.size > settings.MAX_PHOTO_MB * 1024 * 1024:
            raise ValidationError(f'The photo is too big. Use one under {settings.MAX_PHOTO_MB} MB.')
        return photo


class VerificationDetailForm(forms.ModelForm):
    """The private part, entered by the Admin (AD-I3): serial number, marks, contents."""

    class Meta:
        model = VerificationDetail
        fields = ['serial_no', 'marks', 'contents']
        widgets = {'marks': forms.Textarea(attrs={'rows': 2}),
                   'contents': forms.Textarea(attrs={'rows': 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form(self)

    def clean(self):
        """At least one private detail is needed, or there is nothing to check a claim against."""
        cleaned = super().clean()
        serial_no = (cleaned.get('serial_no') or '').strip()
        marks = (cleaned.get('marks') or '').strip()
        contents = (cleaned.get('contents') or '').strip()
        if not serial_no and not marks and not contents:
            raise ValidationError('Enter at least one private detail. Claims are checked against these.')
        return cleaned


class DisposeForm(forms.Form):
    """AD-P9: the Admin must say how the item was disposed of (NFR-04)."""

    reason = forms.CharField(label='How was it disposed of?', max_length=500,
                             widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'e.g. donated to the campus charity drive'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form(self)
