from flask import Blueprint, render_template, request, redirect
from .models import Inscription, db
from .form import Form

bp = Blueprint("inscription", __name__, template_folder='templates')

@bp.route('/inscription', methods=['GET', 'POST'])
def inscription():
    form = Form()
    if request.method == 'POST' and form.validate_on_submit():
        inscription = Inscription(**form.data)
        db.session.add(inscription)
        db.session.commit()

        return redirect('/inscription_reussie')
    return render_template('inscription.html', form=form)

@bp.route('/inscription_reussie')
def reussi():
    return render_template('reussi.html')