from time import sleep
from flask import current_app
from datetime import datetime, timedelta
from uuid import uuid4
import os
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from ecosante.newsletter.models import Newsletter, NewsletterDB
from ecosante.inscription.models import Inscription
from ecosante.extensions import db, sib, celery
from ecosante.utils.send_log_mail import send_log_mail
from ecosante.utils.cache import cache_lock, cache_unlock
from ecosante.utils.healthchecksio import ping

def get_all_contacts(limit=100):
    contacts_api = sib_api_v3_sdk.ContactsApi(sib)
    contacts = []
    offset = 0
    while True:
        try:
            result = contacts_api.get_contacts(limit=100, offset=offset)
        except ValueError: # Le SDK raise cette exception s’il n’y a pas de contacts, par exemple si on a une 100aine pile, on ne le catch pas deux lignes en dessous
            break
        contacts += result.contacts
        if len(result.contacts) < limit:
            break
        offset += limit
    return contacts

def get_blacklisted_contacts(contacts):
    return [c for c in contacts if c['emailBlacklisted']]

def deactivate_contacts(task, contacts):
    if task:
        task.update_state(
            state='STARTED',
            meta={
                "progress": 0,
                "details": "Prise en compte de la désincription des membres"
            }
        )
    for contact in get_blacklisted_contacts(contacts):
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
    send_in_blue_contacts = get_all_contacts()
    deactivate_contacts(task, send_in_blue_contacts)
    delete_lists(task)
    result = import_(task, type_=type_, force_send=force_send, send_in_blue_contacts=send_in_blue_contacts)
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


def import_(task, type_='quotidien', force_send=False, test=False, mail_list_id=None, newsletters=None, activate_webhook=True, filter_already_sent=True, send_in_blue_contacts=[]):
    
    now = datetime.now()
    errors, template_id_mail_list_id = import_in_db(task, now, type_, force_send, test, mail_list_id, newsletters, filter_already_sent)
    import_contacts_in_sb_all(template_id_mail_list_id, now, type_, test, activate_webhook, send_in_blue_contacts)

    return {
        "state": "STARTED",
        "progress": 100,
        "details": "Terminé",
        "errors": errors
    }

def import_in_db(task, now, type_='quotidien', force_send=False, test=False, mail_list_id=None, newsletters=None, filter_already_sent=True):
    errors = []
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
    row2dict = lambda r: {
        c.name: getattr(r, c.name) for c in r.__table__.columns if not c.name in ["id", "short_id"]
    }
    to_add = []
    for nl in (newsletters or Newsletter.export(type_=type_, force_send=force_send, filter_already_sent=filter_already_sent)):
        nldb = NewsletterDB(nl, get_mail_list_id(nl, template_id_mail_list_id, now, test))
        errors.extend(nl.errors)
        if current_app.config['ENV'] == 'production':
            to_add.append(nldb)
            current_app.logger.info(f"Création de l’objet NewsletterDB pour {nldb.inscription_id}, template: {nldb.newsletter_hebdo_template_id}, mail_list_id: {nldb.mail_list_id} ")
            if len(to_add) % 1000 == 0:
                db.engine.execute(NewsletterDB.__table__.insert(), list(map(row2dict, to_add)))
                to_add = []

    if current_app.config['ENV'] == 'production' or test:
        db.engine.execute(NewsletterDB.__table__.insert(), list(map(row2dict, to_add)))
        current_app.logger.info("Commit des newsletters dans la base de données")
    return errors, template_id_mail_list_id

def import_contacts_in_sb(mail_list_id, send_in_blue_contacts):
    contact_api = sib_api_v3_sdk.ContactsApi(sib)
    window_size = 100  # or whatever limit you like
    window_idx = 0
    send_in_blue_mails = {c['email'] for c in send_in_blue_contacts}
    while True:
        start,stop = window_size*window_idx, window_size*(window_idx+1)
        attributes = [
            nl.attributes()
            for nl in NewsletterDB.query.filter_by(mail_list_id=mail_list_id).slice(start, stop).all()
            if nl.inscription.mail in send_in_blue_mails
        ]
        if attributes is None or len(attributes) == 0:
            break
        window_idx += 1
        update_batch_contacts = sib_api_v3_sdk.UpdateBatchContacts(
            [
                sib_api_v3_sdk.UpdateBatchContactsContacts(
                    email=a['EMAIL'],
                    list_ids=[mail_list_id],
                    attributes=a,
                    email_blacklisted=False,
                    sms_blacklisted=False
                )
                for a in attributes
            ]
        )
        current_app.logger.info("About to update contacts with params")
        try:
            update_response = contact_api.update_batch_contacts(update_batch_contacts)
            current_app.logger.info("contacts updated")
        except ApiException as e:
            current_app.logger.error("Exception when calling ContactsApi->import_contacts: %s\n" % e)

def import_contacts_in_sb_all(template_id_mail_list_id, now, type_, test, activate_webhook, send_in_blue_contacts):
    if current_app.config['ENV'] == 'production' or test:
        for template_id, mail_list_id in template_id_mail_list_id.items():
            import_contacts_in_sb(mail_list_id, send_in_blue_contacts)
            campaign_id = create_campaign(now, mail_list_id=mail_list_id, template_id=template_id, type_=type_)
            send(campaign_id)

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
    ping("envoi-webpush-quotidien" if type_ == "quotidien" else "envoi-email-hebdomadaire", "start")
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
    ping("envoi-webpush-quotidien" if type_ == "quotidien" else "envoi-email-hebdomadaire", "success")
    return result

def get_lists_ids_to_delete():
    api_instance = sib_api_v3_sdk.ContactsApi(sib)
    offset = 0
    api_response = api_instance.get_lists(limit=10, offset=offset)
    ids = []
    the_day_before_yesterday = datetime.today() - timedelta(days=2)
    while True:
        for r in api_response.lists:
            try:
                d = datetime.fromisoformat(r['name'][:26])
            except ValueError:
                d = datetime.max # We don't have a datetime, we use min as a default one to be able to compare
            if d <= the_day_before_yesterday:
                ids.append(r['id'])
        if not api_response.lists:
            break
        offset += 10
        api_response = api_instance.get_lists(limit=10, offset=offset)
    return ids