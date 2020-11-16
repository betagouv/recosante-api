from ecosante.newsletter.tasks.import_in_sb import import_and_send
from flask import (
    abort,
    render_template,
    request,
    redirect,
    url_for,
    stream_with_context
)
from flask.wrappers import Response
from datetime import date, datetime
import json
import os
from time import time
from uuid import uuid4

from werkzeug.urls import url_encode
from indice_pollution.regions.solvers import region
from indice_pollution.history.models import IndiceHistory
from ecosante.recommandations.models import Recommandation, db
from ecosante.utils.decorators import admin_capability_url
from ecosante.utils import Blueprint
from ecosante.extensions import celery
from .forms import (
    FormEditIndices,
    FormExport,
    FormImport,
    FormRecommandations,
    FormAvis
)
from .models import (
    Newsletter,
    Recommandation
)
from .tasks import import_in_sb, delete_file, delete_file_error, import_and_send

bp = Blueprint("newsletter", __name__)

@bp.route('<secret_slug>/csv')
@admin_capability_url
def csv_(secret_slug):
    return Response(
        stream_with_context(
            Newsletter.generate_csv(
                preferred_reco=request.args.get('preferred_reco'),
                seed=request.args.get('seed'),
                remove_reco=request.args.getlist('remove_reco')
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
    form_recommandations = FormRecommandations(request.form)
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
        ) + "?" + url_encode(request.args)
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
        seed=request.args.get('seed'),
        remove_reco=request.args.getlist('remove_reco')
    ))
    form_recommandations = FormRecommandations()
    recommandations_list = list([n.recommandation for n in newsletters])
    recommandations = list(set(recommandations_list))
    recommandations.sort(key=lambda r: recommandations_list.count(r), reverse=True)
    for recommandation in recommandations:
        form_recommandations.recommandations.append_entry(recommandation)

    form_indices = FormEditIndices()
    for inscription in [n.inscription for n in newsletters if n.qai is None]:
        form_field = form_indices.indices.append_entry({"insee": inscription.ville_insee})
        form_field.indice.label.text = f'Indice pour la ville de {inscription.ville_name}'
        form_field.indice.description = f' Région: <a target="_blank" href="{region(region_name=inscription.region_name).website}">{inscription.region_name}</a>'
    return render_template(
        'link_export.html',
        secret_slug=secret_slug,
        form_recommandations=form_recommandations,
        form_indices=form_indices,
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
    task_id = None
    if request.method == 'POST' and form.validate_on_submit():
        filepath = os.path.join('/tmp/', f"{time()}-{form.file.data.filename}")
        form.file.data.save(filepath)
        task = import_in_sb.apply_async(
            (filepath,),
            link=delete_file.s(filepath),
            link_error=delete_file_error.s(filepath)
        )
        task_id = task.id

    return render_template(
        "import.html",
        form=form,
        task_id=task_id
    )

@bp.route('<secret_slug>/task_status/<task_id>')
@admin_capability_url
def task_status(secret_slug, task_id):
    task = celery.AsyncResult(task_id)
    return {
        **{'state': task.state},
        **(task.info or {"progress": 0, "details": ""})
    }

@bp.route('<secret_slug>/send')
@admin_capability_url
def send(secret_slug):
    task = import_and_send.delay(
        request.args.get('seed'),
        request.args.get('preferred_reco'),
        request.args.getlist('remove_reco')
    )
    return render_template(
        "send.html",
        task_id=task.id
    )

@bp.route('<short_id>/avis', methods=['GET', 'POST'])
def avis(short_id):
    nl = db.session.query(Newsletter).filter_by(short_id=short_id).first()
    if not nl:
        abort(404)
    nl.appliquee = request.args.get('avis') == 'oui'
    form = FormAvis(request.form, obj=nl)
    if request.method=='POST' and form.validate_on_submit():
        form.populate_obj(nl)
        return redirect(
            url_for('newsletter.avis_enregistre', short_id=short_id)
        )
    db.session.add(nl)
    db.session.commit()

    return render_template(
        'avis.html',
        nl=nl,
        form=form
    )

@bp.route('<short_id>/avis/enregistre')
def avis_enregistre(short_id):
    return render_template('avis_enregistre.html')
