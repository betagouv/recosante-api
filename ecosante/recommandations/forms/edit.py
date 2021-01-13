from jinja2.nodes import Mul
from ecosante.utils.form import RadioField, BaseForm, OuiNonField, MultiCheckboxField
from wtforms import TextAreaField, HiddenField, SelectField


class FormAdd(BaseForm):
    recommandabilite = RadioField(
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
    population = MultiCheckboxField(
        "Montrer aux populations suivantes :",
        choices=[
            ('allergies', 'Personnes allergiques'),
            ('enfants', 'Enfants'),
            ('personnes_sensibles', 'Personnes à pathologie respiratoire'),
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
    chauffage_a_bois = OuiNonField("Chauffage à bois")
    velo_trott_skate = OuiNonField("Vélo / trottinette / skate")
    transport_en_commun = OuiNonField("Transport en commun ?")
    voiture = OuiNonField("Voiture")
    autres_conditions = TextAreaField("Autres conditions")
    sources = TextAreaField("Sources")
    categorie = TextAreaField("Catégorie")
    objectif = TextAreaField("Objectif")


class FormEdit(FormAdd):
    id = HiddenField("id")