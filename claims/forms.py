"""Forms for claims: the claimant's answers and the Admin's reason."""
from django import forms

from core.forms import style_form


class ClaimForm(forms.Form):
    """ST-I3 / SF-I3: the claimant says what makes the item theirs."""

    answers = forms.CharField(
        label='What makes it yours?', max_length=2000,
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'e.g. what is inside it, a mark on it, the serial number'}),
        help_text='Give details only the owner would know. A security officer compares them with the item.')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # let Django build the form as usual
        style_form(self)


class MoreDetailsForm(forms.Form):
    """The claimant answers the Admin's question when more evidence was requested (AD-P7)."""

    details = forms.CharField(label='More details', max_length=1000,
                              widget=forms.Textarea(attrs={'rows': 3}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # let Django build the form as usual
        style_form(self)


class DecisionForm(forms.Form):
    """AD-I4: the Admin must give a reason for every decision."""

    reason = forms.CharField(label='Reason', max_length=500,
                             widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'e.g. details match'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # let Django build the form as usual
        style_form(self)
