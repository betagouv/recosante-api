from jinja2.nodes import Mul
from wtforms.fields.core import SelectField
from ecosante.utils.form import RadioField, BaseForm, OuiNonField, MultiCheckboxField
from wtforms import TextAreaField, HiddenField, validators


class FormAdd(BaseForm):
    status = RadioField(
        "Statut",
        choices=[
            ('draft', 'Brouillon'),
            ('published', 'Publiée')
        ]
    )
    recommandation = TextAreaField('Recommandation')
    precisions = TextAreaField('Précisions')
    recommandation_format_SMS = TextAreaField('Recommandation format SMS')
    type_ = RadioField(
        'Type',
        choices=[
            ("generale", "Indice ATMO"),
            ("episode_pollution", "Épisode de pollution"),
            ("pollens", "Pollens")
        ]
    )
    saison = MultiCheckboxField("Montrer la recommandation que durant les saisons :",
        choices=[
            ('hiver', 'Hiver'),
            ('printemps', 'Printemps'),
            ('ete', 'Été'),
            ('automne', 'Automne'),
        ]
    )
    qa = MultiCheckboxField(
        "Montrer en cas d’indice ATMO :",
        choices=[('bonne', 'bon à moyen'), ('mauvaise', 'dégradé à extrêment mauvais')]
    )
    polluants = MultiCheckboxField(
        "Montrer en cas d’épisode de pollution :",
        description="seuil «information ou recommandation» ou «alerte»",
        choices=[
            ('ozone', 'à l’ozone'),
            ('dioxyde_azote', 'au dioxyde d’azote'),
            ('dioxyde_soufre', 'au dioxyde de soufre'),
            ('particules_fines', 'aux particules fines')
        ]
    )
    min_raep = SelectField(
        'Montrer à partir d’un un RAEP de',
        choices=[(None, "--"), (1, "1"), (4, "4")]
    )
    personne_allergique = OuiNonField("Montre aux personnes allergiques")
    population = MultiCheckboxField(
        "Montrer aux populations suivantes :",
        choices=[
            ('enfants', 'Enfants'),
            ('personnes_sensibles', 'personnes sensibles/vulnérables à la QA'),
            ('autres', 'Autres')
        ]
    )
    activites = MultiCheckboxField(
        "Montrer pour les activités suivantes :",
        choices=[
            ('menage', 'Ménage'),
            ('bricolage', 'Bricolage'),
            ('jardinage', 'Jardinage'),
            ('activite_physique', 'Activité physique')
        ]
    )
    deplacement = MultiCheckboxField(
        "Montrer pour les modes de déplacement suivants :",
        choices=[
            ("velo_trott_skate", "Vélo"),
            ("transport_en_commun", "Transport en commun"),
            ("voiture", "Voiture")
        ]
    )
    chauffage_a_bois = OuiNonField("Chauffage à bois")
    animal_de_compagnie = OuiNonField("Animal de compagnie")
    autres_conditions = TextAreaField("Autres conditions")
    sources = TextAreaField("Sources")
    categorie = TextAreaField("Catégorie")
    objectif = SelectField(
        "Objectif",
        choices=[
            ("", "(sans)"),
            ("Améliorer l’air intérieur de votre logement", "Améliorer l’air intérieur de votre logement"),
            ("Contribuer à réduire la pollution de l’air", "Contribuer à réduire la pollution de l’air"),
            ("Profiter du plein air", "Profiter du plein air")
        ]
    )

    def validate(self, extra_validators=[]):
        rv = super().validate(extra_validators=extra_validators)
        if not self.qa.data and not self.polluants.data and self.type_.data == "generale":# and not self.raep.data:
            rv = False
            self.qa.errors = ["Vous devez remplir soit une qualité de l’air, soit un pic de pollution, sinon la recommandation n’est jamais envoyée"]
        return rv


class FormEdit(FormAdd):
    id = HiddenField("id")