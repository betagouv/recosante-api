
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_assets import Environment

db = SQLAlchemy()
migrate = Migrate()  
assets_env = Environment()

import ecosante.utils.rollup