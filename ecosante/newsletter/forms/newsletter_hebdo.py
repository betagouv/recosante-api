from wtforms.fields.simple import HiddenField
from wtforms import ValidationError
from ecosante.utils.form import BaseForm, IntegerField
from ecosante.newsletter.models import NewsletterHebdoTemplate

class FormTemplateAdd(BaseForm):
    sib_id = IntegerField("ID send in blue")
    ordre = IntegerField("Ordre d’envoi")

    def validate_ordre(form, field):
        template_same_ordre = NewsletterHebdoTemplate.query.filter_by(ordre=field.data).first()
        if template_same_ordre:
            if not 'id' in form.data or int(form.data['id']) != template_same_ordre.id:
                raise ValidationError("Un autre template a déjà cet ordre")

class FormTemplateEdit(FormTemplateAdd):
    id = HiddenField()