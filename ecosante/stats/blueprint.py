from datetime import date, datetime, timedelta
from functools import reduce
from flask import current_app, jsonify, render_template
from flask.globals import request
from ecosante.extensions import db, sib
from ecosante.inscription.models import Inscription
from ecosante.avis.models import Avis
from ecosante.avis.forms import Form
from ecosante.utils.blueprint import Blueprint
from sqlalchemy import func, or_, text
from calendar import month_name, different_locale
import json
from dateutil.parser import parse, ParserError
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from itertools import accumulate, groupby

def get_month_name(month_no, locale):
    with different_locale(locale):
        return month_name[month_no]

bp = Blueprint("stats", __name__)


def first_day_last_day_of_week(d):
    year, week, _ = d.isocalendar()
    first_day = datetime.fromisocalendar(year, week, 1)
    last_day = datetime.fromisocalendar(year, week, 7)
    return f'{first_day.strftime("%d/%m/%Y")} au {last_day.strftime("%d/%m/%Y")}'

@bp.route('/')
def stats():
    func_count_id = func.count(Inscription.id)
    g = func.date_trunc('month', Inscription.date_inscription)
    active_users = {
        f"{get_month_name(v[0].month, 'fr_FR.utf8')} {v[0].year}": v[1]
        for v in
        db.session.query(g, func_count_id).filter(or_(Inscription.deactivation_date == None, Inscription.deactivation_date > date.today())).group_by(g).order_by(g).all()
    }
    all_users = dict(accumulate([
        (f"{get_month_name(v[0].month, 'fr_FR.utf8')} {v[0].year}", v[1])
        for v in
        db.session.query(g, func_count_id).group_by(g).order_by(g).all()
    ], lambda acc, i: (i[0], acc[1] + i[1])))
    last_month = (datetime.now() - timedelta(weeks=5)).date()
    g_sub = func.date_trunc('week', Inscription.date_inscription)
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
    inscriptions_desinscriptions = [
        [first_day_last_day_of_week(v[0]), [v[1], desinscriptions[v[0]]]]
        for v in inscriptions.items()
        if v[0] in desinscriptions
    ]
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
    total_allergies = Inscription.active_query().filter(Inscription.indicateurs.any("raep")).count()
    total_pathologie_respiratoire = Inscription.active_query().filter(Inscription.population.any("pathologie_respiratoire")).count()


    temps_moyen_inscription = db.session.query(
        func.sum(
            func.coalesce(
                Inscription.deactivation_date,
                func.current_date()
            ) - Inscription.date_inscription
        ) / func.count(Inscription.id)
    ).filter(
        Inscription.date_inscription != None
    ).one_or_none()

    to_return = {
        "active_users": json.dumps(active_users),
        "all_users": json.dumps(all_users),
        "total_actifs": total_actifs,
        "total_allergies": total_allergies,
        "total_pathologie_respiratoire": total_pathologie_respiratoire,
        "decouverte": json.dumps(decouverte),
        "inscriptions_desinscriptions": inscriptions_desinscriptions,
        "total_reponses": total_reponses,
        "total_satisfaits": total_satisfaits,
        "total_inscriptions": total_inscriptions,
        "temps_moyen_inscription": temps_moyen_inscription[0] if temps_moyen_inscription else 0
    }

    if not request.accept_mimetypes.accept_html:
        return to_return
    return render_template('stats.html', **to_return)


@bp.route('/openings/')
def openings():
    openings = []
    api_instance = sib_api_v3_sdk.EmailCampaignsApi(sib)
    try:
        api_response = api_instance.get_email_campaigns(
            end_date=datetime.now(),
            start_date=(datetime.now() - timedelta(weeks=4)),
            status='sent'
        )
        for campaign in api_response.campaigns:
            if campaign['tag'] and campaign['tag'] != 'newsletter':
                continue
            try:
                date_ = parse(campaign['name'])
            except ParserError as e:
                current_app.logger.info(e)
                continue
            stats = campaign['statistics']['globalStats']
            if stats['delivered'] == 0:
                continue
            openings.append(
                (
                    date_,
                    (stats['uniqueViews'], stats['delivered'])
                )
            )
    except ApiException as e:
        current_app.logger.error(e)
    openings.sort(key=lambda v: v[0])
    openings = [
        (v[0].strftime("%d/%m/%Y"), (v[1][0]/v[1][1])*100)
        for v in
        [
            (d, reduce(
                lambda acc, v: (acc[0] + v[1][0], acc[1] + v[1][1]),
                values,
                (0, 0))
            )
            for d, values in groupby(openings, lambda v: v[0].date())
        ]
    ]
    opening_yesterday = openings[-1] if openings else None
    return {
        "openings": json.dumps(dict(openings)),
        "opening_yesterday": opening_yesterday,
    }


@bp.route('/users')
def users():
    active_query = db.session.query(Inscription).where(Inscription.deactivation_date == None)
    grouped_query = active_query.group_by(text('1')).order_by(text('1'))
    make_dict = lambda attribute: dict(grouped_query.with_entities(func.unnest(getattr(Inscription, attribute)), func.count('*')).all())
    enfants = dict(active_query.with_entities(Inscription.enfants, func.count('*')).group_by(Inscription.enfants).all())
    if None in enfants:
        enfants['aucun'] += enfants[None]
        del enfants[None]
    return {
        "indicateurs": make_dict('indicateurs'),
        "indicateurs_frequence": make_dict('indicateurs_frequence'),
        "indicateurs_media": make_dict('indicateurs_media'),
        "newsletter_hebdo": make_dict('recommandations_actives'),
        "activites": make_dict('activites'),
        "enfants": enfants,
        "chauffage": make_dict('chauffage'),
        "transport": make_dict('deplacement'),
        "animaux": make_dict('animaux_domestiques'),
    }

