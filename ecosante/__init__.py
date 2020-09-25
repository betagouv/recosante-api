from flask import Flask
from flask_alembic import Alembic
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()
alembic = Alembic()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI') or os.getenv('POSTGRESQL_ADDON_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    db.init_app(app)
    alembic.init_app(app)

    with app.app_context():
        from .inscription import models, blueprint as inscription_bp
        from .stats import blueprint as stats_bp
        alembic.upgrade()

        app.register_blueprint(inscription_bp.bp)
        app.register_blueprint(stats_bp.bp)

    return app