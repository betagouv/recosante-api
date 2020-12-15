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

@pytest.fixture(scope='session')
def app():
    _app = create_app(testing=True)
    _app.config['WTF_CSRF_ENABLED'] = False
    _app.config['SQLALCHEMY_DATABASE_URI'] = DB_CONN
    ctx = _app.app_context()
    ctx.push()
    yield _app
    ctx.pop()


@pytest.fixture(scope="session")
def _db(app):
    """
    Returns session-wide initialised database.
    """
    with app.app_context():
        db.drop_all()
        with cf.ProcessPoolExecutor() as pool:
            pool.submit(flask_migrate.upgrade())
        db.create_all()
        return db