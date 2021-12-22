from flask import current_app
from datetime import datetime
from uuid import uuid4
import os
from flask.helpers import url_for
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from ecosante.newsletter.models import Newsletter, NewsletterDB, Inscription
from ecosante.extensions import db, sib, celery
from ecosante.utils import send_log_mail
from ecosante.utils.cache import cache_lock, cache_unlock

def get_all_contacts(limit=100):
    contacts_api = sib_api_v3_sdk.ContactsApi(sib)
    contacts = []
    offset = 0
    while True:
        result = contacts_api.get_contacts(limit=100, offset=offset)
        contacts += result.contacts
        if len(result.contacts) < limit:
            break
        offset += limit
    return contacts

def get_blacklisted_contacts():
    return [c for c in get_all_contacts() if c['emailBlacklisted']]

def deactivate_contacts(task):
    if task:
        task.update_state(
            state='STARTED',
            meta={
                "progress": 0,
                "details": "Prise en compte de la désincription des membres"
            }
        )
    for contact in get_blacklisted_contacts():
        db_contact = Inscription.active_query().filter(Inscription.mail==contact['email']).first()
        if not db_contact or not db_contact.is_active:
            continue
        db_contact.unsubscribe()

def delete_lists(task):
    if task:
        task.update_state(
            state='STARTED',
            meta={
                "progress": 0,
                "details": "Suppression des anciennes listes"
            }
        )
    list_ids_to_delete = get_lists_ids_to_delete()
    contacts_api = sib_api_v3_sdk.ContactsApi(sib)
    for i, list_id in enumerate(list_ids_to_delete, 1):
        contacts_api.delete_list(list_id)
        if task:
            task.update_state(
                state='STARTED',
                meta={
                    "progress": 0,
                    "details": f"Suppression des anciennes listes ({i}/{len(list_ids_to_delete)})"
                }
            )

def import_and_send(task, type_='quotidien', force_send=False):
    deactivate_contacts(task)
    delete_lists(task)
    result = import_(task, type_=type_, force_send=force_send)
    result['progress'] = 100
    if current_app.config['ENV'] == 'production':
        db.session.commit()
    return result

def send(campaign_id, test=False):
    if current_app.config['ENV'] == 'production' or test:
        current_app.logger.info(f"Envoi en cours de la campagne: {campaign_id}")
        send_email_api = sib_api_v3_sdk.EmailCampaignsApi(sib)
        send_email_api.send_email_campaign_now(campaign_id=campaign_id)
        current_app.logger.info(f"Envoi terminé de la campagne: {campaign_id}")

def create_mail_list(now, test):
    lists_api = sib_api_v3_sdk.ListsApi(sib)
    r = lists_api.create_list(
        sib_api_v3_sdk.CreateList(
            name=f'{now} - mail',
            folder_id=int(os.getenv('SIB_FOLDERID', 5)) if not test else int(os.getenv('SIB_FOLDERID', 1653))
        )
    )
    current_app.logger.info(f"Création de la liste send in blue '{r.id}'")
    return r.id

def get_mail_list_id(newsletter, template_id_mail_list_id, now, test):
    template_sib_id = newsletter.newsletter_hebdo_template.sib_id if newsletter.newsletter_hebdo_template else None
    if not template_sib_id in template_id_mail_list_id:
        template_id_mail_list_id[template_sib_id] = create_mail_list(now, test)
    return template_id_mail_list_id[template_sib_id]

def import_(task, type_='quotidien', force_send=False, test=False, mail_list_id=None, newsletters=None):
    errors = []
    
    now = datetime.now()
    nb_requests = 0
    template_id_mail_list_id = dict()
    if mail_list_id:
        template_id_mail_list_id[None] = mail_list_id
    if task:
        task.update_state(
            state='STARTED',
            meta={
                "details": f"Création de la liste"
            }
        )

    to_add = []
    for nl in (newsletters or Newsletter.export(type_=type_, force_send=force_send)):
        nldb = NewsletterDB(nl, get_mail_list_id(nl, template_id_mail_list_id, now, test))
        errors.extend(nldb.errors)
        if current_app.config['ENV'] == 'production':
            to_add.append(nldb)
            current_app.logger.info(f"Création de l’objet NewsletterDB pour {nldb.inscription_id}, template: {nldb.newsletter_hebdo_template_id}, mail_list_id: {nldb.mail_list_id} ")
            if len(to_add) % 1000 == 0:
                db.session.add_all(to_add)
                db.session.flush() # do not use commit, it will raise an error
                current_app.logger.info("Flush des newsletters dans la base de données")
                to_add = []

    if current_app.config['ENV'] == 'production' or test:
        db.session.add_all(to_add)
        db.session.commit()
        current_app.logger.info("Commit des newsletters dans la base de données")

    import_contacts_in_sb(template_id_mail_list_id, now, type_, test)

    return {
        "state": "STARTED",
        "progress": 100,
        "details": "Terminé",
        "errors": errors
    }


def import_contacts_in_sb(template_id_mail_list_id, now, type_, test):
    if current_app.config['ENV'] == 'production' or test:
        contact_api = sib_api_v3_sdk.ContactsApi(sib)
        for template_id, mail_list_id in template_id_mail_list_id.items():
            request_contact_import = sib_api_v3_sdk.RequestContactImport()
            request_contact_import.list_ids = [mail_list_id]
            request_contact_import.email_blacklist = False
            request_contact_import.sms_blacklist = False
            request_contact_import.update_existing_contacts = True
            request_contact_import.empty_contacts_attributes = True
            request_contact_import.file_url = url_for(
                'newsletter.export',
                secret_slug=os.getenv("CAPABILITY_ADMIN_TOKEN"),
                mail_list_id=mail_list_id,
                _external=True,
                _scheme='https'
            )
            request_contact_import.notify_url = url_for(
                'newsletter.send_campaign',
                secret_slug=os.getenv("CAPABILITY_ADMIN_TOKEN"),
                now=now,
                mail_list_id=mail_list_id,
                template_id=template_id,
                type_=type_,
                _external=True,
                _scheme='https'
            )
            current_app.logger.info("About to send newsletter with params")
            current_app.logger.info(request_contact_import)
            try:
                contact_api.import_contacts(request_contact_import)
                current_app.logger.info("Newsletter sent")
            except ApiException as e:
                current_app.logger.error("Exception when calling ContactsApi->import_contacts: %s\n" % e)

def check_campaign_already_sent(email_campaign_api, mail_list_id):
    api_response = email_campaign_api.get_email_campaigns(limit=20)
    return any(
        [
            mail_list_id in c['recipients']['lists']
            for c in api_response.campaigns
            if 'recipients' in c and 'lists' in c['recipients'] and isinstance(c['recipients']['lists'], list)
        ]
    )

def create_campaign(now, mail_list_id, template_id=None, type_='quotidien', test=False):
    def get_tag(test, type_):
        if test:
            return "test_newsletter"
        if type_ == 'hebdomadaire':
            return "newsletter_hebdo"
        else:
            return "newsletter"

    if current_app.config['ENV'] == 'production' or test:
        template_id = template_id or int(os.getenv('SIB_EMAIL_TEMPLATE_ID', 526))
        email_campaign_api = sib_api_v3_sdk.EmailCampaignsApi(sib)
        if check_campaign_already_sent(email_campaign_api, mail_list_id):
            current_app.logger.info(f"Campagne déjà envoyée pour la liste {mail_list_id}")
            return
        transactional_api = sib_api_v3_sdk.TransactionalEmailsApi(sib)
        template = transactional_api.get_smtp_template(int(template_id))
        current_app.logger.info(f"Appel à Send in blue pour l’envoi de la campagne avec la liste {mail_list_id}, now: {now}, template_id:{template_id}")
        r = email_campaign_api.create_email_campaign(
            sib_api_v3_sdk.CreateEmailCampaign(
                sender=sib_api_v3_sdk.CreateEmailCampaignSender(
                    email=template.sender.email,
                    name=template.sender.name
                ),
                name = f'{now}',
                template_id = template_id,
                subject = template.subject,
                reply_to = "newsletter@recosante.beta.gouv.fr",
                recipients = sib_api_v3_sdk.CreateEmailCampaignRecipients(
                    list_ids=[mail_list_id]
                ),
                header="Aujourd’hui, la qualité de l’air autour de chez vous est…" if type_ == 'quotidien' else "Découvrez les bons gestes de Recosanté",
                tag=get_tag(test, type_)
            )
        )
        email_campaign_id = r.id
    else:
        email_campaign_id = 0
    current_app.logger.info(f"Campagne créée {email_campaign_id} avec la liste {mail_list_id}, now: {now}, template_id:{template_id}")
    return email_campaign_id

def format_errors(errors):
    if not errors:
        return ''
    r = ''
    r2 = ''
    regions = dict()
    errors_types = {
        "no_air_quality": "Pas de qualité de l’air",
        "nothing_to_show": "Aucune donnée à montrer",
        "no_template_weekly_nl": "Pas de template pour la newsletter hebdomadaire"
    }
    for error in errors:
        if error['type'] == 'no_template_weekly_nl':
            r += f"Pas de template de newsletter hebdomadaire pour {error['mail']} (Inscription[{error['inscription_id']})"
            continue
        r += f"{errors_types.get(error['type'], error['type'])} pour la ville de {error['ville']} ({error['insee']}) région: '{error['region']}'\n"
        r2 += f"{error['ville']}, {error['insee']}, {error['region']}\n"
        regions.setdefault(error['region'], 0)
        regions[error['region']] += 1
    r += '\n'
    for region, i in regions.items():
        r += f'La région {region} a eu {i} erreurs\n'
    r += '\n'
    r += r2

    return r

@celery.task(bind=True)
def import_send_and_report(self, type_='quotidien', force_send=False, report=False):
    current_app.logger.info("Début !")
    lock_id = f"type={type_}"
    with cache_lock(lock_id, self.app.oid) as aquired:
        if not aquired:
            current_app.logger.error(f"Import et envoi déjà en cours (type: {type_})")
    new_task_id = str(uuid4())
    self.update_state(
        state='STARTED',
        meta={
            "progress": 0,
            "details": f"Lancement de la tache: '{new_task_id}'",
        }
    )
    result = import_and_send(self, type_=type_, force_send=force_send)
    if report:
        errors = format_errors(result['errors'])
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
        send_log_mail("Rapport d’envoi de la newsletter", body, name="Rapport recosante", email="rapport-envoi@recosante.beta.gouv.fr")
    self.update_state(
        state='SUCESS',
        meta={
            "progress": 100,
            "details": f"Fin",
        }
    )
    cache_unlock(lock_id)
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