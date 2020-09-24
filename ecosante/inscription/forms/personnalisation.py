from ecosante.utils.form import MultiCheckboxField, OuiNonField, BaseForm

class FormPersonnalisation(BaseForm):
    deplacement = MultiCheckboxField(
        'Quel(s) moyen(s) de transport utilisez-vous principalement pour vos déplacements ?',
        choices={
            ('velo', 'Vélo'),
            ('tec', 'Transport en commun'),
            ('voiture', 'Voiture')
        }
    )
    activites = MultiCheckboxField(
        'Pratiquez-vous au moins une fois par semaine les activités suivantes ?',
        choices=[
            ('jardinage', 'Jardinage'),
            ('bricolage', 'Bricolage'),
            ('menage', 'Ménage'),
            ('sport', 'Activité sportive')
        ]
    )
    enfants = OuiNonField('Vivez-vous avec des enfants ?')
    pathologie_respiratoire = OuiNonField('Vivez-vous avec une pathologie respiratoire ?')
    allergie_pollen = OuiNonField('Êtes-vous allergique aux pollens ?')
    fumeur = OuiNonField('Êtes-vous fumeur.euse ?')