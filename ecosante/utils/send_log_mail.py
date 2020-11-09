import os
import requests

def send_log_mail(subject, text_content):
    sib_apikey = os.getenv('SIB_APIKEY')
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
                    "email": "equipe@ecosante.data.gouv.fr"
            }],
            "replyTo": {
                "name":"L'équipe écosanté",
                "email":"contact@ecosante.data.gouv.fr"
            },
            "subject": subject,
            "textContent": text_content
        }
    )