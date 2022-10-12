from flask.globals import current_app
from ecosante.tasks import inscription_patients_task, send_admin_link
from flask import (
    abort,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from ecosante.utils import Blueprint
from ecosante.extensions import admin_authenticator, celery
from ecosante.utils.decorators import webhook_capability_url
from datetime import date, timedelta
from ecosante.newsletter.models import NewsletterDB
from sentry_sdk import capture_event
from indice_pollution import availability
from jose import jwt
from hmac import compare_digest
from wtforms import EmailField

from ecosante.utils.form import BaseForm


bp = Blueprint("pages", __name__, url_prefix='/')

@bp.route('/')
def redirection_index():
    return redirect("https://recosante.beta.gouv.fr/", code=301)


@bp.route('/admin', strict_slashes=False)
@admin_authenticator.route
def admin():
    count_avis_hier = NewsletterDB.query\
        .filter(
            NewsletterDB.avis.isnot(None),
            NewsletterDB.date==date.today() - timedelta(days=1))\
        .count()
    count_avis_aujourdhui = NewsletterDB.query\
        .filter(
            NewsletterDB.avis.isnot(None),
            NewsletterDB.date==date.today())\
        .count()
    return render_template("admin.html", count_avis_hier=count_avis_hier, count_avis_aujourdhui=count_avis_aujourdhui)

@bp.route('/admin_login/', methods=['GET', 'POST'], strict_slashes=False)
def admin_login():
    class AdminForm(BaseForm):
        email = EmailField()
    form = AdminForm()
    if request.method == 'GET':
        return render_template("admin_login.html", form=form)
    elif request.method == 'POST':
        if not form.validate():
            abort(400)
        celery.send_task(
            'ecosante.tasks.send_admin_link.send_admin_link',
            (form.email.data, ),
            queue='send_email',
            routing_key='send_email.admin_link'
        )
        return render_template("admin_login_done.html")

@bp.route('/authenticate')
def authenticate():    
    if (encoded_token := request.args.get('token')) == None:
        abort(401)
    try:
        decoded_token = admin_authenticator.decode_token(encoded_token)
    except (jwt.ExpiredSignatureError, jwt.JWTClaimsError, jwt.JWTError):
        abort(401)
    decoded_email = decoded_token.get('email')
    for email in admin_authenticator.admin_emails:
        if compare_digest(email, decoded_email):
            session['admin_email'] = email
            return redirect(url_for('pages.admin'))
    else:
        abort(401)
    

@bp.route('<secret_slug>/sib_error', methods=['POST'])
@webhook_capability_url
def sib_error(secret_slug):
    capture_event(request.json)
    return {"body": "ok"}


@bp.route('/inscription-patients', methods=['POST'])
def inscription_patients():
    inscription_patients_task.delay(
        request.json['nom_medecin'],
        request.json['mails']
    )
    return '"ok"'


@bp.route('/city-availability')
def city_availability():
    insee = request.args.get('insee')
    if not insee:
        {"availability": False}, 404
    return {"availability": availability(insee)}


@bp.route('/recommandation-episodes-pollution')
def recommandation_episode_pollution():
    nom_polluants = {
        "o3": "à l’Ozone (O3)",
        "pm10": "aux particules fines (PM10)",
        "no2": "au dioxyde d’azote (NO2)",
        "so2": "au dioxyde de soufre (SO2)"
    }
    polluants = [nom_polluants.get(p.lower(), p) for p in request.args.getlist('polluants')]
    return render_template(
        "recommandation-episodes-pollution.html",
        population=request.args.get('population'),
        polluants=polluants
    )

@bp.route('/_application_server_key')
def vapid_public_key():
    return {"application_server_key": current_app.config['APPLICATION_SERVER_KEY']}
