from wtforms.fields.simple import BooleanField, HiddenField
from wtforms import ValidationError
from wtforms.fields import DateField
from wtforms.form import Form
from ecosante.utils.form import BaseForm, IntegerField, MultiCheckboxField, OuiNonField
from ecosante.newsletter.models import NewsletterHebdoTemplate
from datetime import date
from ecosante.recommandations.forms.edit import FormEdit

class FormTemplateAdd(BaseForm):
    sib_id = IntegerField("ID send in blue")
    ordre = IntegerField("Ordre d’envoi (si l’ordre est en dessous de 0 la NL ne sera pas envoyé, c’est utile pour les brouillons)")
    debut_periode_validite = DateField("Début de la période de validité", default=date.today().replace(month=1, day=1))
    fin_periode_validite = DateField("Fin de la période de validité", default=date.today().replace(month=1, day=1, year=date.today().year+1))

    activites = FormEdit.activites
    enfants = OuiNonField("Enfants (de moins de 6 ans) ?")
    chauffage = FormEdit.chauffage
    deplacement = FormEdit.deplacement
    animaux_domestiques = FormEdit.animal_de_compagnie

    indice_atmo = OuiNonField("Inclure (Oui) ou exclure (Non) les abonnés à l’indice ATMO ?")
    raep = OuiNonField("Inclure (Oui) ou exclure (Non) les abonnés RAEP ?")
    vigilance_meteo = OuiNonField("Inclure (Oui) ou exclure (Non) les abonnés à la vigilance météo ?")
    indice_uv = OuiNonField("Inclure (Oui) ou exclure (Non) les abonnés à l’indice UV ?")

class FormTemplateEdit(FormTemplateAdd):
    id = HiddenField()