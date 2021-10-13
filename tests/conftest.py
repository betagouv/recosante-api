from indice_pollution.history.models.commune import Commune
from indice_pollution.history.models.indice_atmo import IndiceATMO
import pytest
import os
import sqlalchemy as sa
import concurrent.futures as cf
import flask_migrate
from ecosante import create_app
from indice_pollution import create_app as create_app_indice_pollution
from ecosante.newsletter.models import NewsletterDB
from ecosante.inscription.models import Inscription
from ecosante.recommandations.models import Recommandation
from .utils import published_recommandation

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

@pytest.fixture(scope='function')
def client(app):
    return app.test_client()

@pytest.fixture(scope="session")
def app(request):
    indice_pollution_app = create_app_indice_pollution()
    indice_pollution_app.config['SQLALCHEMY_DATABASE_URI'] = DB_CONN
    with indice_pollution_app.app_context():
        db_indice_pollution = indice_pollution_app.extensions['sqlalchemy'].db
        db_indice_pollution.engine.execute('CREATE SCHEMA IF NOT EXISTS indice_schema')
        db_indice_pollution.create_all()
        db_indice_pollution.metadata.bind = db_indice_pollution.engine

    app = create_app()
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = DB_CONN
    with app.app_context():
        db = app.extensions['sqlalchemy'].db
        db.engine.execute('DROP TABLE IF EXISTS alembic_version;')
        db.metadata.bind = db.engine
        with cf.ProcessPoolExecutor() as pool:
            pool.submit(flask_migrate.upgrade)
        yield app
        db.metadata.drop_all()
        db.session.remove()
        db_indice_pollution.metadata.drop_all()
        db_indice_pollution.session.remove()
        db.session.close()
        db_indice_pollution.session.close()

@pytest.fixture(scope='function')
def _db(app):
    db = app.extensions['sqlalchemy'].db
    db.session.execute('TRUNCATE {} RESTART IDENTITY;'.format(
        ','.join(table.name 
                 for table in reversed(db.metadata.sorted_tables))))
    db.session.commit()
    return db

@pytest.fixture(scope='function')
def commune(db_session) -> Commune:
    from indice_pollution.history.models import Commune, Departement, Region, Zone
    region = Region(nom="Pays de la Loire", code="52")
    departement = Departement("Mayenne", "53", region.code)
    zone = Zone(type='commune', code='53130')
    commune = Commune(nom="Laval", code="53130", codes_postaux=["53000"], codeDepartement='53', zone=zone)
    db_session.add_all([region, departement, zone, commune])
    return commune

@pytest.fixture(scope='function')
def commune_commited(commune, db_session) -> Commune:
    db_session.commit()
    return commune

@pytest.fixture(scope='function')
def inscription(commune) -> Inscription:
    inscription = Inscription(ville_insee=commune.code, date_inscription='2021-09-28', indicateurs_media=["mail"], commune_id=commune.id, commune=commune)
    return inscription

@pytest.fixture(scope='function')
def inscription_alerte(commune) -> Inscription:
    inscription = Inscription(ville_insee=commune.code, date_inscription='2021-09-28', indicateurs_media=['mail'], commune_id=commune.id, commune=commune)
    inscription.indicateurs_frequence = ["alerte"]
    return inscription

@pytest.fixture(scope='function')
def mauvaise_qualite_air(commune, db_session) -> IndiceATMO:
    from indice_pollution.history.models import IndiceATMO
    from datetime import date
    indice = IndiceATMO(
        zone_id=commune.zone_id,
        date_ech=date.today(),
        date_dif=date.today(),
        no2=4, so2=4, o3=4, pm10=5, pm25=6,
        valeur=6)
    db_session.add(indice)
    return indice

@pytest.fixture(scope='function')
def bonne_qualite_air(commune, db_session) -> IndiceATMO:
    from indice_pollution.history.models import IndiceATMO
    from datetime import date
    indice = IndiceATMO(
        zone_id=commune.zone_id,
        date_ech=date.today(),
        date_dif=date.today(),
        no2=1, so2=1, o3=1, pm10=1, pm25=1,
        valeur=1)
    db_session.add(indice)
    return indice

@pytest.fixture(scope='function')
def recommandation(db_session) -> Recommandation:
    recommandation = published_recommandation()
    db_session.add(recommandation)
    return recommandation
