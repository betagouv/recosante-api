from ecosante.utils.form import BaseForm
from flask_wtf.file import FileField, FileRequired

class FormImport(BaseForm):
    file = FileField("Fichier CSV de contacts à importer",
        validators=[FileRequired()]
    )