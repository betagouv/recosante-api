from flask import Flask, g
import os
from celery import Celery
from .extensions import db, migrate, assets_env, celery
from werkzeug.urls import url_encode
import logging


def configure_celery(flask_app):
    """Configure tasks.celery:
    * read configuration from flask_app.config and update celery config
    * create a task context so tasks can access flask.current_app
    Doing so is recommended by flask documentation:
    https://flask.palletsprojects.com/en/1.1.x/patterns/celery/
    """
    # Settings list:
    # https://docs.celeryproject.org/en/stable/userguide/configuration.html
    celery_conf = {
        key[len('CELERY_'):].lower(): value
        for key, value in flask_app.config.items()
        if key.startswith('CELERY_')
    }
    celery.conf.update(celery_conf)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with flask_app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask


def create_app():
    app = Flask(
        __name__,
        static_folder='assets',
        static_url_path='/assets/'
    )

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI') or os.getenv('POSTGRESQL_ADDON_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['ASSETS_DEBUG'] = True
    app.config['CELERY_RESULT_BACKEND'] = 'db+' + app.config['SQLALCHEMY_DATABASE_URI']
    app.config['CELERY_BROKER_URL'] = 'sqla+' + app.config['SQLALCHEMY_DATABASE_URI']

    db.init_app(app)
    migrate.init_app(app, db)
    assets_env.init_app(app)
    celery = configure_celery(app)

    with app.app_context():
        from .inscription import models, blueprint as inscription_bp, tasks
        from .recommandations import models, commands, blueprint as recommandation_bp
        from .avis import models, commands, blueprint as avis_bp
        from .stats import blueprint as stats_bp
        from .newsletter import blueprint as newsletter_bp, tasks
        from .pages import blueprint as pages_bp

        app.register_blueprint(inscription_bp.bp)
        app.register_blueprint(stats_bp.bp)
        app.register_blueprint(avis_bp.bp)
        app.register_blueprint(recommandation_bp.bp)
        app.register_blueprint(newsletter_bp.bp)
        app.register_blueprint(pages_bp.bp)

        app.jinja_env.add_extension("ecosante.utils.rollup.RollupJSExtension")
        app.jinja_env.add_extension("ecosante.utils.rollup.SCSSExtension")
        app.add_template_global(url_encode, name='url_encode')

    @app.before_first_request
    def before_first_request():
        log_level = logging.DEBUG
        app.logger.setLevel(log_level)

    return app