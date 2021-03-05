from wtforms import widgets, SelectMultipleField, SelectField
from markupsafe import Markup
from flask_wtf import FlaskForm

class BaseForm(FlaskForm):
    class Meta:
        locales = ['fr_FR', 'fr']

        def get_translations(self, form):
            return super(FlaskForm.Meta, self).get_translations(form)


class BlankListWidget:
    def __init__(self, prefix_label=True, class_labels=None):
        self.prefix_label = prefix_label
        self.class_labels = class_labels

    def __call__(self, field, **kwargs):
        kwargs.setdefault("id", field.id)
        html = []
        for subfield in field:
            if self.prefix_label:
                html.append(f"{subfield.label(class_=self.class_labels)} {subfield()}")
            else:
                html.append(f"{subfield()} {subfield.label(class_=self.class_labels)}")
        return Markup("".join(html))


class AutocompleteInputWidget(widgets.TextInput):
    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('type', self.input_type)
        if 'value' not in kwargs:
            kwargs['value'] = field._value()
        if 'required' not in kwargs and 'required' in getattr(field, 'flags', []):
            kwargs['required'] = True
        html_params = self.html_params(name=field.name, **kwargs)
        class_ = kwargs.get('class_')
        return Markup(f'<div class="{class_}" id="{field.name}"><input class="autocomplete-input" {html_params}><ul class="autocomplete-result-list"></ul></div>')

class MultiCheckboxField(SelectMultipleField):
    widget = BlankListWidget(prefix_label=False, class_labels="label-inline")
    option_widget = widgets.CheckboxInput()


class RadioField(SelectField):
    widget = BlankListWidget(prefix_label=False, class_labels="label-inline")
    option_widget = widgets.RadioInput()

def coerce(value):
    if value is None:
        return value
    if type(value) == str:
        return value.lower() == 'oui' or value.lower() == 'true'
    if type(value) == bool:
        return value
    return False

class OuiNonField(RadioField):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args, 
            **{
                **kwargs,
                **{
                    "choices":[('oui', 'Oui'), ('non', 'Non')],
                    "coerce": coerce
                }
            }
        )

    def pre_validate(self, form):
        if self.data is None:
            return True
        return super().pre_validate(form)