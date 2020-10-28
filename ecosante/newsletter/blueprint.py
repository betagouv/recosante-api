from flask.helpers import flash
from ecosante.newsletter.forms.edit_indice import FormEditIndice
from flask import (
    render_template,
    request,
    redirect,
    url_for,
     stream_with_context
)
from flask.wrappers import Response
from datetime import date, datetime
import csv
import codecs
import os
import requests
import json
from urllib.parse import quote
from uuid import uuid4
from indice_pollution.regions.solvers import region
from indice_pollution.history.models import IndiceHistory
from ecosante.recommandations.models import Recommandation, db
from ecosante.utils.decorators import admin_capability_url
from ecosante.utils import Blueprint
from .forms import (
    FormEditIndices,
    FormExport,
    FormImport,
    FormRecommandations
)
from .models import (
    Newsletter,
    Recommandation
)

bp = Blueprint("newsletter", __name__)

@bp.route('<secret_slug>/csv')
@admin_capability_url
def csv_(secret_slug):
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

@bp.route('<secret_slug>/edit_indices', methods=['POST'])
@admin_capability_url
def edit_indices(secret_slug):
    form_indices = FormEditIndices()
    if form_indices.validate_on_submit():
        for form_indice in form_indices.indices.entries:
            indice = db.session.query(IndiceHistory).filter_by(
                date_=date.today(),
                insee=form_indice.data['insee']
            ).first()
            if not indice:
                indice = IndiceHistory(date_=date.today(), insee=form_indice.data['insee'])
                db.session.add(indice)
            indice._features = json.dumps({"indice": form_indice.data['indice'], "date": str(date.today())})
            db.session.commit()
    return redirect(
        url_for(
            "newsletter.link_export",
            secret_slug=secret_slug,
            **request.args
        )
    )


@bp.route('<secret_slug>/edit_recommandations', methods=['POST'])
@admin_capability_url
def edit_recommandations(secret_slug):
    form_recommandations = FormRecommandations()
    if form_recommandations.validate_on_submit():
        for form_recommandation in form_recommandations.recommandations.entries:
            recommandation = db.session.query(Recommandation).get(int(form_recommandation.data['id']))
            form_recommandation.form.populate_obj(recommandation)
            db.session.add(recommandation)
        db.session.commit()
    return redirect(
        url_for(
            "newsletter.link_export",
            secret_slug=secret_slug,
            **request.args
        )
    )

@bp.route('<secret_slug>/link_export')
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
    newsletters = list(Newsletter.export(
        preferred_reco=request.args.get('preferred_reco'),
        seed=request.args.get('seed')
    ))
    form_recommandations = FormRecommandations()
    for recommandation in set([n.recommandation for n in newsletters]):
        form_recommandations.recommandations.append_entry(recommandation)
    form_indices = FormEditIndices()
    for inscription in [n.inscription for n in newsletters if n.qai is None]:
        form_field = form_indices.indices.append_entry({"insee": inscription.ville_insee})
        form_field.indice.label.text = f'Indice pour la ville de {inscription.ville_name}'
        form_field.indice.description = f' Région: <a target="_blank" href="{region(region_name=inscription.region_name).website}">{inscription.region_name}</a>'
    return render_template(
        'link_export.html',
        secret_slug=secret_slug,
        args=request.args,
        form_recommandations=form_recommandations,
        form_indices=form_indices
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
        for delimiter in [',', ';']:
            form.file.data.stream.seek(0)
            stream = codecs.iterdecode(form.file.data.stream, 'utf-8')
            reader = csv.DictReader(stream, delimiter=delimiter)
            if 'MAIL' in reader.fieldnames:
                break
        else:
            flash("Impossible de lire le fichier importé, le délimiteur doit être `,` ou `;`", "error")
            return render_template("import.html", form=form)
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
