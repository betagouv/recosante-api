from ecosante.extensions import celery
from flask import current_app
from datetime import datetime
import csv
import os
import requests
from urllib.parse import quote
from celery import result

def get_lines_csv(filepath):
    for delimiter in [',', ';']:
        with open(filepath) as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            if 'MAIL' in reader.fieldnames:
                return [l for l in reader]
    raise ValueError("Impossible de lire le fichier importé, le délimiteur doit être `,` ou `;`")

@celery.task(bind=True)
def delete_file(self, filepath):
    os.remove(filepath)

@celery.task(bind=True)
def delete_file_error(uuid, filepath):
    os.remove(filepath)
    r = result.AsyncResult(uuid)
    exc = r.get(propagate=False)
    current_app.logger.error('Task {0} raised exception: {1!r}\n{2!r}'.format(
          uuid, exc, r.traceback))



@celery.task(bind=True)
def import_in_sb(self, filepath):
    self.update_state(state='PENDING', meta={"progress": 0, "details": "Lecture du fichier CSV"})
    lines = get_lines_csv(filepath)
    
    headers = {
        "accept": "application/json",
        "api-key": os.getenv('SIB_APIKEY')
    }
    lists = dict()
    now = datetime.now()
    total_nb_requests = 4 + len(lines)
    nb_requests = 0
    current_app.logger.info(1)
    for format in ["sms", "mail"]:
        r = requests.post(
            "https://api.sendinblue.com/v3/contacts/lists",
            headers=headers,
            json={
                "name": f'{now} - {format}',
                "folderId": os.getenv('SIB_FOLDERID', 5)
            }
        )
        r.raise_for_status()
        lists[format] = r.json()['id']
        nb_requests += 1
        self.update_state(
            state='STARTED',
            meta={
                "progress": (nb_requests/total_nb_requests)*100,
                "details": f"Création de la liste {format}"
            }
        )

    for i, line in enumerate(lines):
        mail = quote(line['MAIL'])
        r = requests.put(
            f'https://api.sendinblue.com/v3/contacts/{mail}',
            headers=headers,
            json={
                "attributes": {
                    k: line[k]
                    for k in [
                        'FORMAT', 'QUALITE_AIR', 'LIEN_AASQA',
                        'RECOMMANDATION', 'PRECISIONS', 'VILLE', 'BACKGROUND_COLOR'
                    ]
                },
                "listIds":[lists[line['FORMAT']]]
            }
        )
        r.raise_for_status()
        nb_requests += 1
        self.update_state(
            state='STARTED',
            meta={
                "progress": (nb_requests/total_nb_requests)*100,
                "details": f"Mise à jour des contacts {i}/{len(lines)}"
            }
        )
    r = requests.post(
        'https://api.sendinblue.com/v3/emailCampaigns',
        headers=headers,
        json={
                "sender": {"name": "L'équipe Écosanté", "email": "ecosante@data.gouv.fr"},
                "name": f'{now}',
                "templateId": os.getenv('SIB_EMAIL_TEMPLATE_ID', 96),
                "subject": "Vos recommandations Écosanté",
                "replyTo": "ecosante@data.gouv.fr",
                "recipients":{"listIds":[lists['mail']]},
                "header": "Aujourd'hui, la qualité de l'air autour de chez vous est…"
        })
    r.raise_for_status()
    email_campaign_id = r.json()['id']
    nb_requests += 1
    self.update_state(
        state='STARTED',
        meta={
            "progress": (nb_requests/total_nb_requests)*100,
            "details": f"Création de la campagne mail",
            "email_campaign_id": email_campaign_id
        }
    )

    r = requests.post(
        'https://api.sendinblue.com/v3/smsCampaigns',
        headers=headers,
        json={
            "name": f'{now}',
            "sender": "Ecosante",
            "content":
"""Aujourd'hui l'indice de la qualité de l'air à {VILLE} est {QUALITE_AIR}
Plus d'information : {LIEN_AASQA}
{RECOMMANDATION}
STOP au [STOP_CODE]
""",
            "recipients": {"listIds": [lists['sms']]}
        }
    )
    r.raise_for_status()
    sms_campaign_id = r.json()['id']
    nb_requests += 1
    self.update_state(
        state='SUCCESS',
        meta={
            "progress": 100,
            "details": f"Création de la campagne SMS",
            "email_campaign_id": email_campaign_id,
            "sms_campaign_id": sms_campaign_id
        }
    )
    return filepath
