import sib_api_v3_sdk
from ecosante.extensions import celery, sib, admin_authenticator
from sib_api_v3_sdk.rest import ApiException
from flask import url_for
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@celery.task()
def send_admin_link(email):
    if email not in admin_authenticator.admin_emails:
        logger.error(f"{email} not in admin list")
        return

    token = admin_authenticator.make_token(email)
    email_api = sib_api_v3_sdk.TransactionalEmailsApi(sib)
    authentication_link = url_for("pages.authenticate", _external=True, token=token)
    logger.info(f"Admin link: {authentication_link}")
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
        logger.error(
            f"Error: {e}"
        )
        raise e
    logger.info(
        f"Mail d’authentication à l’administration envoyé à {email}"
    )