from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
     stream_with_context
)
from flask.wrappers import Response
from datetime import datetime
import csv
import codecs
import os
import requests
from urllib.parse import quote
from uuid import uuid4
from ecosante.recommandations.models import Recommandation, db
from ecosante.recommandations.forms import Form as FormRecommandation
from ecosante.utils.decorators import admin_capability_url
from .forms import FormExport, FormImport
from .models import Newsletter, Recommandation

bp = Blueprint("newsletter", __name__, template_folder='templates', url_prefix='/newsletter')

@bp.route('<secret_slug>/csv')
@admin_capability_url
def csv(secret_slug):
    return Response(
        stream_with_context(
            Newsletter.generate_csv(
                request.args.get('preferred_reco')
            )
        ),
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=export-{datetime.now().strftime('%Y-%m-%d_%H%M')}.csv"
        }
    )

@bp.route('<secret_slug>/link_export', methods=['GET', 'POST'])
@admin_capability_url
def link_export(secret_slug):
    if not request.args.get('seed'):
        return redirect(
            url_for(
                "newsletter.link_export",
                seed=str(uuid4()),
                secret_slug=secret_slug,
                **request.args
            )
        )
    if request.method == "POST":
        recommandation = Recommandation.query.get(request.form.get('id'))
        form = FormRecommandation(obj=recommandation)
        if form.validate_on_submit():
            form.populate_obj(recommandation)
            db.session.add(recommandation)
            db.session.commit()
    newsletters = Newsletter.export(
        preferred_reco=request.args.get('preferred_reco'),
        seed=request.args.get('seed')
    )
    recommandations_forms = [
        FormRecommandation(obj=recommandation) 
        for recommandation in set([n.recommandation for n in newsletters])
    ]
    return render_template(
        'link_export.html',
        secret_slug=secret_slug,
        args=request.args,
        recommandations_forms=recommandations_forms
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
                "newsletter.link_export",
                secret_slug=secret_slug,
                preferred_reco=form.recommandations.data,
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