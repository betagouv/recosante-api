from ecosante.utils.form import RadioField, BaseForm, OuiNonField
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
    qa_bonne = OuiNonField("Montrer en cas de qualité de l’air bonne ?")
    qa_moyenne = OuiNonField("Montrer en cas de qualité de l’air moyenne ?")
    qa_mauvaise = OuiNonField("Montrer en cas de qualité de l’air mauvaise ?")
    ozone = OuiNonField("Montrer en cas de pic d’ozone ?")
    particules_fines = OuiNonField("Montrer en cas de pollution aux particules fines ?")
    menage = OuiNonField("Ménage")
    bricolage = OuiNonField("Bricolage")
    chauffage_a_bois = OuiNonField("Chauffage à bois")
    jardinage = OuiNonField("Jardinage")
    balcon_terasse = OuiNonField("Balcon terrasse")
    velo_trott_skate = OuiNonField("Vélo / trottinette / skate")
    transport_en_commun = OuiNonField("Transport en commun ?")
    voiture = OuiNonField("Voiture")
    activite_physique = OuiNonField("Activité physique")
    allergies = OuiNonField("Allergies")
    enfants = OuiNonField("Enfants")
    personnes_sensibles = OuiNonField("Personnes sensibles")
    autres_conditions = TextAreaField("Autres conditions")
    sources = TextAreaField("Sources")
    categorie = TextAreaField("Catégorie")
    objectif = TextAreaField("Objectif")


class FormEdit(FormAdd):
    id = HiddenField("id")