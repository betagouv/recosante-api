from flask import (
    render_template,
    request,
    redirect,
    session,
    url_for,
    jsonify
)
from .models import Inscription, db
from .forms import FormInscription, FormPersonnalisation
from ecosante.utils.decorators import (
    admin_capability_url,
    webhook_capability_url
)
from ecosante.utils import Blueprint
from ecosante.extensions import celery
from flask_assets import Bundle

bp = Blueprint("inscription", __name__)

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
        celery.send_task(
            "ecosante.inscription.tasks.send_success_email.send_success_email",
            (inscription.id,),
        )
        return redirect(url_for('inscription.reussie'))
    return render_template(f'personnalisation.html', form=form)

@bp.route('/reussie')
def reussie():
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
    return redirect(url_for("newsletter.import_", secret_slug=secret_slug))

@bp.route('<secret_slug>/user_unsubscription', methods=['POST'])
@webhook_capability_url
def user_unsubscription(secret_slug):
    mail = request.json['email']
    user = Inscription.query.filter_by(mail=mail).first()
    if not user:
        celery.send_task("send_unsubscribe_error", (mail,))
    else:
        user.unsubscribe()
    return jsonify(request.json)