from ecosante.extensions import celery
from celery.schedules import crontab
from .import_in_sb import import_send_and_report, send #noqa
from .send_webpush_notifications import send_webpush_notifications #noqa

@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    if sender.conf.env != "production":
        return
    sender.add_periodic_task(
        crontab(minute='0', hour='06-13', day_of_week='*/1'),
        import_send_and_report.s(type_='quotidien'),
        queue='send_newsletter',
        routing_key='send_newsletter.import_send_and_report'
    )
    sender.add_periodic_task(
        crontab(minute='0', hour='14', day_of_week='*/1'),
        import_send_and_report.s(type_='quotidien', force_send=True, report=True),
        queue='send_newsletter',
        routing_key='send_newsletter.import_send_and_report'
    )
    sender.add_periodic_task(
        crontab(minute='0', hour='11', day_of_week='4'),
        import_send_and_report.s(type_='hebdomadaire', force_send=True, report=True),
        queue='send_newsletter',
        routing_key='send_newsletter.import_send_and_report'
    )
    sender.add_periodic_task(
        crontab(minute='0', hour='06-13', day_of_week='*/1'),
        send_webpush_notifications.s(),
        queue='send_newsletter',
        routing_key='send_newsletter.send_webpush_notifications'
    )
    sender.add_periodic_task(
        crontab(minute='0', hour='14', day_of_week='*/1'),
        send_webpush_notifications.s(force_send=True),
        queue='send_newsletter',
        routing_key='send_newsletter.send_webpush_notifications'
    )