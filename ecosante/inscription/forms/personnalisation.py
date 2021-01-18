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
    pathologie_respiratoire = OuiNonField(
        'Êtes-vous une personne vulnérable ou sensible à la qualité de l’air ?',
        description="""
        <div id="definition-vulnerables" class="modal__backdrop">
            <div class="modal">
                <h4>Qu’est-ce qu’une population vulnérable ?</h4>
                <p>
                    La population des personnes vulnérables comprend les femmes enceintes, nourrissons et jeunes enfants, personnes de plus de 65 ans, personnes souffrant de pathologies cardiovasculaires, insuffisants cardiaques ou respiratoires, personnes asthmatiques.
                </p>
                <h4>Qu’est-ce qu’une population sensible ?</h4>
                <p>
                La population des personnes sensibles comprend les personnes se reconnaissant comme sensibles lors des pics de pollution et/ ou dont les symptômes apparaissent ou sont amplifiés lors des pics (par exemple : personnes diabétiques, personnes immunodéprimées, personnes souffrant d'affections neurologiques ou à risque cardiaque, respiratoire, infectieux).
                </p>
                <a href="#questionnaire" class="button">Fermer</a>
            </div>
        </div>
        <a href="#definition-vulnerables">Qu’est-ce qu’une personne sensible ou vulnérable ?</a>
        """
    )
    allergie_pollen = OuiNonField('Êtes-vous allergique aux pollens ?')
    fumeur = OuiNonField('Êtes-vous fumeur.euse ?')