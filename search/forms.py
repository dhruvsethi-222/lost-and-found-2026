from django import forms

from core.forms import BootstrapFormMixin
from items.choices import Category, Place


class SearchForm(BootstrapFormMixin, forms.Form):
    q = forms.CharField(label='Search', required=False, max_length=100,
                        widget=forms.TextInput(attrs={'placeholder': 'e.g. black wallet', 'type': 'search'}))
    category = forms.ChoiceField(label='Category', required=False,
                                 choices=[('', 'Any category')] + list(Category.choices))
    place = forms.ChoiceField(label='Place', required=False, choices=[('', 'Any place')] + list(Place.choices))
