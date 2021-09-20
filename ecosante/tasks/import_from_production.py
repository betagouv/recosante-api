from ecosante.inscription.models import Inscription
from ecosante.recommandations.models import Recommandation
from ecosante.newsletter.models import NewsletterDB
from ecosante.extensions import db, celery
from faker import Faker
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine, inspect, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert
from indice_pollution.history.models import IndiceATMO, EpisodePollution


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
    for inscription in prod_session.query(Inscription).all():
        if not inscription.id in staging_inscriptions:
            new_inscription = clone_model(inscription)
            new_inscription.mail = faker.email()
            db.session.add(new_inscription)
        else:
            db.session.add(clone_model(inscription, staging_inscriptions[inscription.id]))
    db.session.commit()

def import_recommandations(prod_session):
    staging_recommandations = {r.id: r for r in Recommandation.query.all()}
    for recommandation in prod_session.query(Recommandation).all():
        db.session.add(clone_model(recommandation, staging_recommandations.get(recommandation.id)))
    db.session.commit()

def import_indices_generic(last_week, prod_session, model, date_col):
    model.query.filter(date_col <= last_week).delete()
    db.session.commit()
    hours = int((datetime.today() - last_week).days * 24)
    for d in [(last_week + timedelta(hours=i)) for i in range(1, hours)]:
        indices = list()
        for indice in prod_session.query(model).filter(func.date_trunc('hour', date_col)==d).all():
            indices.append(clone_data(indice))
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

    import_indices_generic(last_week, prod_session, IndiceATMO, IndiceATMO.date_dif)
    import_indices_generic(last_week, prod_session, EpisodePollution, EpisodePollution.date_dif)
    import_indices_generic(last_week, prod_session, NewsletterDB, NewsletterDB.date)

@celery.task
def import_from_production():
    prod_url = os.getenv('SQLALCHEMY_PROD_DATABASE_URI')
    if not prod_url:
        return
    prod_engine = create_engine(prod_url)
    prod_Session = sessionmaker(prod_engine)
    prod_session = prod_Session()

    import_inscriptions(prod_session)
    import_recommandations(prod_session)
    import_indices(prod_session)