
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_static_digest import FlaskStaticDigest
from flask_assets import Environment, Bundle

db = SQLAlchemy()
migrate = Migrate()  
flask_static_digest = FlaskStaticDigest()
assets_env = Environment()

import ecosante.utils.rollup