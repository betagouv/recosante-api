from flask import current_app, render_template, Blueprint, redirect, request, url_for
from .forms import Form
from .models import Avis, db
from ecosante.inscription.models import Inscription

bp = Blueprint("avis", __name__, template_folder='templates', url_prefix='/avis')

@bp.route('/', methods=['GET', 'POST'])
def index():
    form = Form()
    if request.method == "POST":
        if form.validate_on_submit():
            print('validation')
            avis = Avis()
            form.populate_obj(avis)
            db.session.add(avis)
            db.session.commit()
            return redirect(url_for('avis.ajoute'))

    return render_template(
        'form.html',
        form=form
    )

@bp.route('/ajoute')
def ajoute():
    return render_template('ajoute.html')