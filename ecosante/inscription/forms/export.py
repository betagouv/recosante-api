from ecosante.utils.form import RadioField, BaseForm
from wtforms import widgets


class FormExport(BaseForm):
    recommandations =  RadioField(
        'Choisir une recommandation préférée',
        choices=[],
        widget=widgets.ListWidget(prefix_label=False))