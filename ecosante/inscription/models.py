from ecosante.extensions import db
from ecosante.utils.funcs import (
    convert_boolean_to_oui_non,
    generate_line
)
from sqlalchemy.dialects import postgresql
from sqlalchemy import func
from datetime import (
    date,
    timedelta
)
from dataclasses import dataclass
from typing import List
import requests
import json
from datetime import date

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
    enfants: bool
    diffusion: str
    telephone: str
    mail: str
    frequence: str


    id = db.Column(db.Integer, primary_key=True)
    ville_entree = db.Column(db.String)
    ville_name = db.Column(db.String)
    ville_insee = db.Column(db.String)
    diffusion = db.Column(db.Enum("sms", "mail", name="diffusion_enum"))
    _telephone = db.Column("telephone", db.String)
    mail = db.Column(db.String)
    frequence = db.Column(db.Enum("quotidien", "pollution", name="frequence_enum"))
    #Habitudes
    deplacement = db.Column(postgresql.ARRAY(db.String))
    _sport = db.Column("sport", db.Boolean)
    apa = db.Column(db.Boolean)
    activites = db.Column(postgresql.ARRAY(db.String))
    enfants = db.Column(db.Boolean)
    #Sante
    pathologie_respiratoire = db.Column(db.Boolean)
    allergie_pollen = db.Column(db.Boolean)
    #Misc
    deactivation_date = db.Column(db.Date)

    newsletters = db.relationship(
        "ecosante.newsletter.models.NewsletterDB",
        backref="newsletter",
        lazy="dynamic"
    )

    date_inscription = db.Column(db.Date())
    _cache_api_commune = db.Column("cache_api_commune", db.String())

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.date_inscription = date.today()

    def has_deplacement(self, deplacement):
        return self.deplacement and deplacement in self.deplacement

    @staticmethod
    def convert_telephone(value):
        if not value:
            return value
        if value[:1] == "+":
            return value
        if value[:2] in ("00", "33"):
            return value
        if value[:1] == "0":
            return "+33" + value[1:]
        return "+33" + value

    @property
    def telephone(self):
        return self.convert_telephone(self._telephone)

    @telephone.setter
    def telephone(self, value):
        self._telephone = self.convert_telephone(value)

    @property
    def voiture(self):
        return self.has_deplacement("voiture")

    @property
    def velo(self):
        return self.has_deplacement("velo")
    @property
    def transport_en_commun(self):
        return self.has_deplacement("tec")

    def has_activite(self, activite):
        return self.activites and activite in self.activites

    @property
    def criteres(self):
        liste_criteres = ["menage", "bricolage", "jardinage", "velo", "transport_en_commun",
            "voiture", "sport"]
        return set([critere for critere in liste_criteres
                if getattr(self, critere)])

    @property
    def bricolage(self):
        return self.has_activite("bricolage")

    @property
    def menage(self):
        return self.has_activite("menage")

    @property
    def jardinage(self):
        return self.has_activite("jardinage")

    @property
    def sport(self):
        return self.has_activite("sport")

    @property
    def personne_sensible(self):
        return self.enfants or self.pathologie_respiratoire or self.allergie_pollen

    @property
    def cache_api_commune(self):
        if not self._cache_api_commune:
            if not self.ville_insee:
                return
            r = requests.get(f'https://geo.api.gouv.fr/communes/{self.ville_insee}',
                params={
                    "fields": "nom,centre,region",
                    "format": "json",
                    "geometry": "centre"
                }
            )
            self._cache_api_commune = r.text
            db.session.add(self)
            db.session.commit()
        return json.loads(self._cache_api_commune)

    @property
    def ville_centre(self):
        return self.cache_api_commune.get('centre')

    @property
    def region_name(self):
        return self.cache_api_commune.get('region', {}).get('nom')

    @property
    def is_active(self):
        return not self.deactivation_date

    def last_month_newsletters(self):
        from ecosante.newsletter.models import NewsletterDB

        last_month = date.today() - timedelta(days=30)

        query_sent_nl = db.session\
            .query(func.max(NewsletterDB.id))\
            .filter(
                NewsletterDB.date>=last_month,
                NewsletterDB.inscription_id==self.id
            )\
            .group_by(
                NewsletterDB.date
            ).order_by(
                NewsletterDB.date.desc()
            )
        return db.session\
            .query(NewsletterDB)\
            .filter(NewsletterDB.id.in_(query_sent_nl))\
            .all()

    @classmethod
    def active_query(cls):
        return db.session.query(cls).filter(Inscription.deactivation_date==None)

    def unsubscribe(self):
        from ecosante.inscription.tasks.send_unsubscribe import send_unsubscribe, send_unsubscribe_error
        self.deactivation_date = date.today()
        db.session.add(self)
        db.session.commit()
        send_unsubscribe.apply_async(
            (self.mail,),
            link_error=send_unsubscribe_error.s()
        )

    @classmethod
    def generate_csv(cls):
        yield generate_line([
            'ville',
            'deplacement',
            'activites',
            'pathologie_respiratoire',
            'allergie_pollen',
            'enfants',
            'diffusion',
            'telephone',
            'mail',
            'frequence',
            'deactivation_date'
        ])
        for inscription in cls.active_query().all():
            yield inscription.csv_line()
    
    def csv_line(self):
        return generate_line([
            self.ville_name, 
            self.deplacement,
            self.activites,
            self.pathologie_respiratoire,
            self.allergie_pollen,
            self.enfants,
            self.diffusion,
            self.telephone,
            self.mail,
            self.frequence,
            self.deactivation_date
        ])

    @classmethod
    def export_geojson(cls):
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": [],
                    "geometry": i.ville_centre
                }
                for i in cls.active_query().all()
            ]
        }