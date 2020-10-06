from .. import db
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
