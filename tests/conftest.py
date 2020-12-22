import pytest
import os
import sqlalchemy as sa
import concurrent.futures as cf
import flask_migrate
from ecosante import create_app
from ecosante.extensions import db

# Retrieve a database connection string from the shell environment
try:
    DB_CONN = os.environ['TEST_DATABASE_URL']
except KeyError:
    raise KeyError('TEST_DATABASE_URL not found. You must export a database ' +
                   'connection string to the environmental variable ' +
                   'TEST_DATABASE_URL in order to run tests.')
else:
    DB_OPTS = sa.engine.url.make_url(DB_CONN).translate_connect_args()

pytest_plugins = ['pytest-flask-sqlalchemy']

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture(scope="session")
def app():
    app = create_app()
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = DB_CONN
    with app.app_context():
        db.engine.execute('DROP TABLE IF EXISTS alembic_version;')
        with cf.ProcessPoolExecutor() as pool:
            pool.submit(flask_migrate.upgrade)
        yield app
        db.session.remove()  # looks like db.session.close() would work as well
        db.drop_all()

@pytest.fixture(scope='session')
def _db(app):
    return db