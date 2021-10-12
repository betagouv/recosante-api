from ecosante.extensions import celery, sib
from ecosante.newsletter.models import Newsletter, NewsletterDB, db, Inscription
from flask import current_app
import os
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from time import sleep
import json

@celery.task()
def send_success_email(inscription_id, new_version=False):
    inscription = Inscription.query.get(inscription_id)
    if not new_version:
        success_template_id = int(os.getenv('SIB_SUCCESS_TEMPLATE_ID', 108))
    else:
        if inscription.recommandations_actives == ['oui']:
	        success_template_id = int(os.getenv('SIB_SUCCESS_RECOMMANDATIONS_TEMPLATE_ID', 1453))
        else:
            success_template_id = int(os.getenv('SIB_SUCCESS_INDICATEURS_TEMPLATE_ID', 1452))
    if not success_template_id:
        return

    contact_api = sib_api_v3_sdk.ContactsApi(sib)
    try:
        contact_api.create_contact(
            sib_api_v3_sdk.CreateContact(email=inscription.mail,)
        )
    except ApiException as e:
        if json.loads(e.body)['code'] != 'duplicate_parameter':
            current_app.logger.error(
                f"Unable to create_contact: {e}"
            )
            raise e

    newsletter = NewsletterDB(Newsletter(inscription=inscription))
    sleep(0.5)
    try:
        contact_api.update_contact(
            newsletter.inscription.mail,
            sib_api_v3_sdk.UpdateContact(
                attributes=newsletter.attributes()
            )
        )
    except ApiException as e:
        current_app.logger.error(
            f"Error: {e}"
        )
        raise e

    sleep(0.5)
    email_api = sib_api_v3_sdk.TransactionalEmailsApi(sib)
    try:
        email_api.send_transac_email(
            sib_api_v3_sdk.SendSmtpEmail(
                sender=sib_api_v3_sdk.SendSmtpEmailSender(
                    name= "Recosanté",
                    email= "hi@recosante.beta.gouv.fr"
                ),
                to=[sib_api_v3_sdk.SendSmtpEmailTo(email=newsletter.inscription.mail)],
                reply_to=sib_api_v3_sdk.SendSmtpEmailReplyTo(
                    name="Recosanté",
                    email="hi@recosante.beta.gouv.fr"
                ),
                template_id=success_template_id
            )
        )
    except ApiException as e:
        current_app.logger.error(
            f"Error: {e}"
        )
        raise e
    db.session.add(newsletter)
    db.session.commit()
    current_app.logger.info(
        f"Mail de confirmation d'inscription envoyé à {newsletter.inscription.mail}"
    )