from celery import Celery
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_assets import Environment
import sib_api_v3_sdk
import sqlalchemy
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()
celery = Celery(__name__)
assets_env = Environment()
sib = sib_api_v3_sdk.ApiClient()
cors = CORS()

import ecosante.utils.rollup
