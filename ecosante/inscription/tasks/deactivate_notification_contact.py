from datetime import date, timedelta
import os

import sib_api_v3_sdk
from flask import current_app

from ecosante.extensions import sib, db
from ecosante.inscription.models import Inscription


def deactivate_nofication_contact(inscription_id):
    inscription = Inscription.query.get(inscription_id)
    inscription.deactivation_date = date.today() + timedelta(days=31)
    db.session.add(inscription)
    db.session.commit()

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
                template_id=(os.getenv('SIB_DEACTIVATE_NOTIFICATION_CONTACT', 1454))
            )
        )
    except sib.rest.ApiException as e:
        current_app.logger.error(
            f"Error: {e}"
        )
        raise e