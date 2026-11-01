from django import forms


class FormControlMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                css_class = "form-check-input"
            elif isinstance(widget, forms.Select):
                css_class = "form-select"
            elif isinstance(widget, (forms.widgets.Input, forms.Textarea)):
                css_class = "form-control"
            else:
                continue

            classes = widget.attrs.get("class", "").split()
            if css_class not in classes:
                classes.append(css_class)
            widget.attrs["class"] = " ".join(classes)
