from jinja2.nodes import Mul
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
        choices=[('bonne', 'bon à dégradé'), ('mauvais', 'mauvais à extrêment mauvais')]
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
    raep = OuiNonField("Montrer en cas de RAEP > 0", validators=[validators.Optional(),])
    population = MultiCheckboxField(
        "Montrer aux populations suivantes :",
        choices=[
            ('enfants', 'Enfants'),
            ('personnes_sensibles', 'personnes sensibles/vulnérables à la QA'),
            ('population_generale', 'Population générale')
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
    autres_conditions = TextAreaField("Autres conditions")
    sources = TextAreaField("Sources")
    categorie = TextAreaField("Catégorie")
    objectif = TextAreaField("Objectif")

    def validate(self, extra_validators=[]):
        rv = super().validate(extra_validators=extra_validators)
        if not self.qa.data and not self.polluants.data and not self.raep.data:
            rv = False
            self.qa.errors = ["Vous devez remplir soit une qualité de l’air, soit un pic de pollution, sinon la recommandation n’est jamais envoyée"]
        return rv


class FormEdit(FormAdd):
    id = HiddenField("id")