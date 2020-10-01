from flask import current_app
import csv
from .models import Recommandation, db

@current_app.cli.command('import-recommandations')
def import_recommandations():
    current_app.logger.info("Removing all recommandations")
    Recommandation.query.delete()
    current_app.logger.info("Reading recommandations file")
    with open('data/recommandations.csv') as f:
        reader = csv.DictReader(f)
        i = 0
        for r in reader:
            db.session.add(Recommandation(
                recommandabilite=r['Recommandabilité'],
                recommandation=r['Recommandation'],
                precisions=r['Précisions'],
                recommandation_format_SMS=r['Recommandation format SMS'],
                qa_mauvaise=r['QA mauvaise'],
                menage=r['Ménage'],
                bricolage=r['Bricolage'],
                chauffage_a_bois=r['Chauffage à bois'],
                jardinage=r['Jardinage'],
                balcon_terasse=r['Balcon/Terrasse'],
                velo_trott_skate=r['Vélo/trottinette/skateboard'],
                transport_en_commun=r['Transports en commun'],
                voiture=r['Voiture'],
                activite_physique=r['Activité physique'],
                allergies=r['Allergies'],
                enfants=r['Enfants'],
                personnes_sensibles=r['Personne sensibles'],
                niveau_difficulte=r['Niveau de difficulté'],
                autres_conditions=r['Autres conditions'],
                sources=r['Sources'],
                categorie=r['Catégorie'],
                objectif=r['Objectif']
            ))
            i += 1
    db.session.commit()
    current_app.logger.info(f"{i} recommandations were added")