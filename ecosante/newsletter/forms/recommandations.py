from dataclasses import Field
from ecosante.recommandations.models import Recommandation
from ecosante.recommandations.forms import FormEdit as FormRecommandation
from ecosante.utils.form import BaseForm
from wtforms import FormField, FieldList

class PartialFormRecommandation(BaseForm):
    recommandation = FormRecommandation.recommandation
    precisions = FormRecommandation.precisions
    recommandation_format_SMS = FormRecommandation.recommandation_format_SMS
    id = FormRecommandation.id

class FormRecommandations(BaseForm):
    recommandations = FieldList(FormField(PartialFormRecommandation))