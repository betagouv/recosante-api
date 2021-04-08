import sib_api_v3_sdk
from ecosante.extensions import celery, sib
from time import sleep

@celery.task
def inscription_patients_task(nom_medecin, emails):
    contacts_api = sib_api_v3_sdk.ContactsApi(sib)
    transac_api = sib_api_v3_sdk.TransactionalEmailsApi(sib)
    for email in emails:
        contacts_api.create_contact(
            sib_api_v3_sdk.CreateContact(email=email)
        )
        sleep(0.1)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=[sib_api_v3_sdk.SendSmtpEmailTo(email=email) for email in emails],
        template_id=487,
        params={"NOM_MEDECIN": nom_medecin}
    )
    transac_api.send_transac_email(send_smtp_email=send_smtp_email)