import flask_wtf
from . import FormInscription, FormPersonnalisation
from ecosante.utils.form import BaseForm
from wtforms.fields import HiddenField

class FormPremiereEtape(BaseForm):
    class Meta:
        csrf = False
    mail = FormInscription.mail


class FormDeuxiemeEtape(BaseForm):
    class Meta:
        csrf = False

    ville_insee = FormInscription.ville_insee
    deplacement = FormPersonnalisation.deplacement
    activites = FormPersonnalisation.activites
    pathologie_respiratoire =  FormPersonnalisation.pathologie_respiratoire
    allergie_pollen = FormPersonnalisation.allergie_pollen