from flask import (
    render_template,
    abort,
    request,
    url_for,
    redirect
)
from .models import Recommandation, db
from .forms import FormEdit, FormSearch
from ecosante.utils.decorators import admin_capability_url
from ecosante.utils import Blueprint
from sqlalchemy import or_

bp = Blueprint(
    "recommandations",
    __name__,
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
        return redirect(url_for("inscription.export", secret_slug=secret_slug))
    return render_template("edit.html", form=form)


@bp.route('<secret_slug>/', methods=["GET", "POST"])
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