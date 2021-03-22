from flask import (
    render_template,
    request
)
from werkzeug.utils import redirect
from ecosante.utils import Blueprint
from ecosante.utils.decorators import admin_capability_url, webhook_capability_url
from datetime import date, timedelta
from ecosante.newsletter.models import NewsletterDB
from sentry_sdk import capture_event

bp = Blueprint("pages", __name__, url_prefix='/')

@bp.route('/')
def index():
    return render_template("index.html")

@bp.route('/changement-indice-atmo')
def changement_atmo():
    return render_template("changement-atmo.html")

@bp.route('/donnees-personnelles')
def donnees_personnelles():
    return render_template("donnees-personnelles.html")

@bp.route('/admin/<secret_slug>')
@bp.route('/admin/')
@admin_capability_url
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


@bp.route('<secret_slug>/sib_error', methods=['POST'])
@webhook_capability_url
def sib_error():
    capture_event(request.json)

