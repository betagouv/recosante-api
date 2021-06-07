from ecosante.extensions import celery
from ecosante.newsletter.models import Newsletter
from ecosante.extensions import db
from flask import current_app
from celery.schedules import crontab

from .import_in_sb import import_and_send, import_send_and_report #noqa
from indice_pollution import save_all


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(minute='0', hour='5', day_of_week='*/1'),
        import_send_and_report.s(),
        queue='send_newsletter',
        routing_key='send_newsletter.import_send_and_report'
    )
