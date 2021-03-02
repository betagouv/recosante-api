from flask import (
    render_template,
    request,
    redirect,
    session,
    url_for,
    jsonify,
    stream_with_context,
)
from .models import Inscription, db
from .forms import FormInscription, FormPersonnalisation
from ecosante.utils.decorators import (
    admin_capability_url,
    webhook_capability_url
)
from ecosante.utils import Blueprint
from ecosante.extensions import celery
from flask.wrappers import Response
from datetime import datetime

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
    return render_template('personnalisation.html', form=form)

@bp.route('/reussie')
def reussie():
    return render_template('reussi.html')

@bp.route('<secret_slug>/user_unsubscription', methods=['POST'])
@webhook_capability_url
def user_unsubscription(secret_slug):
    mail = request.json['email']
    user = Inscription.query.filter_by(mail=mail).first()
    if not user:
        celery.send_task("ecosante.inscription.tasks.send_unsubscribe.send_unsubscribe_errorsend_unsubscribe_error", (mail,))
    else:
        user.unsubscribe()
    return jsonify(request.json)

@bp.route('<secret_slug>/export')
@bp.route('/export')
@admin_capability_url
def export():
    return Response(
        stream_with_context(Inscription.generate_csv()),
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=export-{datetime.now().strftime('%Y-%m-%d_%H%M')}.csv"
        }
    )

@bp.route('<secret_slug>/liste')
@bp.route('/liste')
@admin_capability_url
def liste():
    inscriptions = Inscription.active_query().all()
    return render_template(
        'liste.html',
        inscriptions=inscriptions
    )

@bp.route('/geojson')
def geojson():
    return jsonify(Inscription.export_geojson())


@bp.route('/changement')
def changement():
    return render_template('changement.html')