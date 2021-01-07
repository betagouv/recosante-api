from flask import current_app
from datetime import datetime
from uuid import uuid4
import csv
import os
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from urllib.parse import quote_plus
from ecosante.newsletter.models import Newsletter, NewsletterDB
from ecosante.extensions import db, sib, celery
from ecosante.utils import send_log_mail

def get_nl_csv(filepath):
    for delimiter in [',', ';']:
        with open(filepath) as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            if 'MAIL' in reader.fieldnames:
                return [NewsletterDB(Newsletter.from_csv_line(l)) for l in reader]
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
            "details": "Suppression des anciennes listes"
        }
    )
    list_ids_to_delete = get_lists_ids_to_delete()
    contacts_api = sib_api_v3_sdk.ContactsApi(sib)
    for i, list_id in enumerate(list_ids_to_delete, 1):
        contacts_api.delete_list(list_id)
        self.update_state(
            state='PENDING',
            meta={
                "progress": 0,
                "details": f"Suppression des anciennes listes ({i}/{len(list_ids_to_delete)})"
            }
        )
    self.update_state(
        state='PENDING',
        meta={
            "progress": 0,
            "details": "Constitution de la liste"
        }
    )
    newsletters = list(
        map(
            NewsletterDB,
            Newsletter.export(
                preferred_reco=preferred_reco,
                user_seed=seed,
                remove_reco=remove_reco
            )
        )
    )
    self.update_state(
        state='PENDING',
        meta={
            "progress" :0,
            "details": "Construction des listes SIB d'envoi"
        }
    )
    result = import_(self, newsletters, 2)
    send_email_api = sib_api_v3_sdk.EmailCampaignsApi(sib)
    send_email_api.send_email_campaign_now(result["email_campaign_id"])
    self.update_state(
        state='PENDING',
        meta={
            "progress": 99,
            "details": "Envoi de la liste email",
            "email_campaign_id": result['email_campaign_id'],
            "sms_campaign_id": result['sms_campaign_id']
        }
    )
    send_sms_api = sib_api_v3_sdk.SMSCampaignsApi(sib)
    send_sms_api.send_sms_campaign_now(result["sms_campaign_id"])
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
    db.session.commit()
    return result

def import_(task, newsletters, overhead=0):
    email_campaign_id = None,
    sms_campaign_id = None
    errors = []
    
    lists = dict()
    now = datetime.now()
    total_nb_requests = 4 + len(newsletters) + overhead
    nb_requests = 0
    lists_api = sib_api_v3_sdk.ListsApi(sib)
    for format in ["sms", "mail"]:
        r = lists_api.create_list(
            sib_api_v3_sdk.CreateList(
                name=f'{now} - {format}',
                folder_id=os.getenv('SIB_FOLDERID', 5)
            )
        )
        lists[format] = r.id
        nb_requests += 1
        task.update_state(
            state='STARTED',
            meta={
                "progress": (nb_requests/total_nb_requests)*100,
                "details": f"Création de la liste {format}"
            }
        )

    contact_api = sib_api_v3_sdk.ContactsApi(sib)
    for i, nl in enumerate(newsletters):
        if nl.qai is None:
            errors.append(f"Pas de qualité de l’air pour {nl.inscription.mail} ville : {nl.inscription.ville_entree} ")
            current_app.logger.error(f"No qai for {nl.inscription.mail}")
        else:
            try:
                contact_api.update_contact(
                    nl.inscription.mail,
                    sib_api_v3_sdk.UpdateContact(
                        attributes=nl.attributes(),
                        list_ids=[lists[nl.inscription.diffusion]]
                    )
                )
            except ApiException as e:
                current_app.logger.error(f"Error updating {nl.inscription.mail}")
                current_app.logger.error(e)
            current_app.logger.info(f"Mise à jour de {nl.inscription.mail}")
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

    email_campaign_api = sib_api_v3_sdk.EmailCampaignsApi(sib)
    r = email_campaign_api.create_email_campaign(
        sib_api_v3_sdk.CreateEmailCampaign(
            sender = sib_api_v3_sdk.CreateEmailCampaignSender(
                name="L'équipe Écosanté",
                email="ecosante@data.gouv.fr"
            ),
            name = f'{now}',
            template_id = os.getenv('SIB_EMAIL_TEMPLATE_ID', 226),
            subject = "Vos recommandations Écosanté",
            reply_to = "ecosante@data.gouv.fr",
            recipients = sib_api_v3_sdk.CreateEmailCampaignRecipients(
                list_ids=[lists['mail']]
            ),
            header="Aujourd'hui, la qualité de l'air autour de chez vous est…"
        )
    )
    email_campaign_id = r.id
    nb_requests += 1
    task.update_state(
        state='STARTED',
        meta={
            "progress": (nb_requests/total_nb_requests)*100,
            "details": f"Création de la campagne mail",
            "email_campaign_id": email_campaign_id
        }
    )

    sms_campaign_api = sib_api_v3_sdk.SMSCampaignsApi(sib)
    r = sms_campaign_api.create_sms_campaign(
        sib_api_v3_sdk.CreateSmsCampaign(
            name = f'{now}',
            sender = "Ecosante",
            content =
"""Aujourd'hui l'indice de la qualité de l'air à {VILLE} est {QUALITE_AIR}
Plus d'information : {LIEN_AASQA}
{RECOMMANDATION}
STOP au [STOP_CODE]
""",
            recipients = sib_api_v3_sdk.CreateSmsCampaignRecipients(
                list_ids = [lists['sms']]
            )
        )
    )
    sms_campaign_id = r.id
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
        "sms_campaign_id": sms_campaign_id,
        "errors": errors
    }


@celery.task(bind=True)
def import_send_and_report(self):
    result = import_and_send(str(uuid4()), None, [])
    errors = '\n'.join(result['errors'])
    body = """
Bonjour,
Il n’y a pas eu d’erreur lors de l’envoi de la newsletter
Bonne journée !
""" if not errors else f"""
Bonjour,
Il y a eu des erreurs lors de l’envoi de la newsletter :
{errors}

Bonne journée
"""
    send_log_mail("Rapport d’envoi de la newsletter", body)
    return result

def get_lists_ids_to_delete():
    api_instance = sib_api_v3_sdk.ContactsApi(sib)
    offset = 10
    api_response = api_instance.get_lists(limit=10, offset=offset)
    ids = []
    while True:
        ids = ids + [r['id'] for r in api_response.lists]
        if not api_response.lists:
            break
        offset += 10
        api_response = api_instance.get_lists(limit=10, offset=offset)
    return ids