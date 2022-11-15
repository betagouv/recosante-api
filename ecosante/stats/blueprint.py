from datetime import date, datetime, timedelta
from functools import reduce
from flask import current_app
from flask.globals import request
from ecosante.extensions import db, sib
from ecosante.inscription.models import Inscription
from ecosante.newsletter.models import NewsletterDB
from ecosante.utils.blueprint import Blueprint
from sqlalchemy import func, or_, text
from calendar import month_name, different_locale
import json
from dateutil.parser import parse, ParserError
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from itertools import accumulate, groupby
import requests
import os

def get_month_name(month_no, locale):
    with different_locale(locale):
        return month_name[month_no]

bp = Blueprint("stats", __name__)


def first_day_last_day_of_week(d):
    year, week, _ = d.isocalendar()
    first_day = datetime.fromisocalendar(year, week, 1)
    last_day = datetime.fromisocalendar(year, week, 7)
    return f'{first_day.strftime("%d/%m/%Y")} au {last_day.strftime("%d/%m/%Y")}'


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

@bp.route('/web/')
def stats_web():
    matomo_api_url = os.getenv('MATOMO_API_URL')
    if matomo_api_url is None:
        raise Exception("MATOMO_API_URL var env is required")
    start_date = '2021-02-01'
    # Nombre total de visites
    total_visits = 0
    try:
        r = requests.get(f"{matomo_api_url}&method=VisitsSummary.getVisits&period=range&date={start_date},today")
        r.raise_for_status()
        total_visits = r.json().get('value', 0)
    except Exception as e:
        current_app.logger.error(f"Error relative to Matomo API: {e}")
    # Nombre de visites mensuelles
    monthly_visits = {}
    try:
        r = requests.get(f"{matomo_api_url}&method=VisitsSummary.getVisits&period=month&date={start_date},today")
        r.raise_for_status()
        with different_locale('fr_FR'):
            monthly_visits = {datetime.strptime(m, '%Y-%m').strftime('%B %Y'): v for m, v in r.json().items()}
    except Exception as e:
        current_app.logger.error(f"Error relative to Matomo API: {e}")
    # Nombre de visites mensuelles sur le tableau de bord
    place_monthly_visits = {}
    try:
        r = requests.get(f"{matomo_api_url}&method=Actions.getPageUrls&period=month&date={start_date},today&filter_column=label&filter_pattern=^place$")
        r.raise_for_status()
        with different_locale('fr_FR'):
            place_monthly_visits = {datetime.strptime(m, '%Y-%m').strftime('%B %Y'): (next(iter(v), {})).get('nb_visits', 0) for m, v in r.json().items()}
    except Exception as e:
        current_app.logger.error(f"Error relative to Matomo API: {e}")
    # Le site a beaucoup évolué entre 2021 et 2022 ce qui nous oblige à ignorer les stats d'intégration et de referrer antérieures
    new_version_start_date = '2022-01-01'
    # Nombre de visites qui proviennent de l'intégration du widget
    integration_widget = 0
    try:
        r = requests.get(f"{matomo_api_url}&method=VisitsSummary.getVisits&period=range&date={new_version_start_date},today&segment=entryPageUrl=@iframe%253D1")
        r.raise_for_status()
        integration_widget = r.json().get('value', 0)
    except Exception as e:
        current_app.logger.error(f"Error relative to Matomo API: {e}")
    # Nombre de visites qui proviennent du site web
    integration_website = 0
    try:
        r = requests.get(f"{matomo_api_url}&method=VisitsSummary.getVisits&period=range&date={new_version_start_date},today&segment=entryPageUrl!@iframe%253D1")
        r.raise_for_status()
        integration_website = r.json().get('value', 0)
    except Exception as e:
        current_app.logger.error(f"Error relative to Matomo API: {e}")
    # Nombre de visites selon le type de referrer (moteur de rechercher, entrée directe, site web externe, réseaux sociaux, campagne suivie)
    channel_search = 0
    channel_direct = 0
    channel_website = 0
    channel_social = 0
    channel_campaign = 0
    try:
        r = requests.get(f"{matomo_api_url}&method=Referrers.get&period=range&date={new_version_start_date},today&segment=entryPageUrl!@iframe%253D1")
        r.raise_for_status()
        channel_search = r.json().get('Referrers_visitorsFromSearchEngines', 0)
        channel_direct = r.json().get('Referrers_visitorsFromDirectEntry', 0)
        channel_website = r.json().get('Referrers_visitorsFromWebsites', 0)
        channel_social = r.json().get('Referrers_visitorsFromSocialNetworks', 0)
        channel_campaign = r.json().get('Referrers_visitorsFromCampaigns', 0)
    except Exception as e:
        current_app.logger.error(f"Error relative to Matomo API: {e}")
    to_return = {
        "total_visits": total_visits,
        "monthly_visits": json.dumps(monthly_visits),
        "place_monthly_visits": json.dumps(place_monthly_visits),
        "integration_widget": integration_widget,
        "integration_website": integration_website,
        "channel_search": channel_search,
        "channel_direct": channel_direct,
        "channel_website": channel_website,
        "channel_social": channel_social,
        "channel_campaign": channel_campaign,
    }
    return to_return

@bp.route('/email/')
def stats_email():
    # Nombre d'utilisateurs actuellement abonnés
    total_actifs = Inscription.active_query().count()
    # Nombre d'inscriptions par mois
    month_trunc = func.date_trunc('month', Inscription.date_inscription)
    count_id = func.count(Inscription.id)
    inscriptions_month_query = db.session.query(month_trunc, count_id).filter(Inscription.ville_insee.isnot(None) | Inscription.commune_id.isnot(None)).group_by(month_trunc).order_by(month_trunc)
    dict_format = lambda v: (f"{get_month_name(v[0].month, 'fr_FR')} {v[0].year}", int(v[1]))
    inscriptions = dict(map(dict_format, db.session.execute(inscriptions_month_query).all()))
    # Nombre cumulé d'inscriptions par mois
    acc_add = lambda acc, i: (i[0], acc[1] + i[1])
    acc_inscriptions = dict(accumulate([
        (v[0], v[1])
        for v in inscriptions.items()
    ], acc_add))
    # Nombre de désinscriptions par mois
    month_trunc = func.date_trunc('month', Inscription.deactivation_date)
    count_id = func.count(Inscription.id)
    desinscriptions_month_query = db.session.query(month_trunc, count_id).filter(Inscription.deactivation_date.isnot(None)).group_by(month_trunc).order_by(month_trunc)
    desinscriptions = dict(map(dict_format, db.session.execute(desinscriptions_month_query).all()))
    # Nombre cumulé de désinscriptions par mois
    acc_desinscriptions = dict(accumulate([
        (v[0], v[1])
        for v in desinscriptions.items()
    ], acc_add))
    # Nombre cumulé d'abonnés par mois
    active_users = {k: acc_inscriptions.get(k, 0) - acc_desinscriptions.get(k, 0) for k in acc_inscriptions.keys()}
    grouped_query = Inscription.active_query().group_by(text('1')).order_by(text('1'))
    make_dict = lambda attribute: dict(grouped_query.with_entities(func.unnest(getattr(Inscription, attribute)), count_id).all())
    # Nombre d'abonnés par type d'indicateur
    indicateurs = make_dict('indicateurs')
    # Nombre d'abonnés par fréquence
    indicateurs_frequence = make_dict('indicateurs_frequence')
    # Nombre d'abonnés par média
    indicateurs_media = make_dict('indicateurs_media')
    # Nombre d'abonnés à la lettre d'information hebdomadaire
    recommandations_actives = make_dict('recommandations_actives')
    # Nombre total d'abonnés ayant répondu à l'enquête de satisfaction en bas de chaque infolettre
    total_utile = NewsletterDB.query\
        .filter(NewsletterDB.appliquee.isnot(None))\
        .count()
    # Nombre d'abonnés ayant répondu oui à l'enquête de satisfaction en bas de chaque infolettre
    utile_oui = NewsletterDB.query\
        .filter(NewsletterDB.appliquee.is_(True))\
        .count()
    # Durée moyenne d'inscription
    # (pour les abonnés actuels, le temps considéré est la différence entre aujourd'hui et la date d'inscription)
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
        "total_actifs": total_actifs,
        "indicateur_indice_atmo": indicateurs.get("indice_atmo", 0),
        "indicateur_raep": indicateurs.get("raep", 0),
        "indicateur_vigilance_meteo": indicateurs.get("vigilance_meteo", 0),
        "indicateur_indice_uv": indicateurs.get("indice_uv", 0),
        "frequence_quotidien": indicateurs_frequence.get("quotidien", 0),
        "frequence_alerte": indicateurs_frequence.get("alerte", 0),
        "media_mail": indicateurs_media.get("mail", 0),
        "media_notifications_web": indicateurs_media.get("notifications_web", 0),
        "newsletter_hebdo": recommandations_actives.get("oui", 0),
        "total_utile": total_utile,
        "utile_oui": utile_oui,
        "inscriptions": json.dumps(inscriptions),
        "acc_inscriptions": json.dumps(acc_inscriptions),
        "desinscriptions": json.dumps(desinscriptions),
        "acc_desinscriptions": json.dumps(acc_desinscriptions),
        "temps_moyen_inscription": temps_moyen_inscription[0] if temps_moyen_inscription else 0
    }
    return to_return

@bp.route('/email/last2d')
def stats_email_last2d():
    to_return = {}
    yesterday = date.today() - timedelta(days=1)
    # Nombre d'inscriptions ces 2 derniers jours
    inscriptions = db.session.query(Inscription).filter(Inscription.ville_insee.isnot(None) | Inscription.commune_id.isnot(None)).filter(func.date(Inscription.date_inscription) >= yesterday).count()
    # Nombre de désinscriptions ces 2 derniers jours
    desinscriptions = db.session.query(Inscription).filter(Inscription.deactivation_date.isnot(None)).filter(func.date(Inscription.deactivation_date) >= yesterday).count()
    if inscriptions > 0:
        to_return['inscriptions'] = inscriptions
    if desinscriptions > 0:
        to_return['desinscriptions'] = desinscriptions
    return to_return

@bp.route('/email/openings')
def stats_email_openings():
    total_unique_views = 0
    total_delivered = 0
    subject_openings = []
    api_instance = sib_api_v3_sdk.EmailCampaignsApi(sib)
    try:
        day = date.today()
        weekday = day.weekday()
        thursday_weekday = 3 # jeudi
        if thursday_weekday < weekday:
            thursday = day - timedelta(weekday - thursday_weekday)
        else:
            thursday = day - timedelta(weeks=1) + timedelta(thursday_weekday - weekday)
        # Jeudi précédent (jour de la dernière session d'envoi d'infolettres)
        end_date = datetime.combine(thursday, datetime.max.time()).astimezone().isoformat()
        start_date = datetime.combine(thursday, datetime.min.time()).astimezone().isoformat()
        api_response = api_instance.get_email_campaigns(
            end_date=end_date,
            start_date=start_date,
            status='sent'
        )
        for campaign in api_response.campaigns:
            if campaign['tag'] and campaign['tag'] != 'newsletter_hebdo':
                continue
            stats = campaign['statistics']['globalStats']
            if stats['delivered'] == 0:
                continue
            # Nombre total d'ouverture unique d'infolettres
            total_unique_views += stats['uniqueViews']
            # Nombre total d'infolettres délivrés
            total_delivered += stats['delivered']
            # Taux d'ouverture par sujet d'infolettre
            subject_openings.append(
                (
                    campaign['subject'],
                    stats['uniqueViews'] / stats['delivered']
                )
            )
    except ApiException as e:
        current_app.logger.error(f"Error relative to SIB API: {e}")
    # Taux d'ouverture global pour tous les sujets
    opening = total_unique_views / total_delivered if total_delivered > 0 else 0
    return {
        "subject_openings": json.dumps(dict(subject_openings)),
        "opening": opening,
    }