from ecosante.utils.form import BaseForm, MultiCheckboxField
from wtforms.widgets.html5 import SearchInput
from wtforms.fields import StringField, SelectField
from markupsafe import Markup
from ..models import RECOMMANDATION_FILTERS

class FormSearch(BaseForm):
    search = StringField("Recherche", widget=SearchInput())
    categories = MultiCheckboxField(
        'Catégories',
        choices=[
            (filter[0], Markup(f'<abbr title="{filter[2]}">{filter[1]}</abbr>'))
            for filter in RECOMMANDATION_FILTERS
        ]
    )
    status = SelectField(
        "Statut",
        choices=[
            ('published', 'Publiée'),
            ('draft', 'Brouillon'),
            ('', 'Toutes les recommandations')
        ],
        default='published'
    )
