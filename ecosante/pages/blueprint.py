from flask.globals import current_app
from ecosante.tasks.inscriptions_patients import inscription_patients_task
from flask import (
    redirect,
    render_template,
    request
)
from dataclasses import asdict
from ecosante.utils import Blueprint
from ecosante.utils.decorators import admin_capability_url, webhook_capability_url
from datetime import date, timedelta
from ecosante.newsletter.models import NewsletterDB
from ecosante.recommandations.models import Recommandation
from sentry_sdk import capture_event
from indice_pollution import forecast, episodes, raep, availability
from indice_pollution.history.models import PotentielRadon

bp = Blueprint("pages", __name__, url_prefix='/')

@bp.route('/')
def redirection_index():
    return redirect("https://recosante.beta.gouv.fr/", code=301)


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


@bp.route('/data')
def data():
    d = date.today()
    insee = request.args.get('insee')
    f = forecast(insee, d)
    ep = episodes(insee, d)
    r = raep(insee)
    polluants = [
        {
            '1': 'dioxyde_soufre',
            '5': 'particules_fines',
            '7': 'ozone',
            '8': 'dioxyde_azote',
        }.get(str(e['code_pol']), f'erreur: {e["code_pol"]}')
        for e in ep['data']
        if e['etat'] != 'PAS DE DEPASSEMENT'\
            and 'date' in e\
            and e['date'] == str(d)
    ]
    reco = [
        v
        for v in Recommandation.published_query().all()
        if v.is_relevant(None, f['data'][0]['indice'], polluants, 0, d)
    ] if f['data'] else []
    return {
        "forecast": f['data'][0] if f['data'] else [],
        "episode": ep['data'][0] if ep['data'] else [],
        "recommandation": {k: v for k, v in (asdict(reco[0]) if reco else {}).items() if k in ["precisions", "recommandation"]},
        "raep": r.get('data'),
        "potentiel_radon": getattr(PotentielRadon.get(insee), 'classe_potentiel'),
        "metadata": f['metadata']
    }

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


@bp.route('/debug-sentry')
def trigger_error():
    division_by_zero = 1 / 0