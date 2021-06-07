from datetime import date, datetime, timedelta
from flask import current_app, render_template
from flask.globals import request
from ecosante.extensions import db, sib
from ecosante.inscription.models import Inscription
from ecosante.newsletter.models import NewsletterDB
from ecosante.avis.models import Avis
from ecosante.avis.forms import Form
from ecosante.utils.blueprint import Blueprint
from sqlalchemy import func, or_
from calendar import month_name, different_locale
import json
from dateutil.parser import parse, ParserError
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from itertools import accumulate

def get_month_name(month_no, locale):
    with different_locale(locale):
        return month_name[month_no]

bp = Blueprint("stats", __name__)


def first_day_last_day_of_week(d):
    year, week, _ = d.isocalendar()
    first_day = datetime.fromisocalendar(year, week, 1)
    last_day = datetime.fromisocalendar(year, week, 7)
    return f'{first_day.strftime("%d/%m/%Y")} au {last_day.strftime("%d/%m/%Y")}'


def get_inscriptions_desinscriptions():
    last_month = (datetime.now() - timedelta(weeks=5)).date()
    g_sub = func.date_trunc('week', Inscription.date_inscription)
    func_count_id = func.count(Inscription.id)
    inscriptions = {
        v[0]: v[1]
        for v in
        db.session.query(g_sub, func_count_id).filter(Inscription.date_inscription >= last_month).group_by(g_sub).order_by(g_sub).all()
    }
    g_unsub = func.date_trunc('week', Inscription.deactivation_date)
    desinscriptions = {
        v[0]: v[1]
        for v in
        db.session.query(g_unsub, func_count_id).filter(Inscription.deactivation_date >= last_month).group_by(g_unsub).order_by(g_unsub).all()
    }
    return [
        {
            "semaine": first_day_last_day_of_week(v[0]),
            "inscriptions": v[1],
            "desinscriptions": desinscriptions[v[0]]
        }
        for v in inscriptions.items()
        if v[0] in desinscriptions
    ]


def get_ouvertures():
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
                current_app.logger.info(e)
                continue
            stats = campaign['statistics']['globalStats']
            if stats['delivered'] == 0:
                continue
            ouvertures.append(
                (
                    date_,
                    (stats['uniqueViews']/stats['delivered'])*100
                )
            )
    except ApiException as e:
        current_app.logger.error(e)
    ouvertures.sort(key=lambda v: v[0])
    return [
        {"date": datetime.strftime(v[0], "%d/%m/%Y"), "taux d’ouverture" :v[1]}
        for v in ouvertures
    ]

def get_ouverture_veille(ouvertures):
    yesterday_str = (date.today() - timedelta(days=1)).strftime("%d/%m/%Y")
    for ouverture in ouvertures:
        if ouverture["date"] == yesterday_str:
            return ouverture
    return None

def get_decouvertes():
    decouverte_labels = {v[0]: v[1] for v in Form.decouverte.kwargs["choices"]}
    decouverte_unnest_query = db.session.query(func.unnest(Avis.decouverte).label('d')).subquery()
    decouverte_col = decouverte_unnest_query.c.d

    return {
        decouverte_labels[v[0]]: v[1]
        for v in
        db.session.query(decouverte_col, func.count('*')).group_by(decouverte_col).order_by(decouverte_col).all()
    }

def get_all_users():
    func_count_id = func.count(Inscription.id)
    g = func.date_trunc('month', Inscription.date_inscription)
    return list(
        map(
            lambda i: {
                "date": f"{get_month_name(i[0].month, 'fr_FR.utf8')} {i[0].year}",
                "inscriptions": i[1]
            },
            accumulate(
                db.session.query(g, func_count_id).group_by(g).order_by(g).all(),
                lambda acc, i: (i[0], acc[1] + i[1])
            )
        )
    )

@bp.route('/')
def stats():
    ouvertures = get_ouvertures()
    ouverture_veille = get_ouverture_veille(ouvertures)

    to_return = {
        "all_users": get_all_users(),
        "total_actifs": Inscription.active_query().count(),
        "total_allergies": Inscription.active_query().filter(Inscription.population.any("allergie_pollens")).count(),
        "total_pathologie_respiratoire": Inscription.active_query().filter(Inscription.population.any("pathologie_respiratoire")).count(),
        "decouverte": get_decouvertes(),
        "ouvertures": ouvertures,
        "ouverture_veille": ouverture_veille,
        "inscriptions_desinscriptions": get_inscriptions_desinscriptions(),
        "total_reponses": Avis.query.count(),
        "total_satisfaits": Avis.query.filter(Avis.recommandabilite > 8).count(),
        "total_inscriptions": Inscription.query.count(),
        "nb_appliquee": NewsletterDB.query.filter(NewsletterDB.appliquee == True).count(),
        "nb_appliquee_non": NewsletterDB.query.filter(NewsletterDB.appliquee == False).count(),
        "nb_avis": NewsletterDB.query.filter(NewsletterDB.avis != None).count(),
    }

    if not request.accept_mimetypes.accept_html:
        return to_return
    return render_template('stats.html', **to_return)

