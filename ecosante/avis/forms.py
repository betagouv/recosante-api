from ecosante.utils.form import RadioField, BaseForm, MultiCheckboxField, OuiNonField
from wtforms import validators, widgets, SelectField, TextAreaField
from wtforms.fields.html5 import EmailField
from wtforms.validators import ValidationError
from ecosante.inscription.models import Inscription

class Form(BaseForm):
    mail = EmailField(
        'Adresse email',
        [validators.InputRequired(), validators.Email()],
    )
    decouverte = MultiCheckboxField(
        'Sur les recommandations reçues pendant ces deux dernières semaines :',
        choices=[
            ('nouvelles', 'J’ai découvert de nouvelles recommandations'),
            ('rappel', "J'en connaissais déjà certaines, mais j'ai apprécié d'avoir un rappel"),
            ('applique_une', "J'ai appliqué au moins une recommandation"),
            ('rien_nouveau', "Je n'ai rien appris de nouveau")
        ],
        widget=widgets.ListWidget()
    )
    satisfaction_nombre_recommandation = OuiNonField(
        'Etes-vous satisfait.e du nombre de recommandations proposé dans chaque newsletter ?',
        choices=[
            (True, "Oui, une recommandation me suffit"),
            (False, "Non, je souhaiterais davantage de recommandations")
        ]
    )
    satisfaction_frequence = RadioField(
        'Etes-vous satisfait.e de la fréquence à laquelle vous recevez la newsletter Ecosanté ?',
        choices=[
            ('oui', "Oui, je souhaite continuer de recevoir la newsletter Ecosanté à cette fréquence"),
            ('moins_souvent', "Non, j'aimerais la recevoir moins souvent"),
            ('plus_souvent', "Non, j'aimerais la recevoir plus souvent")
        ],
        widget=widgets.ListWidget()
    )
    recommandabilite = SelectField(
        'Sur une échelle de 0 à 10, quelle est la probabilité que vous recommandiez Ecosanté à un proche ?',
        choices=[(0, '0 - Pas du tout probable')] + [(i, str(i)) for i in range(1, 10)] + [(10, '10 - Très probable')]
    )
    encore = OuiNonField(
        'Souhaitez-vous continuer à recevoir la newsletter Ecosanté ? En cliquant sur "oui", vous continuerez de recevoir la newsletter Ecosanté pendant les deux prochaines semaines. Cette question vous sera posée à nouveau à la fin des deux semaines.'
    )
    autres_thematiques = TextAreaField(
        "Si l'Equipe Ecosanté envisageait d'intégrer d'autres thématiques santé-environnement à la newsletter, la ou lesquelles vous intéresserai(en)t ?",
    )

    def validate_mail(form, field):
        inscription = Inscription.query.filter_by(mail=field.data).first()
        if not inscription:
            raise ValidationError("Nous ne connaissons pas cette adresse mail")

