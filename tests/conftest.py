from datetime import date, datetime, timedelta
from indice_pollution.history.models import zone
from indice_pollution.history.models.commune import Commune
from indice_pollution.history.models.indice_atmo import IndiceATMO
from indice_pollution.history.models.raep import RAEP
from indice_pollution.history.models.episode_pollution import EpisodePollution
import pytest
import os
import sqlalchemy as sa
from psycopg2.extras import DateRange
import concurrent.futures as cf
import flask_migrate
from ecosante import create_app
from indice_pollution import create_app as create_app_indice_pollution
from ecosante.newsletter.models import NewsletterHebdoTemplate
from ecosante.inscription.models import Inscription, WebpushSubscriptionInfo
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
        db.metadata.create_all()
        with cf.ProcessPoolExecutor() as pool:
            pool.submit(flask_migrate.upgrade)
        yield app
        db.metadata.drop_all()
        db_indice_pollution.metadata.drop_all()

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
    region = Region(nom="Pays de la Loire", code="52", tncc=4, nccenr='Pays de la Loire')
    zone_departement = Zone(type='departement', code='53')
    departement = Departement(nom="Mayenne", code="53", region=region, zone=zone_departement, tncc=3, nccenr='Mayenne')
    zone = Zone(type='commune', code='53130')
    commune = Commune(nom="Laval", code="53130", codes_postaux=["53000"], zone=zone, zone_pollution=departement.zone, departement=departement, tncc=0, nccenr='Laval')
    db_session.add_all([region, zone_departement, departement, zone, commune])
    return commune

@pytest.fixture(scope='function')
def commune_commited(commune, db_session) -> Commune:
    db_session.commit()
    return commune

@pytest.fixture(scope='function')
def inscription(commune) -> Inscription:
    inscription = Inscription(date_inscription='2021-09-28', indicateurs_media=["mail"], commune_id=commune.id, commune=commune, mail='test@example.com')
    return inscription

@pytest.fixture(scope='function')
def inscription_alerte(commune) -> Inscription:
    inscription = Inscription(ville_insee=commune.code, date_inscription='2021-09-28', indicateurs_media=['mail'], commune_id=commune.id, commune=commune, mail='test@example.com')
    inscription.indicateurs_frequence = ["alerte"]
    return inscription

@pytest.fixture(scope='function')
def inscription_notifications(db_session, inscription: Inscription) -> Inscription:
    inscription.indicateurs_media = ['notifications_web']
    db_session.add(inscription)
    db_session.commit()
    wp = WebpushSubscriptionInfo(
        inscription_id=inscription.id,
        data={
            "keys": {
                "auth": "Cbx6kg7FdlZHKZjaCUc_QQ", 
                "p256dh": "BNSBF5mKSirivNxvBtgzqviOcuFGvSHh21JGLr5m8G0Gb4lrW0jb0Uu5mk6pjTjk5ak2fMkgAOZs1_UfLXmv3K0"
            },
            "endpoint": "https://updates.push.services.mozilla.com/wpush/v2/pouet"
        }
    )
    db_session.add(wp)
    db_session.commit()
    return inscription

@pytest.fixture(scope='function')
def mauvaise_qualite_air(commune_commited, db_session) -> IndiceATMO:
    from indice_pollution.history.models import IndiceATMO
    from datetime import date
    indice = IndiceATMO(
        zone_id=commune_commited.zone_id,
        date_ech=datetime.now(),
        date_dif=datetime.now(),
        no2=4, so2=4, o3=4, pm10=5, pm25=6,
        valeur=6)
    db_session.add(indice)
    return indice

@pytest.fixture(scope='function')
def bonne_qualite_air(commune_commited, db_session) -> IndiceATMO:
    from indice_pollution.history.models import IndiceATMO
    from datetime import date
    indice = IndiceATMO(
        zone_id=commune_commited.zone_id,
        date_ech=datetime.now(),
        date_dif=datetime.now(),
        no2=1, so2=1, o3=1, pm10=1, pm25=1,
        valeur=1)
    db_session.add(indice)
    return indice

@pytest.fixture(scope='function')
def recommandation(db_session) -> Recommandation:
    recommandation = published_recommandation()
    db_session.add(recommandation)
    return recommandation

def make_episode(code_pol, commune):

    episode = EpisodePollution(
        code_pol=code_pol,
        etat="INFORMATION ET RECOMMANDATION",
        date_ech=datetime.now(),
        date_dif=datetime.now(),
        zone_id=commune.zone_pollution_id,
        zone=commune.zone_pollution
    )
    return episode

@pytest.fixture(scope='function')
def episode_soufre(commune_commited):
    return make_episode(1, commune_commited)

@pytest.fixture(scope='function')
def episode_azote(commune_commited):
    return make_episode(3, commune_commited)

@pytest.fixture(scope='function')
def episode_carbone(commune_commited):
    return make_episode(4, commune_commited)

@pytest.fixture(scope='function')
def episode_pm10(commune_commited):
    return make_episode(5, commune_commited)

@pytest.fixture(scope='function')
def episode_ozone(commune_commited):
    return make_episode(7, commune_commited)

@pytest.fixture(scope='function')
def episode_azote(commune_commited):
    return make_episode(8, commune_commited)


def make_raep(commune, raep):
    return RAEP(
        zone_id=commune.departement.zone_id,
        validity=DateRange(date.today(), date.today() + timedelta(weeks=1)),
        cypres=raep,
        noisetier=raep,
        aulne=raep,
        peuplier=raep,
        saule=raep,
        frene=raep,
        charme=raep,
        bouleau=raep,
        platane=raep,
        chene=raep,
        olivier=raep,
        tilleul=raep,
        chataignier=raep,
        rumex=raep,
        graminees=raep,
        plantain=raep,
        urticacees=raep,
        armoises=raep,
        ambroisies=raep,
        total=raep
    )

@pytest.fixture(scope='function')
def raep_eleve(db_session, commune_commited):
    raep = make_raep(commune_commited, 5)
    db_session.add(raep)
    return raep

@pytest.fixture(scope='function')
def raep_faible(db_session, commune_commited):
    raep = make_raep(commune_commited, 1)
    db_session.add(raep)
    return raep

@pytest.fixture(scope='function')
def raep_nul(db_session, commune_commited):
    raep = make_raep(commune_commited, 0)
    db_session.add(raep)
    return raep

@pytest.fixture(scope='function')
def template():
    return NewsletterHebdoTemplate(ordre=1, sib_id=1, _periode_validite=DateRange(date(2022,1, 1), date(2023, 1,1)))


@pytest.fixture(scope='function')
def templates(db_session):
    templates = [
        NewsletterHebdoTemplate(ordre=12, sib_id=14, _periode_validite=DateRange(date(2022,1, 1), date(2023, 1,1)), indicateurs=['indice_atmo', 'raep']),
        NewsletterHebdoTemplate(ordre=12, sib_id=13, _periode_validite=DateRange(date(2022,1, 1), date(2023, 1,1)), indicateurs=['indice_atmo']),
        NewsletterHebdoTemplate(ordre=11, sib_id=12, _periode_validite=DateRange(date(2022,1, 1), date(2023, 1,1)), enfants=True),
        NewsletterHebdoTemplate(ordre=11, sib_id=11, _periode_validite=DateRange(date(2022,1, 1), date(2023, 1,1)), enfants=False),
        NewsletterHebdoTemplate(ordre=10, sib_id=10, _periode_validite=DateRange(date(2022,1, 1), date(2023, 1,1))),
        NewsletterHebdoTemplate(ordre=7, sib_id=7, _periode_validite=DateRange(date(2022,1, 1), date(2023, 1,1))),
	    NewsletterHebdoTemplate(ordre=9, sib_id=9, _periode_validite=DateRange(date(2022,1, 1), date(2023, 1,1))),
	    NewsletterHebdoTemplate(ordre=5, sib_id=5, _periode_validite=DateRange(date(2022,1, 1), date(2023, 1,1))),
	    NewsletterHebdoTemplate(ordre=1, sib_id=1, _periode_validite=DateRange(date(2022,1, 1), date(2023, 1,1)))
    ]
    db_session.add_all(templates)
    return templates