from .. import db
from ecosante.utils.funcs import generate_line
from datetime import date
from dataclasses import dataclass
from typing import List
from sqlalchemy.dialects import postgresql

@dataclass
class Avis(db.Model):
    id: int
    mail: str
    decouverte: List[str]
    satisfaction_nombre_recommandation: bool
    satisfaction_frequence: str
    recommandabilite: int
    encore: bool
    autres_thematiques: str

    id = db.Column(db.Integer, primary_key=True)
    mail = db.Column(db.String)
    decouverte = db.Column(postgresql.ARRAY(db.String))
    satisfaction_nombre_recommandation = db.Column(db.Boolean)
    satisfaction_frequence = db.Column(db.String)
    recommandabilite = db.Column(db.Integer)
    encore = db.Column(db.Boolean)
    autres_thematiques = db.Column(db.String)

    date = db.Column(db.Date())

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.date = date.today()

    @classmethod
    def generate_csv(cls):
        headers = [
            "id",
            "mail",
            "decouverte",
            "satisfaction_nombre_recommandation",
            "satisfaction_frequence",
            "recommandabilite",
            "encore",
            "autres_thematiques"
        ]
        yield generate_line(headers)
        for row in cls.query.all():
            yield generate_line([getattr(row, h) for h in headers])
