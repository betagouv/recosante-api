import requests
from wtforms.fields.html5 import EmailField, TelField
from wtforms import StringField, validators, HiddenField, BooleanField, widgets
from ecosante.utils.form import RadioField, BaseForm, AutocompleteInputWidget
from wtforms.validators import ValidationError


class FormInscription(BaseForm):
    ville_entree = StringField(
        'Dans quelle ville vivez-vous',
        [validators.InputRequired()],
        widget=AutocompleteInputWidget()
    )
    ville_choices = RadioField('Veuillez faire un choix parmis ces villes', choices=[])
    ville_insee = HiddenField('ville_insee')
    ville_name = HiddenField('ville_name')
    mail = EmailField(
        'Adresse email',
        [validators.InputRequired(), validators.Email()],
        description='(attention, les mails Ecosanté peut se retrouver dans vos SPAM ou dans le dossier "Promotions" de votre boîte mail !)'
    )
    diffusion = RadioField(
        'Souhaitez-vous recevoir les recommandations par ?',
        [validators.InputRequired()],
        choices=[('mail', 'Email'), ('sms', 'SMS')]
    )
    telephone = TelField(
        'Numéro de téléphone',
        description="(si vous avez choisi l'option d'envoi par SMS)"
    )
    frequence = RadioField(
        'À quelle fréquence souhaitez-vous recevoir les informations ?',
        [validators.InputRequired()],
        description="En selectionnant «lorsque la qualité de l'air est mauvaise» il est possible que vous ne receviez peu ou pas d'alerte Ecosanté. C'est une bonne nouvelle, cela signifie que la qualité de l'air n'est pas mauvaise dans votre région.",
        choices=[
            ('quotidien',  'Tous les jours'),
            ('pollution',  "Lorsque la qualité de l'air est mauvaise")
        ]
    )
    rgpd = BooleanField(
        "En cochant cette case vous consentez à partager vos données personnelles avec l'équipe écosanté",
        [validators.DataRequired(message='Vous devez accepter de partager vos données pour vous inscrire')],
        description='<a href="#donnees-personnelles">En savoir plus sur les données personnelles</a>',
    )

    def validate_ville_entree(form, field):
        if form.ville_insee.data and form.ville_name.data:
            form.ville_choices.choices = [(form.ville_insee.data, form.ville_name.data)]
            form.ville_choices.data = form.ville_insee.data
            return

        if form.ville_choices.data:
            r = requests.get(f'https://geo.api.gouv.fr/communes/{form.ville_choices.data}',
                params={
                    "fields": "nom",
                    "format": "json"
            })
            r.raise_for_status()
            if "nom" in r.json() and "code" in r.json():
                form.ville_insee.data = r.json()['code']
                form.ville_name.data = r.json()['nom']
                form.ville_choices.choices = [(r.json()['code'], r.json()['nom'])]
                return

        r = requests.get("https://geo.api.gouv.fr/communes",params={
                "nom": field.data,
                "boost": "population",
                "fields": "nom,code,codesPostaux",
                "format": "json"
        })
        r.raise_for_status()
        results = r.json()
        if len(results) == 0:
            raise ValidationError(f'Impossible de trouver une ville ayant pour nom :"{field.data}"')
        elif len(results) == 1 and results[0]['nom'].lower() == field.data.lower():
                form.ville_insee.data = results[0]['code']
                form.ville_name.data = results[0]['nom']
                return
        form.ville_choices.choices = [(v['code'], v['nom']) for v in results[:5]]
        raise ValidationError(
            f"Impossible de trouver une ville correspondant exactement à {field.data} veuillez faire un choix"
        )
