from flask import (
    abort,
    render_template,
    request,
    jsonify,
    stream_with_context,
    make_response
)
from .models import Inscription, db
from .forms import FormPremiereEtape, FormDeuxiemeEtape
from ecosante.utils.decorators import (
    admin_capability_url,
    webhook_capability_url
)
from ecosante.utils import Blueprint
from ecosante.extensions import celery
from flask.wrappers import Response
from flask_cors import cross_origin
from datetime import datetime
from email_validator import validate_email
import json

bp = Blueprint("inscription", __name__)

@bp.route('/premiere-etape', methods=['POST'], strict_slashes=False)
@cross_origin(origins='*')
def premiere_etape():
    form = FormPremiereEtape(data=request.json)
    if form.validate_on_submit():
        valid = validate_email(form.mail.data)
        mail = valid.email.lower()
        inscription = Inscription.query.filter_by(mail=mail).first() or Inscription()
        inscription.mail = mail
        db.session.add(inscription)
        db.session.commit()
        return jsonify({"uid": inscription.uid}), 201
    return jsonify(form.errors), 400


@bp.route('/<uid>/', methods=['POST', 'GET'], strict_slashes=False)
@cross_origin(origins='*')
def deuxieme_etape(uid):
    inscription = db.session.query(Inscription).filter_by(uid=uid).first()
    form = FormDeuxiemeEtape(obj=inscription, data=request.json)
    if request.method == 'POST':
        if not inscription:
            abort(404)
        if form.validate_on_submit():
            for fieldname in form._fields.keys():
                if (request.form and fieldname in request.form.keys()) or (request.json and fieldname in request.json.keys()):
                    setattr(inscription, fieldname, getattr(form, fieldname).data)
            db.session.add(inscription)
            db.session.commit()
            inscription = db.session.query(Inscription).filter_by(uid=uid).first()
        else:
            return jsonify(form.errors), 400
    return {
        **{
            k: getattr(inscription, k)
            for k in form._fields.keys()
        },
        **{
            "ville_nom": inscription.ville_nom,
            "ville_codes_postaux": inscription.ville_codes_postaux
        }
    }

@bp.route('/<uid>/_confirm', methods=['GET'], strict_slashes=False)
@cross_origin(origins='*')
def confirm(uid):
    inscription = Inscription.query.filter_by(uid=uid).first()
    if not inscription:
        return jsonify({"errors": ["Unable to find inscription"]}), 404
    celery.send_task(
        "ecosante.inscription.tasks.send_success_email.send_success_email",
        (inscription.id,),
    )
    return jsonify({"result": "ok"})


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
    return render_template('changement.html', uid=request.args.get('uid'))

@bp.route('/confirmer-changement', methods=['POST', 'GET'])
def confirmer_changement():
    uid = request.args.get('uid')
    if not uid:
        abort(400)
    inscription = db.session.query(Inscription).filter_by(uid=uid).first()
    if not inscription:
        abort(404)
    inscription.deactivation_date = None
    inscription.diffusion = 'mail'
    inscription.frequence = 'quotidien'
    db.session.add(inscription)
    db.session.commit()
    return render_template('confirmer_changement.html')