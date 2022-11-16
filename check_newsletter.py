import sys
from datetime import date, datetime
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

from ecosante.extensions import sib
from ecosante.newsletter.models import NewsletterDB
from ecosante.utils.send_log_mail import send_log_mail

THRESHOLD = 1000

if __name__ == "__main__":
    errors = []
    if (count := NewsletterDB.query.filter(NewsletterDB.date==date.today()).count()) < THRESHOLD:
        errors.append(f"Il y a eu {count} newsletters crées en base de données aujourd’hui")

    contacts_api = sib_api_v3_sdk.ContactsApi(sib)
    try:
        api_response = contacts_api.get_lists(limit=10)
    except ApiException:
        print("Unable to get lists")
        sys.exit(1)

    today_lists = [
        l
        for l in api_response.lists
        if l['name'].endswith(' - mail') and datetime.fromisoformat(l['name'][:len(' - mail')]).date() == date.today()
    ]
    if (count_contacts := sum([l['uniqueSubscribers'] for l in today_lists])) < THRESHOLD:
        errors.append(f"Il y a eu {len(today_lists)} créées aujourd’hui contenant {count_contacts} contacts")

    campaigns_api = sib_api_v3_sdk.EmailCampaignsApi(sib)
    try:
        campaigns = campaigns_api.get_email_campaigns(
            start_date=str(date.today())+'T00:00:00.000Z',
            end_date=str(datetime.now())
        )
    except ApiException:
        print("Unable to get campaigns")
        sys.exit(1)
    if (count_delivered := sum([c['statistics']['globalStats']['delivered'] for c in campaigns.campaigns])) < THRESHOLD:
        errors.append(f"Il y a eu {count_delivered} mails délivrés dans {len(campaigns)} campagnes")

    if errors:
        joined_errors = "\n".join(errors)
        text_content = f"""
Bonjour,

L’envoi de la newsletter ne s’est pas bien effectué. Les erreurs suivantes ont été constatées :

{joined_errors}

Bonne chance !
"""
        send_log_mail("Erreur envoi newsletter", text_content)