from ecosante.extensions import celery
from ecosante.newsletter.models import Newsletter
from flask import current_app
import os
import requests

@celery.task()
def send_success_email(inscription_id):
    newsletter = Newsletter.from_inscription_id(inscription_id)
    sib_apikey = os.getenv('SIB_APIKEY')
    success_template_id = os.getenv('SIB_SUCCESS_TEMPLATE_ID', 108)

    r = requests.post(
        'https://api.sendinblue.com/v3/contacts',
        headers={
            'accept': 'application/json',
            'api-key': sib_apikey 
        },
        json={
            "email": newsletter.inscription.mail,
        }
    )
    try:
        r.raise_for_status()
    except Exception as e:
        current_app.logger.error(
            f"Error: {r.content}"
        )
        raise e
    r = requests.put(
        f'https://api.sendinblue.com/v3/contacts/{newsletter.inscription.mail}',
        headers={
            'accept': 'application/json',
            'api-key': sib_apikey
        },
        json={
            "attributes": {
                "VILLE": newsletter.inscription.ville_name,
                "QUALITE_AIR": newsletter.qualif,
                "BACKGROUND_COLOR": newsletter.background,
                "RECOMMANDATION": newsletter.recommandation.recommandation,
                "PRECISIONS": newsletter.recommandation.precisions,
            }
        }
    )
    try:
        r.raise_for_status()
    except Exception as e:
        current_app.logger.error(
            f"Error: {r.content}"
        )
        raise e
    r = requests.post(
        'https://api.sendinblue.com/v3/smtp/email',
        headers={
            'accept': 'application/json',
            'api-key': sib_apikey
        },
        json={
            "sender": {
                "name":"L'équipe écosanté",
                "email":"ecosante@data.gouv.fr"
            },
            "to": [{
                    "email": newsletter.inscription.mail,
            }],
            "replyTo": {
                "name":"L'équipe écosanté",
                "email":"ecosante@data.gouv.fr"
            },
            "templateId": success_template_id
        }
    )
    try:
        r.raise_for_status()
    except Exception as e:
        current_app.logger.error(
            f"Error: {r.content}"
        )
        raise e
    current_app.logger.info(
        f"Mail de confirmation d'inscription envoyé à {newsletter.inscription.mail}"
    )