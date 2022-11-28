import json
from time import sleep
from flask import current_app
from py_vapid import Vapid
from ecosante.inscription.models import Inscription, WebpushSubscriptionInfo
from ecosante.newsletter.models import Newsletter, NewsletterDB
from ecosante.inscription.tasks.deactivate_notification_contact import deactivate_nofication_contact
from ecosante.extensions import db, celery
from pywebpush import WebPushException, webpush
from copy import deepcopy


vapid_claims = {"sub": "mailto:contact@recosante.beta.gouv.fr"}

def send_webpush_notification(nldb: NewsletterDB, vapid_claims, retry=0):
    if retry >= 3:
        return None
    try:
        r = webpush(
            nldb.webpush_subscription_info.data,
            data=json.dumps(nldb.webpush_data),
            vapid_private_key=current_app.config['VAPID_PRIVATE_KEY'],
            vapid_claims=deepcopy(vapid_claims)
        )
        current_app.logger.info(f"Notification sent to {nldb.inscription.mail}")
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
        elif ex.response and ex.response.status_code == 410:
            db.session.remove(nldb.webpush_subscription_info)
        else:
            current_app.logger.error(f"Error sending notification to {nldb.inscription.mail}")
            current_app.logger.error(ex)
            return None


@celery.task(bind=True)
def send_webpush_notifications(self, only_to=None, filter_already_sent=True, force_send=False):
    inscription_ids_with_error = set()
    for nl in Newsletter.export(media='notifications_web', only_to=only_to, filter_already_sent=filter_already_sent, force_send=force_send):
        nldb = NewsletterDB(nl)
        nldb = send_webpush_notification(nldb, vapid_claims)
        if nldb:
            db.session.add(nldb)
        else:
            inscription_ids_with_error.add(nldb.inscription_id)
    db.session.commit()

    still_in_db = db.session\
        .query(WebpushSubscriptionInfo.inscription_id)\
        .filter(WebpushSubscriptionInfo.inscription_id.in_(inscription_ids_with_error))\
        .all()

    ids_to_send_deactivate_notifcation_contact = set()
    if still_in_db:
        ids_to_send_deactivate_notifcation_contact = inscription_ids_with_error - {v[0] for v in still_in_db}
    else:
        ids_to_send_deactivate_notifcation_contact = inscription_ids_with_error

    for inscription_id in ids_to_send_deactivate_notifcation_contact:
        deactivate_nofication_contact.apply_async(
                (inscription_id,),
                queue='send_email',
                routing_key='send_email.unsubscribe_notification'
            )
