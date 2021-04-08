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
    func_count_id = func.count(Inscription.id)
    g = func.date_trunc('month', Inscription.date_inscription)
    active_users = {
        f"{get_month_name(v[0].month, 'fr_FR.utf8')} {v[0].year}": v[1]
        for v in
        db.session.query(g, func_count_id).filter(or_(Inscription.deactivation_date == None, Inscription.deactivation_date > date.today())).group_by(g).order_by(g).all()
    }
    all_users = {
        f"{get_month_name(v[0].month, 'fr_FR.utf8')} {v[0].year}": v[1]
        for v in
        db.session.query(g, func_count_id).group_by(g).order_by(g).all()
    }
    last_month = (datetime.now() - timedelta(weeks=5)).date()
    g_sub = func.date_trunc('week', Inscription.date_inscription)
    inscriptions = {
        v[0].isocalendar()[1]: v[1]
        for v in
        db.session.query(g_sub, func_count_id).filter(Inscription.date_inscription >= last_month).group_by(g_sub).order_by(g_sub).all()
    }
    g_unsub = func.date_trunc('week', Inscription.deactivation_date)
    desinscriptions = {
        v[0].isocalendar()[1]: v[1]
        for v in
        db.session.query(g_unsub, func_count_id).filter(Inscription.deactivation_date >= last_month).group_by(g_unsub).order_by(g_unsub).all()
    }
    decouverte_labels = {v[0]: v[1] for v in Form.decouverte.kwargs["choices"]}
    decouverte_unnest_query = db.session.query(func.unnest(Avis.decouverte).label('d')).subquery()
    decouverte_col = decouverte_unnest_query.c.d

    decouverte = {
        decouverte_labels[v[0]]: v[1]
        for v in
        db.session.query(decouverte_col, func.count('*')).group_by(decouverte_col).order_by(decouverte_col).all()
    }
    total_reponses = Avis.query.count()
    total_satisfaits = Avis.query.filter(Avis.recommandabilite > 8).count()

    total_inscriptions = Inscription.query.count()
    total_actifs = Inscription.active_query().count()
    total_allergies = Inscription.active_query().filter(Inscription.population.any("allergie_pollens")).count()
    total_pathologie_respiratoire = Inscription.active_query().filter(Inscription.population.any("pathologie_respiratoire")).count()

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
    ouvertures = [(datetime.strftime(v[0], "%d/%m/%Y"), v[1]) for v in ouvertures]
    ouverture_veille = ouvertures[-1] if ouvertures else None

    to_return = {
        "active_users": json.dumps(active_users),
        "all_users": json.dumps(all_users),
        "total_actifs": total_actifs,
        "total_allergies": total_allergies,
        "total_pathologie_respiratoire": total_pathologie_respiratoire,
        "decouverte": json.dumps(decouverte),
        "ouvertures": json.dumps(dict(ouvertures)),
        "ouverture_veille": ouverture_veille,
        "inscriptions": inscriptions,
        "desinscriptions": desinscriptions,
        "total_reponses": total_reponses,
        "total_satisfaits": total_satisfaits,
        "total_inscriptions": total_inscriptions,
    }

    if not request.accept_mimetypes.accept_html:
        return to_return
    return render_template('stats.html', **to_return)

