import json
from time import sleep
from flask import current_app
from py_vapid import Vapid
from ecosante.newsletter.models import Newsletter, NewsletterDB
from ecosante.extensions import db, celery
from pywebpush import WebPushException, webpush


vapid_claims = {"sub": "mailto:contact@recosante.beta.gouv.fr"}

def send_webpush_notification(nldb: NewsletterDB, vapid_claims, retry=0):
    if retry >= 3:
        return None
    try:
        r = webpush(
            nldb.webpush_subscription_info.data,
            data=json.dumps(nldb.webpush_data),
            vapid_private_key=current_app.config['VAPID_PRIVATE_KEY'],
            vapid_claims=vapid_claims
        )
        return nldb
    except WebPushException as ex:
        if ex.response and ex.response.status_code == 429:
            retry_after = ex.response.headers.get('retry-after')
            try:
                retry_after_int = int(retry_after)
                sleep(retry_after_int)
                return send_webpush_notification(nldb, vapid_claims, retry+1)
            except ValueError:
                current_app.logger.error(f"Unable to retry after: {retry_after}")
                return None

@celery.task(bind=True)
def send_webpush_notifications(self):
    for nl in Newsletter.export(media='notifications_web'):
        nldb = NewsletterDB(nl)
        nldb = send_webpush_notification(nldb, vapid_claims)
        if nldb:
            db.session.add(nldb)
    db.session.commit()