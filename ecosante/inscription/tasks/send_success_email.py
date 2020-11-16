from ecosante.extensions import celery, sib
from ecosante.newsletter.models import Newsletter
from flask import current_app
import os
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from time import sleep
import json

@celery.task()
def send_success_email(inscription_id):
    newsletter = Newsletter.from_inscription_id(inscription_id)
    success_template_id = os.getenv('SIB_SUCCESS_TEMPLATE_ID', 108)

    contact_api = sib_api_v3_sdk.ContactsApi(sib)
    try:
        contact_api.create_contact(
            sib_api_v3_sdk.CreateContact(email=newsletter.inscription.mail,)
        )
    except ApiException as e:
        current_app.logger.error(
            f"Error: {e}"
        )
        if json.loads(e.body)['code'] != 'duplicate_parameter':
            raise e

    sleep(0.5)
    try:
        contact_api.update_contact(
            newsletter.inscription.mail,
            sib_api_v3_sdk.UpdateContact(
                attributes={
                    "VILLE": newsletter.inscription.ville_name,
                    "QUALITE_AIR": newsletter.qualif,
                    "BACKGROUND_COLOR": newsletter.background,
                    "RECOMMANDATION": newsletter.recommandation.recommandation,
                    "PRECISIONS": newsletter.recommandation.precisions,
                }
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
                    name= "L'équipe écosanté",
                    email= "ecosante@data.gouv.fr"
                ),
                to=[sib_api_v3_sdk.SendSmtpEmailTo(email=newsletter.inscription.mail)],
                reply_to=sib_api_v3_sdk.SendSmtpEmailReplyTo(
                    name="L'équipe écosanté",
                    email="ecosante@data.gouv.fr"
                ),
                template_id=success_template_id
            )
        )
    except ApiException as e:
        current_app.logger.error(
            f"Error: {e}"
        )
        raise e
    current_app.logger.info(
        f"Mail de confirmation d'inscription envoyé à {newsletter.inscription.mail}"
    )