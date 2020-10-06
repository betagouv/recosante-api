from os import read
from flask import current_app
import csv
import click
from .models import Avis, db
from .forms import Form

@current_app.cli.command('import-avis')
@click.argument("filepath")
def import_avis(filepath):
    with open(filepath) as f:
        reader = csv.reader(f, delimiter=',')
        _header = next(reader)
        for row in reader:
            avis = Avis()
            avis.mail = row[2]
            avis.decouverte = [select_to_dict(Form.decouverte)[v.strip()] for v in row[3].split(";")] if row[3] else []
            avis.satisfaction_nombre_recommandation = row[4].strip() == "Oui, une recommandation me suffit"
            avis.satisfaction_frequence = select_to_dict(Form.satisfaction_frequence).get(row[5])
            avis.recommandabilite = select_to_dict(Form.recommandabilite).get(row[6])
            avis.encore = row[7].strip() == "Oui"
            avis.autres_thematiques = row[8]

            db.session.add(avis)
        db.session.commit()


def select_to_dict(field):
    return {k[1]: k[0] for k in field.kwargs['choices']}
