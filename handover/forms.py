"""The hand-over form: one box for the collector's ID number (AD-I5)."""
from django import forms
from django.core.exceptions import ValidationError

from core.forms import style_form


class HandOverForm(forms.Form):
    collector_id = forms.CharField(
        label="Collector's ID number", max_length=30,
        widget=forms.TextInput(attrs={'placeholder': 'e.g. 227034', 'autocomplete': 'off'}),
        help_text='Type the number on the student or staff ID card the collector shows you.')

    def __init__(self, *args, claimant=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.claimant = claimant            # the person whose claim was approved
        style_form(self)

    def clean_collector_id(self):
        """The card shown must belong to the claimant, so nobody else can collect the item."""
        value = self.cleaned_data['collector_id'].strip().upper()
        expected = (self.claimant.admission_no or self.claimant.staff_no or '').upper()
        if value != expected:
            raise ValidationError("This ID does not match the claimant's ID. Only the claimant can collect the item.")
        return value
