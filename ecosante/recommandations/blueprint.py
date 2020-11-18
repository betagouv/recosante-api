from ecosante.pages.blueprint import admin
from flask import (
    render_template,
    abort,
    request,
    url_for,
    redirect,
    flash
)
from .models import Recommandation, db
from ecosante.newsletter.models import NewsletterDB
from .forms import FormAdd, FormEdit, FormSearch
from ecosante.utils.decorators import admin_capability_url
from ecosante.utils import Blueprint
from sqlalchemy import or_

bp = Blueprint(
    "recommandations",
    __name__,
)

@bp.route('<secret_slug>/add', methods=['GET', 'POST'])
@admin_capability_url
def add(secret_slug):
    form = FormAdd()
    if request.method == "POST":
        recommandation = Recommandation()
        form.populate_obj(recommandation)
        db.session.add(recommandation)
        db.session.commit()
        flash("Recommandation ajoutée")
        return redirect(url_for("recommandations.list", secret_slug=secret_slug))
    return render_template(
        "edit.html",
        form=form,
        action="Ajouter"
    )

@bp.route('<secret_slug>/edit/<id>', methods=['GET', 'POST'])
@admin_capability_url
def edit(secret_slug, id):
    recommandation = Recommandation.query.get(id)
    if not recommandation:
        abort(404)
    form = FormEdit(obj=recommandation)
    if request.method == "POST":
        form.populate_obj(recommandation)
        db.session.add(recommandation)
        db.session.commit()
        return redirect(url_for("recommandations.list", secret_slug=secret_slug))
    return render_template(
        "edit.html",
        form=form,
        action="Éditer"
    )

@bp.route('<secret_slug>/remove/<id>', methods=["GET", "POST"])
@admin_capability_url
def remove(secret_slug, id):
    recommandation = Recommandation.query.get(id)
    if request.method == "POST":
        db.session.delete(recommandation)
        db.session.commit()
        flash("Recommandation supprimée")
        return redirect(url_for("recommandations.list", secret_slug=secret_slug))
    return render_template(
        "remove.html",
        secret_slug=secret_slug,
        id=id,
        recommandation=recommandation
    )

@bp.route('<secret_slug>/', methods=["GET", "POST"])
@admin_capability_url
def list(secret_slug):
    form = FormSearch()
    query = Recommandation.query
    filters = []
    if form.validate_on_submit():
        if form.search.data:
            search = f"%{form.search.data}%"
            query = query.filter(
                or_(
                        Recommandation.recommandation.ilike(search),
                        Recommandation.precisions.ilike(search),
                        Recommandation.recommandation_format_SMS.ilike(search)
                )
            )
        for categorie in form.categories.data:
            query = query.filter(
                getattr(Recommandation, categorie).is_(True)
            )
    return render_template(
        "list.html",
        recommandations=query.all(),
        form=form,
        secret_slug=secret_slug
    )

@bp.route('/<secret_slug>/<id>/details')
@admin_capability_url
def details(secret_slug, id):
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
        secret_slug=secret_slug
    )