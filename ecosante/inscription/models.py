from .. import db
from sqlalchemy.dialects import postgresql
from datetime import date
from dataclasses import dataclass
from typing import List

@dataclass
class Inscription(db.Model):
    id: int
    ville_entree: str
    ville_name: str
    ville_insee: str
    deplacement: List[str]
    sport: bool
    apa: bool
    activites: List[str]
    pathologie_respiratoire: bool
    allergie_pollen: bool
    fumeur: bool
    enfants: bool
    diffusion: str
    telephone: str
    mail: str
    frequence: str


    id = db.Column(db.Integer, primary_key=True)
    ville_entree = db.Column(db.String)
    ville_name = db.Column(db.String)
    ville_insee = db.Column(db.String)
    diffusion = db.Column(db.String)
    telephone = db.Column(db.String)
    mail = db.Column(db.String)
    frequence = db.Column(db.String)
    #Habitudes
    deplacement = db.Column(postgresql.ARRAY(db.String))
    sport = db.Column(db.Boolean)
    apa = db.Column(db.Boolean)
    activites = db.Column(postgresql.ARRAY(db.String))
    enfants = db.Column(db.Boolean)
    #Sante
    pathologie_respiratoire = db.Column(db.Boolean)
    allergie_pollen = db.Column(db.Boolean)
    fumeur = db.Column(db.Boolean)

    date_inscription = db.Column(db.Date())

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.date_inscription = date.today()

    def has_habitudes(self):
        return any([getattr(self, k) is not None for k in ['deplacement', 'sport', 'apa', 'activites', 'enfants']])

    def has_sante(self):
        return any([getattr(self, k) is not None for k in ['pathologie_respiratoire', 'allergie_pollen', 'fumeur']])
