"""The search form: a text box and two dropdowns. Nothing in it is required."""
from django import forms

from core.forms import style_form
from items.choices import Category, Place


class SearchForm(forms.Form):
    q = forms.CharField(label='Search', required=False, max_length=100,
                        widget=forms.TextInput(attrs={'placeholder': 'e.g. black wallet', 'type': 'search'}))
    category = forms.ChoiceField(label='Category', required=False,
                                 choices=[('', 'Any category')] + list(Category.choices))
    place = forms.ChoiceField(label='Place', required=False,
                              choices=[('', 'Any place')] + list(Place.choices))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form(self)
