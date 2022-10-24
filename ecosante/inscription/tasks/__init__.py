from celery.schedules import crontab
from ecosante.extensions import celery


from .send_success_email import send_success_email #noqa
from .send_update_profile import send_update_profile #noqa
from .send_unsubscribe import send_unsubscribe, send_unsubscribe_error #noqa
from .send_deactivated_contacts import send_deactivated_contacts #noqa


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
     sender.add_periodic_task(
        crontab(hour='04', day_of_week='*/1'),
        send_deactivated_contacts.s(),
        queue='send_email',
        routing_key='send_email.send_deactivated_contacts'
    )