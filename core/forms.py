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
