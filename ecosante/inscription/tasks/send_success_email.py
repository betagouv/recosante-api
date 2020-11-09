from ecosante.extensions import celery
from ecosante.newsletter.models import Newsletter
import os
import requests

@celery.task()
def send_success_email(inscription):
    newsletter = Newsletter(inscription)
    sib_apikey = os.getenv('SIB_APIKEY')
    success_template_id = os.getenv('SIB_SUCCESS_TEMPLATE_ID', 108)

    r = requests.post(
        'https://api.sendinblue.com/v3/contacts',
        headers={
            'accept': 'application/json',
            'api-key': sib_apikey 
        },
        json={
            "email": inscription.mail,
        }
    )
    r = requests.put(
        f'https://api.sendinblue.com/v3/contacts/{inscription.mail}',
        headers={
            'accept': 'application/json',
            'api-key': sib_apikey
        },
        json={
            "attributes": {
                "VILLE": inscription.ville_name,
                "QUALITE_AIR": newsletter.qualif,
                "BACKGROUND_COLOR": newsletter.background,
                "RECOMMANDATION": newsletter.recommandation.recommandation,
                "PRECISIONS": newsletter.recommandation.precisions,
            }
        }
    )
    r = requests.post(
        'https://api.sendinblue.com/v3/smtp/email',
        headers={
            'accept': 'application/json',
            'api-key': sib_apikey
        },
        json={
            "sender": {
                "name":"L'équipe écosanté",
                "email":"contact@ecosante.data.gouv.fr"
            },
            "to": [{
                    "email": inscription.mail,
            }],
            "replyTo": {
                "name":"L'équipe écosanté",
                "email":"contact@ecosante.data.gouv.fr"
            },
            "templateId": success_template_id
        }
    )