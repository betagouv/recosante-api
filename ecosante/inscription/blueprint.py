from flask import (Blueprint, render_template, request, redirect, session, url_for,
     current_app, stream_with_context, jsonify)
from flask.wrappers import Response
from .models import Inscription, db
from .forms import FormInscription, FormPersonnalisation, FormExport, FormImport
from ecosante.utils.decorators import admin_capability_url
from ecosante.recommandations.models import Recommandation
from datetime import datetime
import csv
import codecs
import os
import requests
from urllib.parse import quote

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
    inscription = Inscription.query.get(session['inscription']['id'])
    inscription.send_success_email()

    return render_template('reussi.html')

@bp.route('/geojson')
def geojson():
    return jsonify(Inscription.export_geojson())

@bp.route('<secret_slug>/csv')
@admin_capability_url
def export_csv(secret_slug):
    return Response(
        stream_with_context(
            Inscription.generate_csv(
                request.args.get('preferred_reco')
            )
        ),
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=export-{datetime.now().strftime('%Y-%m-%d_%H%M')}.csv"
        }
    )

@bp.route('<secret_slug>/export', methods=['GET', 'POST'])
@admin_capability_url
def export(secret_slug):
    form = FormExport()
    form.recommandations.choices=[
        (
            r.id,
            r.recommandation
        )
        for r in Recommandation.query.all()
    ]
    form.recommandations.widget.secret_slug = secret_slug
    if request.method == 'POST':
        return redirect(
            url_for(
                "inscription.export_csv",
                secret_slug=secret_slug,
                preferred_reco=form.recommandations.data
            )
        )

    return render_template('export.html', form=form, secret_slug=secret_slug)


@bp.route('<secret_slug>/import', methods=['GET', 'POST'])
@admin_capability_url
def import_(secret_slug):
    form = FormImport()
    sms_campaign_id, email_campaign_id = None, None
    if request.method == 'POST' and form.validate_on_submit():
        headers = {
            "accept": "application/json",
            "api-key": os.getenv('SIB_APIKEY')
        }
        lists = dict()
        now = datetime.now()
        for format in ["sms", "mail"]:
            r = requests.post(
                "https://api.sendinblue.com/v3/contacts/lists",
                headers=headers,
                json={
                    "name": f'{now} - {format}',
                    "folderId": os.getenv('SIB_FOLDERID', 5)
                }
            )
            r.raise_for_status()
            lists[format] = r.json()['id']

        stream = codecs.iterdecode(form.file.data.stream, 'utf-8')
        reader = csv.DictReader(stream)
        for row in reader:
            mail = quote(row['MAIL'])
            r = requests.put(
                f'https://api.sendinblue.com/v3/contacts/{mail}',
                headers=headers,
                json={
                    "attributes": {
                        k: row[k]
                        for k in [
                            'FORMAT', 'QUALITE_AIR', 'LIEN_AASQA',
                            'RECOMMANDATION', 'PRECISIONS', 'VILLE', 'BACKGROUND_COLOR'
                        ]
                    },
                    "listIds":[lists[row['FORMAT']]]
                }
            )
            r.raise_for_status()

        r = requests.post(
            'https://api.sendinblue.com/v3/emailCampaigns',
            headers=headers,
            json={
                    "sender": {"name": "L'équipe Écosanté", "email": "ecosante@data.gouv.fr"},
                    "name": f'{now}',
                    "templateId": os.getenv('SIB_EMAIL_TEMPLATE_ID', 96),
                    "subject": "Vos recommandations Écosanté",
                    "replyTo": "ecosante@data.gouv.fr",
                    "recipients":{"listIds":[lists['mail']]},
                    "header": "Aujourd'hui, la qualité de l'air autour de chez vous est…"
            })
        r.raise_for_status()
        email_campaign_id = r.json()['id']

        r = requests.post(
            'https://api.sendinblue.com/v3/smsCampaigns',
            headers=headers,
            json={
                "name": f'{now}',
                "sender": "Ecosante",
                "content":
"""Aujourd'hui l'indice de la qualité de l'air à {VILLE} est {QUALITE_AIR}
Plus d'information : {LIEN_AASQA}
{RECOMMANDATION}
STOP au [STOP_CODE]
""",
                "recipients": {"listIds": [lists['sms']]}
            }
        )
        r.raise_for_status()
        sms_campaign_id = r.json()['id']


    return render_template(
        "import.html",
        form=form,
        sms_campaign_id=sms_campaign_id,
        email_campaign_id=email_campaign_id
    )