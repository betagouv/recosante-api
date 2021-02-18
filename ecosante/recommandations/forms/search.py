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
    objectif = SelectField(
        "Objectif",
        choices = [
            (None, 'Tous les objectifs'),
            ("", "(sans)"),
            ("Améliorer l’air intérieur de votre logement", "Améliorer l’air intérieur de votre logement"),
            ("Contribuer à réduire la pollution de l’air", "Contribuer à réduire la pollution de l’air"),
            ("Profiter du plein air", "Profiter du plein air")
        ]
    )
