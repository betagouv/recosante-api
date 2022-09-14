import sib_api_v3_sdk
from ecosante.extensions import celery, sib, admin_authenticator
from ecosante.inscription.models import Inscription
import os
from sib_api_v3_sdk.rest import ApiException
from time import sleep
from flask import current_app, url_for

@celery.task()
def send_admin_link(email):
    if email not in admin_authenticator.admin_emails:
        return

    token = admin_authenticator.make_token(email)
    email_api = sib_api_v3_sdk.TransactionalEmailsApi(sib)
    authentication_link = url_for("pages.authenticate", _external=True, token=token)
    try:
        email_api.send_transac_email(
            sib_api_v3_sdk.SendSmtpEmail(
                subject='Lien connexion recosanté',
                sender=sib_api_v3_sdk.SendSmtpEmailSender(
                    name= "Recosanté",
                    email= "hi@recosante.beta.gouv.fr"
                ),
                to=[sib_api_v3_sdk.SendSmtpEmailTo(email=email)],
                reply_to=sib_api_v3_sdk.SendSmtpEmailReplyTo(
                    name="Recosanté",
                    email="hi@recosante.beta.gouv.fr"
                ),
                html_content=f"""
                Bonjour,
                Voici votre <a href="{ authentication_link }">lien pour aller sur l’administration</a>
                Bonne journée
                """,
                text_content=f"""
                Bonjour,
                Voici votre lien pour aller sur l’administration : { authentication_link }
                Bonne journée
                """
            )
        )
    except ApiException as e:
        current_app.logger.error(
            f"Error: {e}"
        )
        raise e
    current_app.logger.info(
        f"Mail d’authentication à l’administration envoyé à {email}"
    )