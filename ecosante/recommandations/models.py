from typing import SupportsRound
from flask.globals import current_app
from .. import db
import sqlalchemy.types as types
import uuid
import random
from datetime import date

class CustomBoolean(types.TypeDecorator):
    impl = db.Boolean

    def process_bind_param(self, value, dialect):
        if value is None:
            return False
        if type(value) is bool:
            return value
        return 'x' in value.lower() or 't' in value.lower()

RECOMMANDATION_FILTERS = [
    ("qa_mauvaise", "👎", "Qualité de l’air mauvaise"),
    ("qa_moyenne", "🤏", "Qualité de l’air moyenne"),
    ("qa_bonne", "👍", "Qualité de l’air bonne"),
    ("menage", "🧹", "Ménage"),
    ("bricolage", "🔨", "Bricolage"),
    ("chauffage_a_bois", "🔥", "Chauffage à bois"),
    ("jardinage", "🌳", "Jardinage"),
    ("velo_trott_skate", "🚴", "Vélo, trotinette, skateboard"),
    ("transport_en_commun", "🚇", "Transport en commun"),
    ("voiture", "🚗", "Voiture"),
    ("activite_physique", "‍🏋", "Activité physique"),
    ("allergies", "🤧", "Allergies aux pollens"),
    ("enfants", "🧒", "Enfants"),
    ("personnes_sensibles", "🤓", "Personnes sensibles"),
    ("automne", "🍂", "Automne"),
    ("hiver", "☃", "Hiver"),
    ("ete", "🌞", "Été"),
    ("particules_fines", "🌫️", "Pollution aux particules fines"),
    ("ozone", "🧪", "Pollution à l’ozone"),
    ("dioxyde_azote", "🐮", "Dioxyde d’azote"),
    ("dioxyde_soufre", "🛢️", "Dioxyde de soufre"),
    ("episode_pollution", "⚠️", "Épisode de pollution")
]

class Recommandation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recommandabilite = db.Column(db.String)
    recommandation = db.Column(db.String)
    precisions = db.Column(db.String)
    recommandation_format_SMS = db.Column(db.String)
    qa_mauvaise = db.Column(CustomBoolean, nullable=True)
    qa_moyenne = db.Column(CustomBoolean, nullable=True)
    qa_bonne = db.Column(CustomBoolean, nullable=True)
    menage = db.Column(CustomBoolean)
    bricolage = db.Column(CustomBoolean)
    chauffage_a_bois = db.Column(CustomBoolean)
    jardinage = db.Column(CustomBoolean)
    balcon_terasse = db.Column(CustomBoolean)
    velo_trott_skate = db.Column(CustomBoolean)
    transport_en_commun = db.Column(CustomBoolean)
    voiture = db.Column(CustomBoolean)
    activite_physique = db.Column(CustomBoolean)
    allergies = db.Column(CustomBoolean)
    enfants = db.Column(CustomBoolean)
    personnes_sensibles = db.Column(CustomBoolean)
    autres_conditions = db.Column(db.String)
    sources = db.Column(db.String)
    categorie = db.Column(db.String)
    objectif = db.Column(db.String)
    automne = db.Column(CustomBoolean, nullable=True)
    hiver = db.Column(CustomBoolean, nullable=True)
    ete = db.Column(CustomBoolean, nullable=True)
    ozone = db.Column(CustomBoolean, nullable=True)
    dioxyde_azote = db.Column(CustomBoolean, nullable=True)
    dioxyde_soufre = db.Column(CustomBoolean, nullable=True)
    particules_fines = db.Column(CustomBoolean, nullable=True)
    episode_pollution = db.Column(CustomBoolean, nullable=True)

    @property
    def velo(self):
        return self.velo_trott_skate

    @property
    def sport(self):
        return self.activite_physique

    @sport.setter
    def sport(self, value):
        self.activite_physique = value

    @property
    def allergie_pollen(self):
        return self.allergies

    @property
    def fumeur(self):
        return self.categorie and "tabagisme" in self.categorie.lower()

    @fumeur.setter
    def fumeur(self, value):
        if value:
            self.categorie = (self.categorie or "") + " tabagisme"

    def _multi_getter(self, prefix, list_):
        to_return = []
        for v in list_:
            if getattr(self, prefix + v):
                to_return.append(v)
        return to_return

    def _multi_setter(self, prefix, list_, values):
        if not values:
            return
        for v in list_:
            setattr(self, prefix + v, v in values)

    @property
    def qa(self):
        return self._multi_getter("qa_", ['bonne', 'moyenne', 'mauvaise'])

    @qa.setter
    def qa(self, value):
        self._multi_setter('qa_', ['bonne', 'moyenne', 'mauvaise'], value)

    @property
    def polluants(self):
        return self._multi_getter("", ['ozone', 'dioxyde_azote', 'dioxyde_soufre', 'particules_fines'])

    @polluants.setter
    def polluants(self, value):
        self._multi_setter("", ['ozone', 'dioxyde_azote', 'dioxyde_soufre', 'particules_fines'], value)


    @property
    def saison(self):
        if self.automne:
            return "automne"
        if self.hiver:
            return "hiver"
        if self.ete:
            return "été"
        return ""

    @saison.setter
    def saison(self, value):
        if not value:
            return
        for v in ['automne', 'hiver', 'ete']:
            setattr(self, v, v == value)

    def is_relevant(self, inscription, qa):
        for critere in ["menage", "bricolage", "jardinage", "velo",
                        "transport_en_commun", "voiture", "sport",
                        "allergie_pollen", "enfants", "fumeur"]:
            if not getattr(inscription, critere) and getattr(self, critere):
                return False
        if qa:
            # Quand la qualité de l'air est bonne
            if (not (qa <= 4)) and self.qa_bonne:
                return False
            # Quand la qualité de l'air est moyenne
            elif not(4 < qa <= 7) and self.qa_moyenne:
                return False
            # Quand la qualité de l'air est mauvaise
            elif not(7 < qa) and self.qa_mauvaise:
                return False
        # Voir https://stackoverflow.com/questions/44124436/python-datetime-to-season/44124490
        # Pour déterminer la saison
        season = (date.today().month%12 +3)//3
        if self.ete and season != 2:
            return False
        if self.automne and season != 3:
            return False
        if self.hiver and season != 4:
            return False
        return True

    def format(self, inscription):
        return self.recommandation if inscription.diffusion == 'mail' else self.recommandation_format_SMS

    @property
    def filtres(self):
        for attr, emoji, description in RECOMMANDATION_FILTERS:
            if getattr(self, attr):
                yield (attr, emoji, description)

    @classmethod
    def shuffled(cls, user_seed=None, preferred_reco=None, remove_reco=[]):
        recommandations = cls.query.filter_by(recommandabilite="Utilisable").order_by(cls.id).all()
        user_seed = 1/(uuid.UUID(user_seed, version=4).int) if user_seed else random.random()
        random.Random(user_seed).shuffle(recommandations)
        recommandations = list(filter(lambda r: str(r.id) not in set(remove_reco), recommandations))
        if preferred_reco:
            recommandations = [cls.query.get(preferred_reco)] + recommandations
        return recommandations

    @classmethod
    def get_revelant(cls, recommandations, inscription, qai):
        copy_recommandations = []
        same_category_recommandations = []
        last_month_newsletters = inscription.last_month_newsletters()
        recent_recommandation_ids = [
            nl.recommandation_id
            for nl in last_month_newsletters
        ]
        recent_recommandations = []
        last_category = "" if not last_month_newsletters else last_month_newsletters[0].recommandation.categorie
        for recommandation in recommandations:
            if not recommandation.id in recent_recommandation_ids:
                if recommandation.categorie == last_category:
                    same_category_recommandations.append(recommandation)
                else:
                    copy_recommandations.append(recommandation)
            else:
                recent_recommandations.append(recommandation)
        copy_recommandations.extend(same_category_recommandations)
        copy_recommandations.extend(recent_recommandations)

        return next(filter(lambda r: r.is_relevant(inscription, qai), copy_recommandations))

    @classmethod
    def get_one(cls, inscription, qai):
        return cls.get_revelant(cls.shuffled(), inscription, qai)


    def to_dict(self):
        return {
            "id": self.id,
            "recommandabilite": self.recommandabilite,
            "recommandation": self.recommandation,
            "precisions": self.precisions,
            "recommandation_format_SMS": self.recommandation_format_SMS,
            "qa_mauvaise": self.qa_mauvaise,
            "qa_moyenne": self.qa_moyenne,
            "qa_bonne": self.qa_bonne,
            "menage": self.menage,
            "bricolage": self.bricolage,
            "chauffage_a_bois": self.chauffage_a_bois,
            "jardinage": self.jardinage,
            "balcon_terasse": self.balcon_terasse,
            "velo_trott_skate": self.velo_trott_skate,
            "transport_en_commun": self.transport_en_commun,
            "voiture": self.voiture,
            "activite_physique": self.activite_physique,
            "allergies": self.allergies,
            "enfants": self.enfants,
            "personnes_sensibles": self.personnes_sensibles,
            "autres_conditions": self.autres_conditions,
            "sources": self.sources,
            "categorie": self.categorie,
            "objectif": self.objectif,
            "automne": self.automne,
            "hiver": self.hiver,
            "ete": self.ete,
            "ozone": self.ozone,
            "particules_fines": self.particules_fines
        }