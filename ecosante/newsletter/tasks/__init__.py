from ecosante.extensions import celery
from ecosante.newsletter.models import Newsletter
from ecosante.extensions import db
from celery.schedules import crontab
from flask import current_app

from .import_in_sb import import_send_and_report #noqa

@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    if current_app.config['ENV'] != "production":
        return
    sender.add_periodic_task(
        crontab(minute='*/30', hour='05-09', day_of_week='*/1'),
        import_send_and_report.s(),
        queue='send_newsletter',
        routing_key='send_newsletter.import_send_and_report'
    )
    sender.add_periodic_task(
        crontab(minute='0', hour='10', day_of_week='*/1'),
        import_send_and_report.s(force_send=True, report=True),
        queue='send_newsletter',
        routing_key='send_newsletter.import_send_and_report'
    )