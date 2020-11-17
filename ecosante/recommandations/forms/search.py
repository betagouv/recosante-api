from ecosante.utils.form import BaseForm, MultiCheckboxField
from wtforms.widgets.html5 import SearchInput
from wtforms.fields import StringField

class FormSearch(BaseForm):
    search = StringField("Recherche", widget=SearchInput())
    categories = MultiCheckboxField(
        'Catégories',
        choices=[
            ("qa_mauvaise", "☁"),
            ("menage", "🧹"),
            ("bricolage", "🔨"),
            ("chauffage_a_bois", "🔥"),
            ("jardinage", "🌳"),
            ("velo_trott_skate", "🚴"),
            ("transport_en_commun", "🚇"),
            ("voiture", "🚗"),
            ("activite_physique", "🏋"),
            ("allergies", "🤧"),
            ("enfants", "🧒"),
            ("personnes_sensibles", "🤓"),
            ("automne", "🍂"),
            ("hiver", "☃")
        ]
    )
