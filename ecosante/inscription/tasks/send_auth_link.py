import sib_api_v3_sdk
from ecosante.extensions import celery, sib, authenticator
from ecosante.inscription.models import Inscription
import os
from sib_api_v3_sdk.rest import ApiException
from time import sleep
from flask import current_app

@celery.task()
def send_auth_link(inscription_id, redirect_path):
    template_keys = {
        '/notifications/': ('SIB_UPDATE_NOTIFICATIONS_TEMPLATE_ID', None),
    }
    template_key, default_id = template_keys.get(redirect_path, ('SIB_UPDATE_PROFILE_TEMPLATE_ID', 1454))
    success_template_id = int(os.getenv(template_key, default_id))

    inscription = Inscription.query.get(inscription_id)
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
                template_id=success_template_id,
                params={
                    "USER_UID": inscription.uid,
                    "AUTH_TOKEN": authenticator.make_token(inscription.uid)
                }
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