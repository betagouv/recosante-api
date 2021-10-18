from flask.globals import current_app
from ecosante.inscription.models import Inscription, WebpushSubscriptionInfo
from ecosante.recommandations.models import Recommandation
from ecosante.newsletter.models import NewsletterDB
from ecosante.extensions import db, celery
from faker import Faker
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine, inspect, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert
from indice_pollution.history.models import IndiceATMO, EpisodePollution, Commune, Zone


def clone_data(model, model_b=None, **kwargs):
    # Ensure the model’s data is loaded before importing.
    if hasattr(model, "id"):
        model.id
    elif hasattr(model, "valeur"):
        model.valeur

    i = inspect(model.__class__)
    relationships_columns = i.relationships.keys()
    non_relationships_columns = [k for k in i.columns.keys() if k not in relationships_columns]
    data = {c: getattr(model, c) for c in non_relationships_columns}
    data.update(kwargs)
    return data

def clone_model(model, model_b=None, **kwargs):
    data = clone_data(model, model_b, **kwargs)
    if not model_b:
        clone = model.__class__(**data)
        return clone
    table = model.__table__
    for key in table.primary_key.columns.keys():
        if key in data:
            del data[key]
    for k, v in data.items():
        setattr(model_b, k, v)
    return model_b

def import_inscriptions(prod_session):
    faker = Faker(locale='fr_FR')

    staging_inscriptions = {i.id: i for i in Inscription.query.all()}
    communes = {c.insee: c.id for c in Commune.query.all()}
    for inscription in prod_session.query(Inscription).all():
        if not inscription.id in staging_inscriptions:
            new_inscription = clone_model(inscription)
            new_inscription.mail = faker.email()
            if inscription.commune:
                new_inscription.commune_id = communes[inscription.commune.insee]
            elif inscription.ville_insee:
                new_inscription.commune_id = communes[inscription.ville_insee]
            db.session.add(new_inscription)
        else:
            inscription = clone_model(inscription, staging_inscriptions[inscription.id])
            if inscription.commune:
                inscription.commune_id = communes[inscription.commune.insee]
            elif inscription.ville_insee:
                inscription.commune_id = communes[inscription.ville_insee]
            db.session.add(inscription)
    db.session.commit()

def import_webpush_subcriptions(prod_session):
    staging_subs = {w.id: w for w in WebpushSubscriptionInfo.query.all()}
    for wp in prod_session.query(WebpushSubscriptionInfo).all():
        if wp.id in staging_subs:
            continue
        new_wp = clone_model(wp)
        db.session.add(new_wp)
    db.session.commit()


def import_recommandations(prod_session):
    staging_recommandations = {r.id: r for r in Recommandation.query.all()}
    for recommandation in prod_session.query(Recommandation).all():
        db.session.add(clone_model(recommandation, staging_recommandations.get(recommandation.id)))
    db.session.commit()

def import_indices_generic(last_week, prod_session, model, date_col, staging_inscriptions=None, zones=None):
    table_name = f'{model.__table__.schema}."{model.__tablename__}"' if model.__table__.schema else model.__tablename__
    #db.session.execute(f'TRUNCATE TABLE {table_name}')
    #db.session.commit()
    #On commente pour l’instant à cause de deadlocks
    hours = int(((datetime.today() + timedelta(days=1)) - last_week).days * 24)
    for d in [(last_week + timedelta(hours=i)) for i in range(1, hours)]:
        indices = list()
        for indice in prod_session.query(model).filter(func.date_trunc('hour', date_col)==d).all():
            cloned_data = clone_data(indice)
            if staging_inscriptions and cloned_data['inscription_id'] not in staging_inscriptions:
                continue
            if zones and cloned_data['zone_id'] in zones:
                cloned_data['zone_id'] = zones[cloned_data['zone_id']]
            indices.append(cloned_data)
            if len(indices) == 10000:
                db.session.execute(
                    insert(
                        model.__table__,
                        indices
                    ).on_conflict_do_nothing()
                )
                db.session.commit()
                indices = []
        db.session.execute(
            insert(
                model.__table__,
                indices
            ).on_conflict_do_nothing()
        )
        db.session.commit()

def import_indices(prod_session):
    last_week = datetime.combine(
        (datetime.now() - timedelta(days=3)),
        datetime.min.time()
    )

    zones = {
        "region": {},
        "epci": {},
        "departement": {},
        "bassin_dair": {},
        "commune": {},
    }
    for z in Zone.query.all():
        zones[z.type][z.code] = z.id
    zones_production = {z.id: zones[z.type][z.code] for z in prod_session.query(Zone).all()}
    import_indices_generic(last_week, prod_session, IndiceATMO, IndiceATMO.date_dif, zones=zones_production)
    import_indices_generic(last_week, prod_session, EpisodePollution, EpisodePollution.date_dif, zones=zones_production)
    staging_inscriptions = set([i.id for i in Inscription.query.all()])
    import_indices_generic(last_week, prod_session, NewsletterDB, NewsletterDB.date, staging_inscriptions=staging_inscriptions)

@celery.task
def import_from_production():
    prod_url = os.getenv('SQLALCHEMY_PROD_DATABASE_URI')
    if not prod_url or celery.conf.env not in ('staging', 'dev'):
        current_app.logger.error("Quitting, can not import to an environment that is not staging or dev")
        return
    if str(db.engine.url) == prod_url:
        current_app.logger.error("Quitting, can not import from the same url as prod_url")
        return
    prod_engine = create_engine(prod_url)
    prod_Session = sessionmaker(prod_engine)
    prod_session = prod_Session()

    try:
        import_inscriptions(prod_session)
    except Exception as e:
        print(e)
        db.session.rollback()
        prod_session.rollback()
        return
    import_webpush_subcriptions(prod_session)
    import_recommandations(prod_session)
    import_indices(prod_session)