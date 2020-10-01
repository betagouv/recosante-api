from flask import (Blueprint, render_template, request, redirect, session, url_for,
     current_app, stream_with_context)
from flask.wrappers import Response
from .models import Inscription, db
from .forms import FormInscription, FormPersonnalisation
from ecosante.utils.decorators import admin_capability_url
from csv import DictReader
from datetime import datetime

bp = Blueprint("inscription", __name__, template_folder='templates', url_prefix='/inscription')

@bp.route('/', methods=['GET', 'POST'])
def inscription():
    form = FormInscription()
    if request.method == 'POST':
        if form.validate_on_submit():
            inscription = Inscription.query.filter_by(mail=form.mail.data).first() or Inscription()
            form.populate_obj(inscription)
            db.session.add(inscription)
            db.session.commit()
            session['inscription'] = inscription
            return redirect(url_for('inscription.personnalisation'))
    else:
        form.mail.process_data(request.args.get('mail'))

    return render_template('inscription.html', form=form)

@bp.route('/personnalisation', methods=['GET', 'POST'])
def personnalisation():
    if not session['inscription']:
        return redirect(url_for('index'))
    inscription = Inscription.query.get(session['inscription']['id'])
    form = FormPersonnalisation(obj=inscription)
    if request.method == 'POST' and form.validate_on_submit():
        form.populate_obj(inscription)        
        db.session.add(inscription)
        db.session.commit()
        session['inscription'] = inscription
        return redirect(url_for('inscription.reussie'))
    return render_template(f'personnalisation.html', form=form)

@bp.route('/reussie')
def reussie():
    return render_template('reussi.html')

@bp.route('<secret_slug>/csv')
@admin_capability_url
def export_csv(secret_slug):
    return Response(
        stream_with_context(Inscription.generate_csv(request.args.get('new_export'))),
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=export-{datetime.now().strftime('%Y-%m-%d_%H%M')}.csv"
        }
    )

@bp.route('<secret_slug>/import_csv', methods=['GET', 'POST'])
@admin_capability_url
def import_csv(secret_slug):
    def convert_list(to_convert):
        to_convert = to_convert.strip().lower()
        if len(to_convert) == 0:
            return []
        return [l.strip() for l in to_convert.split(";")]

    if request.method == 'POST':
        if request.form.get('ecraser') == 'on':
            num_rows_deleted = db.session.query(Inscription).delete()
            current_app.logger.info(f'{num_rows_deleted} inscriptions effacées')
            db.session.commit()
        file = request.files['file']
        stream = StringIO(file.stream.read().decode("UTF8"), newline=None)
        reader = DictReader(stream, skipinitialspace=True, delimiter=';')
        for row in reader:
            mail = row["Votre adresse e-mail : elle permettra à l'Equipe Ecosanté de communiquer avec vous si besoin."]
            inscription = Inscription.query.filter_by(mail=mail).first() or Inscription()
            inscription.ville_entree = row['Dans quelle ville vivez-vous ?']
            inscription.diffusion = row["Souhaitez-vous recevoir les recommandations par : *"]
            inscription.telephone = row["Numéro de téléphone :"]
            inscription.mail = mail
            inscription.frequence = "quotidien" if row["A quelle fréquence souhaitez-vous recevoir les recommandations ? *"] == "Tous les jours" else "pollution"
            inscription.deplacement = convert_list(row['Parmi les choix suivants, quel(s) moyen(s) de transport utilisez-vous principalement pour vos déplacements ?'])
            inscription.sport = row["Pratiquez-vous une activité sportive au moins une fois par semaine ? On entend par activité sportive toute forme d'activité physique ayant pour objectif l'amélioration et le maintien de la condition physique."] == "Oui"
            inscription.apa = row["Pratiquez-vous une Activité Physique Adaptée au moins une fois par semaine ? Les APA regroupent l’ensemble des activités physiques et sportives adaptées aux capacités des personnes atteintes de maladie chronique ou de handicap."] == "Oui"
            inscription.activites = convert_list(row["Pratiquez-vous au moins une fois par semaine les activités suivantes ?"])
            inscription.enfants = row["Vivez-vous avec des enfants ?"] == "Oui"
            inscription.pathologie_respiratoire = row["Vivez-vous avec une pathologie respiratoire ?"] == "Oui"
            inscription.allergie_pollen = row["Vivez-vous avec une pathologie respiratoire ?"] == "Oui"
            inscription.fumeur = row["Êtes-vous fumeur.euse ?"] == "Oui"
            inscription.date_inscription = datetime.strptime(row["timestamp"], "%d/%m/%Y %H:%M")
            db.session.add(inscription)
        db.session.execute("""
            UPDATE inscription SET activites = array_append(activites, 'sport')
            WHERE 
                sport = true 
                AND not (activites::text[] @> ARRAY['sport']::text[]);
        """)
        db.session.commit()
        return render_template('import_csv_reussi.html')
        
    return render_template("import_csv.html")
