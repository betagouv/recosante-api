
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_static_digest import FlaskStaticDigest

db = SQLAlchemy()
migrate = Migrate()  
flask_static_digest = FlaskStaticDigest()