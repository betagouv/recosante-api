from jinja2.nodes import Mul
from ecosante.utils.form import RadioField, BaseForm, OuiNonField, MultiCheckboxField
from wtforms import TextAreaField, HiddenField, SelectField


class FormAdd(BaseForm):
    recommandabilite = RadioField(
        "Recommandabilité",
        choices=[
            ('Non-utilisable', 'Non-utilisable'),
            ('Utilisable', 'Utilisable')
        ]
    )
    recommandation = TextAreaField('Recommandation')
    precisions = TextAreaField('Précisions')
    recommandation_format_SMS = TextAreaField('Recommandation format SMS')
    saison = SelectField("Montrer en",
        choices=[
            ('', ''),
            ('ete', 'Été'),
            ('automne', 'Automne'),
            ('hiver', 'Hiver')
        ]
    )
    qa = MultiCheckboxField(
        "Montrer en cas de qualité de l’air :",
        choices=[('bonne', 'Bonne'), ('moyenne', 'Moyenne'), ('mauvaise', 'Mauvaise')]
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