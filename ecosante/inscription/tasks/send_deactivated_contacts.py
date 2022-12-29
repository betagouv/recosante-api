from datetime import date
import os

from flask import current_app
import sib_api_v3_sdk

from ecosante.extensions import celery, db, sib
from ecosante.inscription.models import Inscription

@celery.task()
def send_deactivated_contacts():
    query = Inscription.query.filter_by(
        Inscription.deactivation_date == date.today(),
        Inscription.mail.is_not(None)
    ).limit(30)

    for inscription in query.all():
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
                    template_id=(os.getenv('SIB_DEACTIVATED_CONTACT', 1454))
                )
            )
        except sib.rest.ApiException as e:
            current_app.logger.error(
                f"Error: {e}"
            )
            raise e
        inscription.mail = None
        db.session.add(inscription)
    db.session.commit()