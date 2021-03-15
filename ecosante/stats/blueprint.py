from datetime import date, datetime, timedelta
from flask import current_app, render_template
from flask.globals import request
from ecosante.extensions import db, sib
from ecosante.inscription.models import Inscription
from ecosante.avis.models import Avis
from ecosante.avis.forms import Form
from ecosante.utils.blueprint import Blueprint
from sqlalchemy import func, or_
from calendar import month_name, different_locale
import json
from dateutil.parser import parse, ParserError
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

def get_month_name(month_no, locale):
    with different_locale(locale):
        return month_name[month_no]

bp = Blueprint("stats", __name__)

@bp.route('/')
def stats():
    g = func.date_trunc('month', Inscription.date_inscription)
    subscriptions = {
        f"{get_month_name(v[0].month, 'fr_FR.utf8')} {v[0].year}": v[1]
        for v in
        db.session.query(g, func.count(Inscription.id)).group_by(g).filter(or_(Inscription.deactivation_date == None, Inscription.deactivation_date > date.today())).order_by(g).all()
    }
    decouverte_labels = {v[0]: v[1] for v in Form.decouverte.kwargs["choices"]}
    decouverte_unnest_query = db.session.query(func.unnest(Avis.decouverte).label('d')).subquery()
    decouverte_col = decouverte_unnest_query.c.d

    decouverte = {
        decouverte_labels[v[0]]: v[1]
        for v in
        db.session.query(decouverte_col, func.count('*')).group_by(decouverte_col).order_by(decouverte_col).all()
    }
    nb_reponses = Avis.query.count()
    nb_satisfaits = Avis.query.filter(Avis.recommandabilite > 8).count()

    nb_inscriptions = Inscription.active_query().count()
    nb_allergies = Inscription.active_query().filter(Inscription.population.any("allergie_pollens")).count()
    nb_pathologie_respiratoire = Inscription.active_query().filter(Inscription.population.any("pathologie_respiratoire")).count()

    ouvertures = []
    api_instance = sib_api_v3_sdk.EmailCampaignsApi(sib)
    try:
        api_response = api_instance.get_email_campaigns(
            end_date=datetime.now(),
            start_date=(datetime.now() - timedelta(weeks=4)),
            status='sent'
        )
        for campaign in api_response.campaigns:
            try:
                date_ = parse(campaign['name'])
            except ParserError as e:
                current_app.logger.error(e)
                continue
            stats = campaign['statistics']['globalStats']
            ouvertures.append(
                (
                    date_,
                    (stats['uniqueViews']/stats['delivered'])*100
                )
            )
    except ApiException as e:
        current_app.logger.error(e)
    ouvertures.sort(key=lambda v: v[0])
    ouvertures = [(datetime.strftime(v[0], "%d/%m/%Y"), v[1]) for v in ouvertures]
    ouverture_veille = ouvertures[-1] if ouvertures else None

    to_return = {
        "actifs": Inscription.active_query().count(),
        "subscriptions": json.dumps(subscriptions),
        "media": json.dumps({
            "SMS": Inscription.active_query().filter_by(diffusion='sms').count(),
            "Mail": Inscription.active_query().filter_by(diffusion='mail').count()
        }),
        "frequence": json.dumps({
            'Tous les jours': Inscription.active_query().filter_by(frequence='quotidien').count(),
            "Lorsque la qualité de l'air est mauvaise": Inscription.active_query().filter_by(frequence='pollution').count()
        }),
        "ouvertures": json.dumps(dict(ouvertures)),
        "ouverture_veille": ouverture_veille,
        "nb_reponses": nb_reponses,
        "nb_satisfaits": nb_satisfaits,
        "nb_inscriptions": nb_inscriptions,
        "nb_allergies": nb_allergies,
        "nb_pathologie_respiratoire": nb_pathologie_respiratoire,
        "decouverte": json.dumps(decouverte),

    }

    if not request.accept_mimetypes.accept_html:
        return to_return
    return render_template('stats.html', **to_return)

