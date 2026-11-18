"""One shared helper for forms: gives every field the Bootstrap look."""
from django import forms


def style_form(form):
    """
    Adds the Bootstrap CSS class to every field of a form, so the templates stay short.
    Each form calls it once, at the end of its __init__.
    """
    for name, field in form.fields.items():
        widget = field.widget
        if isinstance(widget, forms.RadioSelect):
            continue                                   # radio buttons are styled in the template
        if isinstance(widget, forms.Select):
            css_class = 'form-select'                  # dropdown list
        else:
            css_class = 'form-control'                 # text box, date, file, password
        widget.attrs['class'] = css_class
        # Screen readers read the message under the field together with the field.
        widget.attrs['aria-describedby'] = f'{form.add_prefix(name)}-message'


class DateBox(forms.DateInput):
    """A date box that makes the browser show a calendar."""
    input_type = 'date'


class ReportPeriodForm(forms.Form):
    """The period the Admin's reports cover (AD-R1)."""

    date_from = forms.DateField(label='From', widget=DateBox(format='%Y-%m-%d'))
    date_to = forms.DateField(label='To', widget=DateBox(format='%Y-%m-%d'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form(self)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('date_from') and cleaned.get('date_to') and cleaned['date_from'] > cleaned['date_to']:
            raise forms.ValidationError('"From" must be on or before "To".')
        return cleaned
