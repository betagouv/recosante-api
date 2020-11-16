from ecosante.extensions import celery
from flask import current_app
from datetime import datetime
import csv
import os
import requests
from urllib.parse import quote
from ecosante.newsletter.models import Newsletter
from ecosante.extensions import db

def get_nl_csv(filepath):
    for delimiter in [',', ';']:
        with open(filepath) as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            if 'MAIL' in reader.fieldnames:
                return [Newsletter.from_csv_line(l) for l in reader]
    raise ValueError("Impossible de lire le fichier importé, le délimiteur doit être `,` ou `;`")

@celery.task(bind=True)
def delete_file(self, return_, filepath):
    os.remove(filepath)
    return return_

@celery.task()
def delete_file_error(self, exc, traceback, filepath):
    os.remove(filepath)
    current_app.logger.error('Task {0} raised exception: {1!r}\n{2!r}'.format(
          self.id, exc, traceback))


@celery.task(bind=True)
def import_in_sb(self, filepath):
    self.update_state(
        state='PENDING',
        meta={
            "progress": 0,
            "details": "Lecture du fichier CSV"
        }
    )
    newsletters = get_nl_csv(filepath)
    result = import_(self, newsletters)
    self.update_state(
        state='STARTED',
        meta={
            "progress": 100,
            "details": f"Création de la campagne SMS",
            "email_campaign_id": result['email_campaign_id'],
            "sms_campaign_id": result['sms_campaign_id']
        }
    )
    return result

@celery.task(bind=True)
def import_and_send(self, seed, preferred_reco, remove_reco):
    self.update_state(
        state='PENDING',
        meta={
            "progress": 0,
            "details": "Constitution de la liste"
        }
    )
    result = import_(
        self,
        list(Newsletter.export(
            preferred_reco=preferred_reco,
            user_seed=seed,
            remove_reco=remove_reco
        )),
        2
    )
    headers = {
        "accept": "application/json",
        "api-key": os.getenv('SIB_APIKEY')
    }
    r = requests.post(
        f'https://api.sendinblue.com/v3/emailCampaigns/{result["email_campaign_id"]}/sendNow',
        headers=headers
    )
    r.raise_for_status()
    self.update_state(
        state='PENDING',
        meta={
            "progress": 99,
            "details": "Envoi de la liste email",
            "email_campaign_id": result['email_campaign_id'],
            "sms_campaign_id": result['sms_campaign_id']
        }
    )
    r = requests.post(
        f'https://api.sendinblue.com/v3/smsCampaigns/{result["sms_campaign_id"]}/sendNow',
        headers=headers
    )
    r.raise_for_status()
    self.update_state(
        state='PENDING',
        meta={
            "progress": 100,
            "details": "Envoi de la liste email",
            "email_campaign_id": result['email_campaign_id'],
            "sms_campaign_id": result['sms_campaign_id']
        }
    )
    result['progress'] = 100
    return result

def import_(task, newsletters, overhead=0):
    email_campaign_id = None,
    sms_campaign_id = None
    
    headers = {
        "accept": "application/json",
        "api-key": os.getenv('SIB_APIKEY')
    }
    lists = dict()
    now = datetime.now()
    total_nb_requests = 4 + len(newsletters) + overhead
    nb_requests = 0
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
        task.update_state(
            state='STARTED',
            meta={
                "progress": (nb_requests/total_nb_requests)*100,
                "details": f"Création de la liste {format}"
            }
        )

    for i, nl in enumerate(newsletters):
        mail = quote(nl.inscription.mail)
        r = requests.put(
            f'https://api.sendinblue.com/v3/contacts/{mail}',
            headers=headers,
            json={
                "attributes": nl.attributes(),
                "listIds":[lists[nl.inscription.diffusion]]
            }
        )
        r.raise_for_status()
        current_app.logger.info(f"Mise à jour de {mail}")
        nb_requests += 1
        task.update_state(
            state='STARTED',
            meta={
                "progress": (nb_requests/total_nb_requests)*100,
                "details": f"Mise à jour des contacts {i}/{len(newsletters)}"
            }
        )
        db.session.add(nl)
    db.session.commit()

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
    task.update_state(
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
    task.update_state(
        state='STARTED',
        meta={
            "progress": (nb_requests/total_nb_requests)*100,
            "details": f"Création de la campagne SMS",
            "email_campaign_id": email_campaign_id,
            "sms_campaign_id": sms_campaign_id
        }
    )
    return {
        "state": "STARTED",
        "progress": (nb_requests/total_nb_requests)*100,
        "details": "Terminé",
        "email_campaign_id": email_campaign_id,
        "sms_campaign_id": sms_campaign_id
    }
