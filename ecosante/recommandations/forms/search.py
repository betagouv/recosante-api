from ecosante.utils.form import BaseForm, MultiCheckboxField
from wtforms.widgets import SearchInput
from wtforms.fields import StringField, SelectField, SelectMultipleField
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
            ('hidden', 'Non publiée'),
            ('draft', 'Brouillon'),
            ('', 'Toutes les recommandations')
        ],
        default='published'
    )

    type = SelectField(
        "Type",
        choices = [
            (None, 'Tous les types'),
            ("indice_atmo", "Indice ATMO"),
            ("episode_pollution", "Épisode de pollution"),
            ("pollens", "Pollens"),
            ("radon", "Radon")
        ]
    )

    order = SelectField(
        "Ordre",
        choices=[
            ('random', 'Aléatoire'),
            ('id', 'Chronologique')
        ]
    )