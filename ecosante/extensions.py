from celery import Celery
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_assets import Environment

db = SQLAlchemy()
migrate = Migrate()
celery = Celery(__name__)
assets_env = Environment()

import ecosante.utils.rollup