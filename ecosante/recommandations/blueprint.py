from flask.globals import current_app
from flask.helpers import make_response
from ecosante.pages.blueprint import admin
from flask import (
    render_template,
    abort,
    request,
    url_for,
    redirect,
    flash,
    stream_with_context
)
from flask.wrappers import Response
from datetime import datetime
from itertools import chain
from .models import Recommandation, db
from ecosante.newsletter.models import NewsletterDB
from .forms import FormAdd, FormEdit, FormSearch
from ecosante.utils.decorators import admin_capability_url
from ecosante.utils import Blueprint
from ecosante.utils.funcs import generate_line
from sqlalchemy import or_

bp = Blueprint(
    "recommandations",
    __name__,
)

@bp.route('<secret_slug>/add', methods=['GET', 'POST'])
@bp.route('add', methods=['GET', 'POST'])
@admin_capability_url
def add():
    form = FormAdd()
    if request.method == "POST":
        recommandation = Recommandation()
        form.populate_obj(recommandation)
        db.session.add(recommandation)
        db.session.commit()
        flash("Recommandation ajoutée")
        return redirect(url_for("recommandations.list_"))
    return render_template(
        "edit.html",
        form=form,
        action="Ajouter"
    )

@bp.route('<secret_slug>/edit/<id>', methods=['GET', 'POST'])
@bp.route('edit/<id>', methods=['GET', 'POST'])
@admin_capability_url
def edit(id):
    recommandation = db.session.query(Recommandation).get(id)
    if not recommandation:
        abort(404)
    form = FormEdit(obj=recommandation)
    if request.method == "POST":
        form.populate_obj(recommandation)
        db.session.add(recommandation)
        db.session.commit()
        return redirect(url_for("recommandations.list_", **request.args.to_dict(flat=False)))
    return render_template(
        "edit.html",
        form=form,
        action="Éditer"
    )

@bp.route('<secret_slug>/remove/<id>', methods=["GET", "POST"])
@bp.route('remove/<id>', methods=["GET", "POST"])
@admin_capability_url
def remove(id):
    recommandation = Recommandation.query.get(id)
    if request.method == "POST":
        db.session.delete(recommandation)
        db.session.commit()
        flash("Recommandation supprimée")
        return redirect(url_for("recommandations.list_"))
    return render_template(
        "remove.html",
        id=id,
        recommandation=recommandation
    )


def make_query(form):
    query = Recommandation.query
    if form.search.data:
        search = f"%{form.search.data}%"
        query = query.filter(
            or_(
                    Recommandation.recommandation.ilike(search),
                    Recommandation.precisions.ilike(search),
                    Recommandation.recommandation_format_SMS.ilike(search)
            )
        )
    if form.recommandabilite.data:
        query = query.filter(Recommandation.recommandabilite==form.recommandabilite.data)
    for categorie in form.categories.data:
        query = query.filter(
            getattr(Recommandation, categorie).is_(True)
        )
    return query.order_by(Recommandation.id)

@bp.route('<secret_slug>/', methods=["GET", "POST"])
@bp.route('/', methods=["GET", "POST"])
@admin_capability_url
def list_():
    form = FormSearch(request.args)
    query = make_query(form)
    return render_template(
        "list.html",
        recommandations=query.all(),
        form=form,
    )

@bp.route('<secret_slug>/csv', methods=["GET", "POST"])
@bp.route('/csv', methods=["GET", "POST"])
@admin_capability_url
def csv():
    form = FormSearch(request.args)
    query = make_query(form)

    return Response(
        stream_with_context(
            chain(
                generate_line(Recommandation().to_dict().keys()),
                map(
                    lambda line: generate_line(line.to_dict().values()),
                    query.all()
                )
            )
        ),
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=recommandations-export-{datetime.now().strftime('%Y-%m-%d_%H%M')}.csv"
        }
    )

@bp.route('/<secret_slug>/<id>/details')
@bp.route('/<id>/details')
@admin_capability_url
def details(id):
    recommandation = Recommandation.query.get(id)
    if not recommandation:
        return abort(404)

    newsletters = NewsletterDB.query\
        .filter_by(recommandation_id=id)\
        .filter(NewsletterDB.appliquee.isnot(None))\
        .order_by(NewsletterDB.date.desc())\
        .all()

    return render_template(
        "details.html",
        recommandation=recommandation,
        newsletters=newsletters,
    )
