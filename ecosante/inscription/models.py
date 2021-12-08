from operator import and_
from sqlalchemy.orm import joinedload, relationship, selectinload
from indice_pollution.history.models import Commune, Departement
from ecosante.extensions import db
from ecosante.utils.funcs import generate_line, oxford_comma
from sqlalchemy.dialects import postgresql
from sqlalchemy import func
from datetime import (
    date,
    timedelta
)
from dataclasses import dataclass
from typing import List
import requests
from datetime import date
from sqlalchemy import text, or_
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm.attributes import flag_modified
import json

class WebpushSubscriptionInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    data = db.Column(postgresql.JSONB)
    inscription_id = db.Column(db.Integer, db.ForeignKey('inscription.id'), index=True)

@dataclass
class Inscription(db.Model):
    ville_insee: str

    id: int = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uid: str = db.Column(
        db.String(),
        server_default=text("generate_random_id('public', 'inscription', 'uid', 8)")
    )
    ville_entree: str = db.Column(db.String)
    ville_name: str = db.Column(db.String)
    _ville_insee: str = db.Column("ville_insee", db.String)
    commune_id: int = db.Column(db.Integer, db.ForeignKey(Commune.id))
    commune: Commune = db.relationship(Commune)
    diffusion: str = db.Column("diffusion", db.Enum("sms", "mail", name="diffusion_enum"), default="mail")
    telephone: str = db.Column(db.String)
    mail: str = db.Column(db.String)
    frequence: str = db.Column(db.Enum("quotidien", "pollution", name="frequence_enum"), default="quotidien")
    #Habitudes
    deplacement: str = db.Column(postgresql.ARRAY(db.String))
    apa: bool = db.Column(db.Boolean)
    activites: List[str] = db.Column(postgresql.ARRAY(db.String))
    enfants: str = db.Column("enfants", db.String)
    chauffage: List[str] = db.Column(postgresql.ARRAY(db.String))
    animaux_domestiques: List[str] = db.Column(postgresql.ARRAY(db.String))
    #Sante
    population: List[str] = db.Column(postgresql.ARRAY(db.String))
    #Misc
    deactivation_date: date = db.Column(db.Date)
    connaissance_produit: List[str] = db.Column(postgresql.ARRAY(db.String))
    ouvertures: List[date] = db.Column(postgresql.ARRAY(db.Date))
    recommandations: List[str] = db.Column(postgresql.ARRAY(db.String))
    notifications: List[str] = db.Column(postgresql.ARRAY(db.String))
    _webpush_subscriptions_info: List[WebpushSubscriptionInfo] = relationship("WebpushSubscriptionInfo", backref="inscription")
    #Indicateurs
    indicateurs: List[str] = db.Column(postgresql.ARRAY(db.String), default=['indice_atmo', 'raep'])
    indicateurs_frequence: List[str] = db.Column(postgresql.ARRAY(db.String), default=['quotidien'])
    indicateurs_media: List[str] = db.Column(postgresql.ARRAY(db.String), default=['mail'])
    #Recommandations
    recommandations_actives: List[str] = db.Column(postgresql.ARRAY(db.String), default=['oui'])
    recommandations_frequence: List[str] = db.Column(postgresql.ARRAY(db.String), default=['quotidien'])
    recommandations_media: List[str] = db.Column(postgresql.ARRAY(db.String), default=['mail'])

    last_month_newsletters = relationship(
        "NewsletterDB",
        order_by='desc(NewsletterDB.date)',
        primaryjoin="""and_(
            Inscription.id == NewsletterDB.inscription_id,
            NewsletterDB.date >= text("current_date - integer '30'")
        )""",
        viewonly=True
    )

    last_newsletters_hebdo = relationship(
        "NewsletterDB",
        order_by='desc(NewsletterDB.date)',
        primaryjoin="""and_(
            Inscription.id == NewsletterDB.inscription_id,
            NewsletterDB.newsletter_hebdo_template_id != None
        )""",
        viewonly=True
    )

    date_inscription = db.Column(db.Date())
    _cache_api_commune = db.Column("cache_api_commune", db.JSON())

    def __init__(self, **kwargs):
        kwargs.setdefault("date_inscription", date.today())
        super().__init__(**kwargs)

    def has_deplacement(self, deplacement):
        return self.deplacement and deplacement in self.deplacement

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

    def activite_setter(self, activite, value):
        if type(self.activites) != list:
            self.activites = []
        if value and activite not in self.activites:
            self.activites.append(activite)
        elif not value and activite in self.activites:
            self.activites.remove(activite)
        flag_modified("activites")

    @property
    def criteres(self):
        liste_criteres = ["menage", "bricolage", "jardinage", "velo", "transport_en_commun",
            "voiture", "sport"]
        return set([critere for critere in liste_criteres
                if getattr(self, critere)])

    @hybrid_property
    def bricolage(self):
        return self.has_activite("bricolage")
    @bricolage.setter
    def bricolage(self, value):
        return self.activite_setter("bricolage", value)

    @hybrid_property
    def menage(self):
        return self.has_activite("menage")
    @menage.setter
    def menage(self, value):
        return self.activite_setter("menage", value)

    @hybrid_property
    def jardinage(self):
        return self.has_activite("jardinage")
    @jardinage.setter
    def jardinage(self, value):
        return self.activite_setter("jardinage", value)

    @hybrid_property
    def sport(self):
        return self.has_activite("sport")
    @sport.setter
    def sport(self, value):
        return self.activite_setter("sport", value)

    @property
    def personne_sensible(self):
        if type(self.population) != list:
            return False
        return "pathologie_respiratoire" in self.population\
                or "allergie_pollens" in self.population\
                or self.has_enfants

    @hybrid_property
    def allergie_pollens(self):
        return type(self.population) == list and "allergie_pollens" in self.population
    @allergie_pollens.setter
    def allergie_pollens(self, value):
        if not type(self.population) == list:
            self.population = []
        if value and not "allergie_pollens" in self.population:
            self.population.append("allergie_pollens")
        elif not value and "allergie_pollens" in self.population:
            self.population.remove("allergie_pollens")
        flag_modified(self, 'population')

    @hybrid_property
    def pathologie_respiratoire(self):
        return type(self.population) == list and "pathologie_respiratoire" in self.population
    @pathologie_respiratoire.setter
    def pathologie_respiratoire(self, value):
        if not type(self.population) == list:
            self.population = []
        if value and not "pathologie_respiratoire" in self.population:
            self.population += ["pathologie_respiratoire"]
        elif not value and "pathologie_respiratoire" in self.population:
            self.population.remove("pathologie_respiratoire")
        flag_modified(self, 'population')

    @property
    def has_enfants(self):
        return self.enfants == 'oui'

    def set_cache_api_commune(self):
        if not self.ville_insee:
            return
        r = requests.get(f'https://geo.api.gouv.fr/communes/{self.ville_insee}',
            params={
                "fields": "nom,centre,region,codesPostaux,departement",
                "format": "json",
                "geometry": "centre"
            }
        )
        self._cache_api_commune = r.json()
        db.session.add(self)
        db.session.commit()

    @hybrid_property
    def cache_api_commune(self):
        if not self.ville_insee:
            return {}
        if not self._cache_api_commune:
            self.set_cache_api_commune()
        return self._cache_api_commune
    @cache_api_commune.setter
    def cache_api_commune(self, value):
        self._cache_api_commune = value


    def cache_api_commune_get(self, key, default_value=None):
        if self._cache_api_commune and not key in self._cache_api_commune:
            self._cache_api_commune = None
        return self.cache_api_commune.get(key, default_value)

    @hybrid_property
    def ville_insee(self):
        return self._ville_insee
    @ville_insee.setter
    def ville_insee(self, value):
        self._ville_insee = value
        self.set_cache_api_commune()

    @property
    def ville_centre(self):
        return self.cache_api_commune_get('centre')

    @property
    def ville_nom(self):
        return self.cache_api_commune_get('nom')

    @property
    def ville_codes_postaux(self):
        return self.cache_api_commune_get('codesPostaux')

    @property
    def ville(self):
        return {
            "nom": self.ville_nom,
            "code": self.ville_insee,
            "codes_postaux": self.ville_codes_postaux
        }

    @property
    def region_name(self):
        return self.cache_api_commune_get('region', {}).get('nom')

    @property
    def departement(self):
        return self.cache_api_commune_get('departement', {})

    @property
    def is_active(self):
        return self.deactivation_date is None or self.deactivation_date > date.today()

    @classmethod
    def active_query(cls):
        return db.session.query(cls)\
            .filter((Inscription.deactivation_date == None) | (Inscription.deactivation_date > date.today()))\
            .filter(Inscription.ville_insee.isnot(None) | Inscription.commune_id.isnot(None))\
            .filter(Inscription.mail != "", Inscription.mail.isnot(None))

    def unsubscribe(self):
        from ecosante.inscription.tasks.send_unsubscribe import send_unsubscribe, send_unsubscribe_error
        self.deactivation_date = date.today()
        db.session.add(self)
        db.session.commit()
        send_unsubscribe.apply_async(
            (self.mail,),
            link_error=send_unsubscribe_error.s(),
            queue='send_email',
            routing_key='send_email.unsubscribe'
        )

    @classmethod
    def generate_csv(cls):
        yield generate_line([
            'region',
            'ville',
            'deplacement',
            'activites',
            'pathologie_respiratoire',
            'allergie_pollens',
            'enfants',
            'diffusion',
            'mail',
            'frequence',
            'date_inscription',
            'deactivation_date'
        ])
        for inscription in cls.active_query().all():
            yield inscription.csv_line()
    
    def csv_line(self):
        return generate_line([
            self.region_name,
            self.ville_nom,
            self.deplacement,
            self.activites,
            self.pathologie_respiratoire,
            self.allergie_pollens,
            self.enfants,
            self.diffusion,
            self.mail,
            self.frequence,
            self.date_inscription,
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

    @classmethod
    def query_inactive_accounts(cls):
        return db.session.query(cls)\
            .filter(
                cls.deactivation_date != None,
                cls.deactivation_date <= (date.today() - timedelta(days=30))
            )

    @classmethod
    def deactivate_accounts(cls):
        r = cls.query_inactive_accounts()\
            .filter(cls.mail != None)\
            .update({"mail": None})
        db.session.commit()
        return r

    @property
    def diffusion_liste(self):
        if self.diffusion:
            return [self.diffusion]
        else:
            return self.diffusion

    @diffusion_liste.setter
    def diffusion_liste(self, value):
        self.liste_setter(value, 'diffusion')

    def liste_setter(self, value, attribute):
        if type(value) == list:
            if len(value) >= 1:
                setattr(self, attribute, value[0])
                return
        self.diffusion = None

    @property
    def webpush_subscriptions_info(self):
        return self._webpush_subscriptions_info
    @webpush_subscriptions_info.setter
    def webpush_subscriptions_info(self, value):
        self.add_webpush_subscriptions_info(value)

    @property
    def indicateurs_medias_lib(self):
        return oxford_comma(
            s.replace('notifications_web', 'notification')
            for s in self.indicateurs_media
        )

    def add_webpush_subscriptions_info(self, value):
        try:
            j_new_value = json.loads(value)
        except json.JSONDecodeError as e:
            return None
        if isinstance(j_new_value, dict):
            j_new_value = [j_new_value]
        elif isinstance(j_new_value, list):
            pass
        else:
            return None
        for data in j_new_value:
            if any([self.is_equal_webpush_subscriptions_info(sub.data, data) for sub in self.webpush_subscriptions_info]):
                return
            wp = WebpushSubscriptionInfo(data=data)
            wp.inscription_id = self.id
            self.webpush_subscriptions_info.append(wp)
            db.session.add(wp)

    @classmethod
    def is_equal_webpush_subscriptions_info(cls, val1, val2):
        return val1['endpoint'] == val2['endpoint'] and\
               val1['keys'] == val2['keys']

    @classmethod
    def is_valid_webpush_subscriptions_info(cls, val):
        return 'endpoint' in val and 'keys' in val

    def has_indicateur(self, indicateur):
        return isinstance(self.indicateurs, list) and indicateur in self.indicateurs

    @classmethod
    def export_query(cls, only_to=None, filter_already_sent=True, media='mail', type_='quotidien'):
        from ecosante.newsletter.models import NewsletterDB
        query = Inscription.active_query()
        if only_to:
            query = query.filter(Inscription.mail.in_(only_to))
        if filter_already_sent:
            query_nl = NewsletterDB.query\
                .filter(
                    NewsletterDB.date==date.today(),
                    NewsletterDB.inscription.has(Inscription.indicateurs_media.contains([media])))\
                .with_entities(
                    NewsletterDB.inscription_id
            )
            if type_ == 'quotidien':
                query_nl = query_nl.filter(
                    NewsletterDB.label != None,
                    NewsletterDB.label != "",
                    NewsletterDB.newsletter_hebdo_template_id == None
                )
            elif type_ == 'hebdomadaire':
                query_nl = query_nl.filter(NewsletterDB.newsletter_hebdo_template_id != None)
            query = query.filter(Inscription.id.notin_(query_nl))
        query = query\
            .filter(or_(Inscription.indicateurs_frequence == None, ~Inscription.indicateurs_frequence.contains(["hebdomadaire"])))\
            .filter(Inscription.commune_id != None)\
            .filter(Inscription.date_inscription < str(date.today()))

        if type_ == 'hebdomadaire':
            query = query.filter(
                Inscription.recommandations_actives.contains(['oui'])
            ).options(
                selectinload(
                    Inscription.last_newsletters_hebdo
                )
            )
        elif type_ == 'quotidien':
	        query = query\
                .filter(Inscription.indicateurs_media.contains([media]))\
                .options(
                selectinload(
                    Inscription.last_month_newsletters
                )
            )

        return query.options(
            joinedload(
                Inscription.commune
            ).joinedload(
                Commune.departement,
            ).joinedload(
                Departement.region
            )
        ).populate_existing()