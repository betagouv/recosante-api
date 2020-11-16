from ecosante.utils.form import BaseForm
from wtforms import TextField

class FormAvis(BaseForm):
    avis = TextField('Avis')