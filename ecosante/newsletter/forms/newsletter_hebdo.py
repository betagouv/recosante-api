from wtforms.fields.simple import HiddenField
from wtforms import ValidationError
from wtforms.fields import DateField
from ecosante.utils.form import BaseForm, IntegerField
from ecosante.newsletter.models import NewsletterHebdoTemplate
from datetime import date

class FormTemplateAdd(BaseForm):
    sib_id = IntegerField("ID send in blue")
    ordre = IntegerField("Ordre d’envoi")
    debut_periode_validite = DateField("Début de la période de validité", default=date.today().replace(month=1, day=1))
    fin_periode_validite = DateField("Fin de la période de validité", default=date.today().replace(month=1, day=1, year=date.today().year+1))

    def validate_ordre(form, field):
        template_same_ordre = NewsletterHebdoTemplate.query.filter_by(ordre=field.data).first()
        if template_same_ordre:
            if not 'id' in form.data or int(form.data['id']) != template_same_ordre.id:
                raise ValidationError("Un autre template a déjà cet ordre")

class FormTemplateEdit(FormTemplateAdd):
    id = HiddenField()