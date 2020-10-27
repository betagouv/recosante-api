from . import create_app

app = create_app()

from .extensions import celery #noqa