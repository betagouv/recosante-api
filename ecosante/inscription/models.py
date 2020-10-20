from .. import db
from sqlalchemy.dialects import postgresql
from datetime import date
from dataclasses import dataclass
from typing import List
import requests
import json
import os

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
    fumeur = db.Column(db.Boolean)

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
                for i in cls.query.all()
            ]
        }

    def send_success_email(self):
        from ecosante.newsletter.models import Newsletter
        newsletter = Newsletter(self)
        sib_apikey = os.getenv('SIB_APIKEY')
        success_template_id = os.getenv('SIB_SUCCESS_TEMPLATE_ID', 108)

        r = requests.post(
            'https://api.sendinblue.com/v3/contacts',
            headers={
                'accept': 'application/json',
                'api-key': sib_apikey 
            },
            json={
                "email": self.mail,
            }
        )
        r = requests.put(
            f'https://api.sendinblue.com/v3/contacts/{self.mail}',
            headers={
                'accept': 'application/json',
                'api-key': sib_apikey
            },
            json={
                "attributes": {
                    "VILLE": self.ville_name,
                    "QUALITE_AIR": newsletter.qualif,
                    "BACKGROUND_COLOR": newsletter.background,
                    "RECOMMANDATION": newsletter.recommandation.recommandation,
                    "PRECISIONS": newsletter.recommandation.precisions,
                }
            }
        )
        r = requests.post(
            'https://api.sendinblue.com/v3/smtp/email',
            headers={
                'accept': 'application/json',
                'api-key': sib_apikey
            },
            json={
                "sender": {
                    "name":"L'équipe écosanté",
                    "email":"contact@ecosante.data.gouv.fr"
                },
                "to": [{
                        "email": self.mail,
                }],
                "replyTo": {
                    "name":"L'équipe écosanté",
                    "email":"contact@ecosante.data.gouv.fr"
                },
                "templateId": success_template_id
            }
        )
