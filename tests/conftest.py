import pytest

from ecosante import create_app
from ecosante.extensions import db


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(scope='session')
def app():
    _app = create_app(testing=True)
    ctx = _app.app_context()
    ctx.push()
    yield _app
    ctx.pop()


@pytest.fixture(scope="session")
def _db(app):
    """
    Returns session-wide initialised database.
    """
    db.drop_all()
    db.create_all()
    return db