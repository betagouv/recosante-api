from flask import render_template, Blueprint, abort, request, url_for, redirect
from .models import Recommandation, db
from .forms import Form
from ecosante.utils.decorators import admin_capability_url

bp = Blueprint(
    "recommandations",
    __name__,
    template_folder='templates',
    url_prefix='/recommandations'
)

@bp.route('<secret_slug>/edit/<id>', methods=['GET', 'POST'])
@admin_capability_url
def edit(secret_slug, id):
    recommandation = Recommandation.query.get(id)
    if not recommandation:
        abort(404)
    form = Form(obj=recommandation)
    if request.method == "POST":
        form.populate_obj(recommandation)
        db.session.add(recommandation)
        db.session.commit()
        return redirect(url_for("inscription.export", secret_slug=secret_slug))
    return render_template("edit.html", form=form)