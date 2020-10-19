from ecosante.utils.form import BaseForm
from wtforms import IntegerField, HiddenField, validators, FieldList, FormField

class FormEditIndice(BaseForm):
    indice = IntegerField('Indice de pollution', [validators.InputRequired()])
    insee = HiddenField('insee')

class FormEditIndices(BaseForm):
    indices = FieldList(FormField(FormEditIndice))