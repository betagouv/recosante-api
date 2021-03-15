from wtforms.fields.core import SelectField
from . import FormInscription
from ecosante.utils.form import BaseForm, MultiCheckboxField
from wtforms import ValidationError
import requests

class FormPremiereEtape(BaseForm):
    class Meta:
        csrf = False
    mail = FormInscription.mail


class FormDeuxiemeEtape(BaseForm):
    class Meta:
        csrf = False

    ville_insee = FormInscription.ville_insee
    deplacement = MultiCheckboxField(choices=[('velo', ''), ('tec', ''), ('voiture', ''), ('aucun', '')])
    activites = MultiCheckboxField(
        choices=[('jardinage', ''), ('bricolage', ''), ('menage', ''), ('sport', ''), ('aucun', '')]
    )
    animaux_domestiques = MultiCheckboxField(choices=[('chat', ''), ('chien', ''), ('aucun', '')])
    chauffage = MultiCheckboxField(choices=[('bois', ''), ('chaudiere', ''), ('appoint', ''), ('aucun', '')])
    connaissance_produit = MultiCheckboxField(
        choices=[
            ('medecin', ''),
            ('association', ''),
            ('reseaux_sociaux', ''),
            ('publicite', ''),
            ('ami', ''),
            ('autrement', '')
    ])
    population = MultiCheckboxField(choices=[('pathologie_respiratoire', ''), ('allergie_pollens', ''), ('aucun', '')])
    enfants = SelectField(choices=['oui', 'non', 'aucun', None], coerce=lambda v: None if v is None else str(v))

    def validate_ville_insee(form, field):
        r = requests.get(f'https://geo.api.gouv.fr/communes/{field.data}')
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            raise ValidationError("Unable to get ville")
