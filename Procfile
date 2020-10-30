python: flask run
watchstatic: flask assets watch
beat: celery --app ecosante.celery_worker.celery beat
worker: celery --app ecosante.celery_worker.celery worker -E
