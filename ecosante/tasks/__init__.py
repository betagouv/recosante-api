from celery.schedules import crontab
from ecosante.extensions import celery
from flask import current_app
from .import_from_production import import_from_production

@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    if sender.conf.env != "staging":
        return
    sender.add_periodic_task(
        crontab(minute='0', hour='14', day_of_week='*/1'),
        import_from_production.s(),
        queue='staging'
    )