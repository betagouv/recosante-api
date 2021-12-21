import requests, requests_mock
from ecosante.newsletter.tasks.send_webpush_notifications import *
from ecosante.newsletter.models import Newsletter, NewsletterDB
from tests.conftest import inscription

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

    send_webpush_notifications()
    assert mock.call_count == 1
    nls = NewsletterDB.query.all()
    assert len(nls) == 1
    assert nls[0].webpush_subscription_info.id == inscription_notifications.webpush_subscriptions_info[0].id

    send_webpush_notifications()
    assert mock.call_count == 1

@requests_mock.Mocker(kw='mock')
def test_cas_send_wepush_notifications_pas_de_donnee(inscription_notifications, recommandation, **kw):
    mock = kw['mock']
    mock.post('https://updates.push.services.mozilla.com/wpush/v2/pouet', text='data')

    send_webpush_notifications()
    assert mock.call_count == 0
    nls = NewsletterDB.query.all()
    assert len(nls) == 0