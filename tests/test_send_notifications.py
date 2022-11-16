from datetime import date, datetime, timedelta
import os
import requests_mock
from ecosante.newsletter.tasks.send_webpush_notifications import *
from ecosante.newsletter.models import Newsletter, NewsletterDB
from indice_pollution.history.models import VigilanceMeteo
from indice_pollution.history.models import IndiceUv
from psycopg2.extras import DateTimeTZRange
from datetime import date

@requests_mock.Mocker(kw='mock')
def test_cas_send_wepush_notification(inscription_notifications, recommandation, **kw):
    mock = kw['mock']
    mock.post('https://updates.push.services.mozilla.com/wpush/v2/pouet', text='data')

    nl = Newsletter(
        inscription=inscription_notifications,
        forecast={"data": []},
        episodes={"data": []},
        recommandations=[recommandation],
        webpush_subscription_info=inscription_notifications.webpush_subscriptions_info[0]
    )
    send_webpush_notification(NewsletterDB(nl), vapid_claims)
    assert mock.call_count == 1

@requests_mock.Mocker(kw='mock')
def test_cas_send_wepush_notifications(inscription_notifications, recommandation, bonne_qualite_air, raep_eleve, **kw):
    mock = kw['mock']
    mock.post('https://updates.push.services.mozilla.com/wpush/v2/pouet', text='data')
    mock.get(f'https://hc-ping.com/{os.getenv("HEALTCHECKSIO_API_KEY")}/envoi-webpush-quotidien/start')
    mock.get(f'https://hc-ping.com/{os.getenv("HEALTCHECKSIO_API_KEY")}/envoi-webpush-quotidien')

    send_webpush_notifications()
    assert mock.call_count == 3
    nls = NewsletterDB.query.all()
    assert len(nls) == 1
    assert nls[0].webpush_subscription_info.id == inscription_notifications.webpush_subscriptions_info[0].id

    send_webpush_notifications()
    assert mock.call_count == 5

@requests_mock.Mocker(kw='mock')
def test_cas_send_wepush_notifications_pas_de_donnee(inscription_notifications, recommandation, **kw):
    mock = kw['mock']
    mock.post('https://updates.push.services.mozilla.com/wpush/v2/pouet', text='data')
    mock.get(f'https://hc-ping.com/{os.getenv("HEALTCHECKSIO_API_KEY")}/envoi-webpush-quotidien/start')
    mock.get(f'https://hc-ping.com/{os.getenv("HEALTCHECKSIO_API_KEY")}/envoi-webpush-quotidien')

    send_webpush_notifications()
    assert mock.call_count == 2
    nls = NewsletterDB.query.all()
    assert len(nls) == 0

def test_webpush_data(inscription_notifications, recommandation, bonne_qualite_air, raep_eleve, db_session):
    indice_uv = IndiceUv(
        zone_id=inscription_notifications.commune.zone_id,
        date=date.today(),
        uv_j0=1,
    )
    db_session.add(indice_uv)
    v = VigilanceMeteo(
        zone_id=inscription_notifications.commune.departement.zone_id,
        phenomene_id=1,
        couleur_id=1,
        date_export=datetime.now() - timedelta(hours=1),
        validity=DateTimeTZRange(date.today() - timedelta(days=1), date.today() + timedelta(days=1)),
    )
    db_session.add(v)
    inscription_notifications.indicateurs = inscription_notifications.indicateurs + ["indice_uv"] + ["vigilance_meteo"]
    db_session.commit()
    newsletters = list(Newsletter.export(media='notifications_web'))
    assert len(newsletters) == 1
    nldb = NewsletterDB(newsletters[0])
    webpush_data = nldb.webpush_data
    assert 'Air' in webpush_data['body']
    assert 'Pollens' in webpush_data['body']
    assert 'Vigilance météo' in webpush_data['body']
    assert 'UV' in webpush_data['body']
