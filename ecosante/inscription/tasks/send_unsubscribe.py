from ecosante.extensions import celery
from ecosante.utils import send_log_mail

@celery.task()
def send_unsubscribe(mail):
    send_log_mail(
        "Désinscription de la liste de diffusion",
        f"""
Bonjour,

L'utilisateur {mail} s'est désinscrit de la newsletter

Bonne journée !
""")

@celery.task()
def send_unsubscribe_error(mail):
    send_log_mail(
        "Erreur lors de la désinscription à la liste de diffusion",
        f"""
Bonjour,

L'utilisateur {mail} a tenté de se désinscrire mais nous n'avons pas trouvé son mail en base.
Il pourrait être opportun que l'équipe technique comprenne ce qui s'est passé

Bonne journée !
""")