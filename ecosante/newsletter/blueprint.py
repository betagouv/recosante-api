from flask import (
    abort,
    render_template,
    request,
    redirect,
    url_for,
    stream_with_context,
    session
)
from flask.wrappers import Response
from datetime import date, datetime
import json
import os
from time import time
from uuid import uuid4

from werkzeug.urls import url_encode
from indice_pollution.regions.solvers import get_region
from indice_pollution.history.models import IndiceHistory
from ecosante.recommandations.models import Recommandation, db
from ecosante.utils.decorators import admin_capability_url, task_status_capability_url
from ecosante.utils import Blueprint
from ecosante.extensions import celery
from .forms import FormAvis
from .models import (
    Newsletter,
    NewsletterDB,
    Recommandation
)

bp = Blueprint("newsletter", __name__)

@bp.route('<short_id>/avis', methods=['GET', 'POST'])
def avis(short_id):
    nl = db.session.query(NewsletterDB).filter_by(short_id=short_id).first()
    if not nl:
        abort(404)
    nl.appliquee = request.args.get('avis') == 'oui'
    form = FormAvis(request.form, obj=nl)
    if request.method=='POST' and form.validate_on_submit():
        form.populate_obj(nl)
        db.session.add(nl)
        db.session.commit()
        return redirect(
            url_for('newsletter.avis_enregistre', short_id=short_id)
        )
    db.session.add(nl)
    db.session.commit()

    return render_template(
        'avis.html',
        nl=nl,
        form=form,
    )

@bp.route('<short_id>/avis/enregistre')
def avis_enregistre(short_id):
    return render_template('avis_enregistre.html')

@bp.route('<secret_slug>/avis/liste')
@bp.route('/avis/liste')
@admin_capability_url
def liste_avis():
    newsletters = NewsletterDB.query\
        .filter(NewsletterDB.avis.isnot(None))\
        .order_by(NewsletterDB.date.desc())\
        .all()
    return render_template('liste_avis.html', newsletters=newsletters)


@bp.route('<secret_slug>/avis/csv')
@bp.route('/avis/csv')
@admin_capability_url
def export_avis():
    return Response(
        stream_with_context(
            NewsletterDB.generate_csv_avis()
        ),
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=export-avis-{datetime.now()}"
        }
    )