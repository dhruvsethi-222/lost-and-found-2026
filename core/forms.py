"""Shared form helper: gives every field the Bootstrap look, so templates stay short."""
from django import forms


class BootstrapFormMixin:
    """Adds Bootstrap classes to every field and links each field to its error message."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, (forms.RadioSelect, forms.CheckboxSelectMultiple)):
                continue                                   # styled in the template
            if isinstance(widget, forms.CheckboxInput):
                css = 'form-check-input'
            elif isinstance(widget, forms.Select):
                css = 'form-select'
            else:
                css = 'form-control'
            widget.attrs['class'] = (widget.attrs.get('class', '') + ' ' + css).strip()
            # screen readers read the message under the field together with the field
            widget.attrs['aria-describedby'] = f'{self.add_prefix(name)}-message'

    def full_clean(self):
        """After checking, outline the fields that have a problem in red."""
        super().full_clean()
        for name in self.errors:
            if name in self.fields:
                widget = self.fields[name].widget
                widget.attrs['class'] = (widget.attrs.get('class', '') + ' is-invalid').strip()
