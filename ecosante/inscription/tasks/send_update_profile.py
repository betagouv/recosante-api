import sib_api_v3_sdk
from ecosante.extensions import celery, sib
from ecosante.inscription.models import Inscription
import os
from sib_api_v3_sdk.rest import ApiException
from time import sleep
from flask import current_app

@celery.task()
def send_update_profile(inscription_id):
    success_template_id = int(os.getenv('SIB_SUCCESS_TEMPLATE_ID', 1454))
    inscription = Inscription.query.get(inscription_id)
    contact_api = sib_api_v3_sdk.ContactsApi(sib)
    try:
        contact_api.update_contact(
            inscription.mail,
            sib_api_v3_sdk.UpdateContact(
                attributes={
                    "USER_UID": inscription.uid,
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
                    name= "Recosanté",
                    email= "hi@recosante.beta.gouv.fr"
                ),
                to=[sib_api_v3_sdk.SendSmtpEmailTo(email=inscription.mail)],
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
    current_app.logger.info(
        f"Mail de modification de profile envoyé à {inscription.mail}"
    )