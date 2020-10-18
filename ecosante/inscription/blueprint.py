from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    session,
    url_for,
    jsonify
)
from .models import Inscription, db
from .forms import FormInscription, FormPersonnalisation
from ecosante.utils.decorators import admin_capability_url

bp = Blueprint("inscription", __name__, template_folder='templates', url_prefix='/inscription')

@bp.route('/', methods=['GET', 'POST'])
def inscription():
    form = FormInscription()
    if request.method == 'POST':
        if form.validate_on_submit():
            inscription = Inscription.query.filter_by(mail=form.mail.data).first() or Inscription()
            form.populate_obj(inscription)
            db.session.add(inscription)
            db.session.commit()
            session['inscription'] = inscription
            return redirect(url_for('inscription.personnalisation'))
    else:
        form.mail.process_data(request.args.get('mail'))

    return render_template('inscription.html', form=form)

@bp.route('/personnalisation', methods=['GET', 'POST'])
def personnalisation():
    if not session['inscription']:
        return redirect(url_for('index'))
    inscription = Inscription.query.get(session['inscription']['id'])
    form = FormPersonnalisation(obj=inscription)
    if request.method == 'POST' and form.validate_on_submit():
        form.populate_obj(inscription)        
        db.session.add(inscription)
        db.session.commit()
        session['inscription'] = inscription
        return redirect(url_for('inscription.reussie'))
    return render_template(f'personnalisation.html', form=form)

@bp.route('/reussie')
def reussie():
    inscription = Inscription.query.get(session['inscription']['id'])
    inscription.send_success_email()

    return render_template('reussi.html')

@bp.route('/geojson')
def geojson():
    return jsonify(Inscription.export_geojson())

@bp.route('<secret_slug>/export', methods=['GET', 'POST'])
@admin_capability_url
def export(secret_slug):
    return redirect(url_for("newsletter.export", secret_slug=secret_slug))

@bp.route('<secret_slug>/import', methods=['GET', 'POST'])
@admin_capability_url
def import_(secret_slug):
    return redirect(url_for("newsletter.import", secret_slug=secret_slug))