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
    saison = SelectField("Montrer la recommandation durant la saison :",
        choices=[
            ('', 'Toutes les saisons'),
            ('hiver', 'Hiver'),
            ('printemps', 'Printemps'),
            ('ete', 'Été'),
            ('automne', 'Automne'),
        ]
    )
    qa = MultiCheckboxField(
        "Montrer en cas de qualité de l’air :",
        choices=[('bonne', 'Bonne'), ('mauvaise', 'Mauvaise')]
    )
    polluants = MultiCheckboxField(
        "Montrer en cas de pic de :",
        choices=[
            ('ozone', 'Ozone'),
            ('dioxyde_azote', 'Doxyde d’azote'),
            ('dioxyde_soufre', 'Dioxyde de soufre'),
            ('particules_fines', 'Particules fines')
        ]
    )
    population = MultiCheckboxField(
        "Montrer à :",
        choices=[
            ('allergies', 'Personnes allergiques'),
            ('enfants', 'Enfants'),
            ('personnes_sensibles', 'Personnes sensibles'),
            ('population_generale', 'Population générale')
        ]
    )
    episode_pollution = OuiNonField("Montrer en cas de pic de pollution ?")
    menage = OuiNonField("Ménage")
    bricolage = OuiNonField("Bricolage")
    chauffage_a_bois = OuiNonField("Chauffage à bois")
    jardinage = OuiNonField("Jardinage")
    balcon_terasse = OuiNonField("Balcon terrasse")
    velo_trott_skate = OuiNonField("Vélo / trottinette / skate")
    transport_en_commun = OuiNonField("Transport en commun ?")
    voiture = OuiNonField("Voiture")
    activite_physique = OuiNonField("Activité physique")
    autres_conditions = TextAreaField("Autres conditions")
    sources = TextAreaField("Sources")
    categorie = TextAreaField("Catégorie")
    objectif = TextAreaField("Objectif")


class FormEdit(FormAdd):
    id = HiddenField("id")