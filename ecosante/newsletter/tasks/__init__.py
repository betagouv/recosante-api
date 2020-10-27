from ecosante.extensions import celery
from ecosante.newsletter.models import Newsletter
from flask import current_app
from celery.schedules import crontab

@celery.task()
def save_indice():
    for nl in Newsletter.export():
        current_app.logger.info(f'Save history for {nl.inscription.ville_insee}')

@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(minute='0', hour='*/1'),
        save_indice.s()
    )