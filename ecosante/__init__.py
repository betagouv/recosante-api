from flask import Flask
from flask_alembic import Alembic
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()
alembic = Alembic()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI') or os.getenv('POSTGRESQL_ADDON_URI')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    db.init_app(app)
    alembic.init_app(app)
    monkey_patch()

    with app.app_context():
        from .inscription import models, blueprint
        alembic.upgrade()

        app.register_blueprint(blueprint.bp)

    return app

def monkey_patch():
    from wtforms import Field, validators

    def is_required(self):
        return any(map(lambda validator: isinstance(validator, validators.DataRequired), self.validators))

    Field.is_required = is_required