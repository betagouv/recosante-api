from ecosante.utils.form import BaseForm
from wtforms.fields import StringField
from wtforms.widgets import TextArea

class FormAvis(BaseForm):
    avis = StringField('Aidez-nous à comprendre pourquoi vous n’allez pas appliquer cette recommandation en écrivant quelques mots', widget=TextArea())