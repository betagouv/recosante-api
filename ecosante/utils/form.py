from wtforms import widgets, SelectMultipleField, SelectField, IntegerField as BaseIntegerField
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

class OuiNonField(SelectMultipleField):
    option_widget = widgets.RadioInput()
    widget = BlankListWidget(prefix_label=False, class_labels="label-inline")

    def __init__(self, *args, **kwargs):
        kwargs['choices']= [('oui', 'Oui'), ('non', 'Non')]
        super().__init__(*args, **kwargs)

    def process_data(self, value):
        if value == True:
            self.data = ['oui']
        elif value == False:
            self.data = ['non']
        else:
            self.data = []

    def process_formdata(self, valuelist):
        if len(valuelist) == 1:
            self.data = valuelist[0].lower() in ('oui', 'true')
        else:
            self.data = None

    def pre_validate(self, form):
        if self.data not in (True, False, None):
            raise ValueError(self.gettext("'%(value)s' is not a valid choice for this field") % dict(value=d))

class IntegerField(BaseIntegerField):
    def process_formdata(self, valuelist):
        if valuelist and valuelist[0]:
            super().process_formdata(valuelist)

def coerce_int(i):
    if i is None:
        return i
    elif i == "":
        return None
    else:
        return int(i)