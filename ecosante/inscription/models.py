from .. import db
from sqlalchemy.dialects import postgresql
from datetime import date

class Inscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ville_entree = db.Column(db.String)
    ville_name = db.Column(db.String)
    ville_insee = db.Column(db.String)
    deplacement = db.Column(postgresql.ARRAY(db.String))
    sport = db.Column(db.Boolean)
    apa = db.Column(db.Boolean)
    activites = db.Column(postgresql.ARRAY(db.String))
    pathologie_respiratoire = db.Column(db.Boolean)
    allergie_pollen = db.Column(db.Boolean)
    fumeur = db.Column(db.Boolean)
    enfants = db.Column(db.Boolean)
    diffusion = db.Column(db.String)
    telephone = db.Column(db.String)
    mail = db.Column(db.String)
    frequence = db.Column(db.String)

    date_inscription = db.Column(db.Date())

    def __init__(self, **kwargs):
        columns = self.__table__.columns
        data = dict(filter(lambda v: f'inscription.{v[0]}' in columns, kwargs.items()))
        super().__init__(**data)
        self.date_inscription = date.today()