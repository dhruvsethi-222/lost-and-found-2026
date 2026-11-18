"""The form for a post or a reply: one text box."""
from django import forms

from core.forms import style_form


class PostForm(forms.Form):
    text = forms.CharField(label='Your post', max_length=280,
                           widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'e.g. Has anyone seen a blue umbrella near the library?'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form(self)
