from celery import Celery
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_assets import Environment
from flask_rebar import Rebar
from flask_caching import Cache
from markdown_link_attr_modifier import LinkAttrModifierExtension
import sib_api_v3_sdk
from flask_cors import CORS
from markdown import Markdown

db = SQLAlchemy()
migrate = Migrate()
celery = Celery(__name__)
assets_env = Environment()
sib = sib_api_v3_sdk.ApiClient()
cors = CORS()
rebar = Rebar()
markdown = Markdown(
    extensions=[LinkAttrModifierExtension(new_tab='on')]
)
cache = Cache()

import ecosante.utils.rollup
