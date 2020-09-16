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

class MultiCheckboxField(SelectMultipleField):
    widget = BlankListWidget(prefix_label=False, class_labels="label-inline")
    option_widget = widgets.CheckboxInput()


class RadioField(SelectField):
    widget = BlankListWidget(prefix_label=False, class_labels="label-inline")
    option_widget = widgets.RadioInput()

def coerce(value):
    if value is None:
        return value
    return value == True or value == 'oui'

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
