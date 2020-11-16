python: flask run
watchstatic: flask assets watch
beat: celery --app ecosante.celery_worker.celery beat
worker: watchmedo auto-restart --directory=./ --pattern=*.py --recursive -- celery --app ecosante.celery_worker.celery worker -E
