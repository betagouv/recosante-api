from datetime import date
from ecosante.extensions import db
from dataclasses import dataclass, asdict
from ecosante.inscription.models import Inscription
from flask.globals import current_app
from sqlalchemy.dialects import postgresql
from  sqlalchemy.sql.expression import func, nullslast
import uuid
import random
from typing import List, Set
from bs4 import BeautifulSoup

RECOMMANDATION_FILTERS = [
    ("qa_mauvaise", "👎", "Qualité de l’air mauvaise"),
    ("qa_bonne", "👍", "Qualité de l’air bonne"),
    ("menage", "🧹", "Ménage"),
    ("bricolage", "🔨", "Bricolage"),
    ("chauffage", "🔥", "Chauffage"),
    ("jardinage", "🌳", "Jardinage"),
    ("velo_trott_skate", "🚴", "Vélo, trotinette, skateboard"),
    ("transport_en_commun", "🚇", "Transport en commun"),
    ("voiture", "🚗", "Voiture"),
    ("activite_physique", "‍🏋", "Activité physique"),
    ("enfants", "🧒", "Enfants"),
    ("personnes_sensibles", "🤓", "Personnes sensibles"),
    ("autres", "🌐", "Autres"),
    ("hiver", "☃", "Hiver"),
    ("printemps", "⚘", "Printemps"),
    ("ete", "🌞", "Été"),
    ("automne", "🍂", "Automne"),
    ("particules_fines", "🌫️", "Pollution aux particules fines"),
    ("ozone", "🧪", "Pollution à l’ozone"),
    ("dioxyde_azote", "🐮", "Dioxyde d’azote"),
    ("dioxyde_soufre", "🛢️", "Dioxyde de soufre"),
    ("episode_pollution", "⚠️", "Épisode de pollution"),
    #("min_raep", "🤧", "Risque allergique lié à l’exposition des pollens")
]

@dataclass(repr=True)
class Recommandation(db.Model):
    recommandation_sanitized: str
    precisions_sanitized: str
    id: int = db.Column(db.Integer, primary_key=True)
    status: str = db.Column(db.String)
    recommandation: str = db.Column(db.String)
    precisions: str = db.Column(db.String)
    recommandation_format_SMS: str = db.Column(db.String)
    type_: str = db.Column("type", db.String)
    qa_mauvaise: bool = db.Column(db.Boolean, nullable=True)
    qa_bonne: bool = db.Column(db.Boolean, nullable=True)
    menage: bool = db.Column(db.Boolean)
    bricolage: bool = db.Column(db.Boolean)
    chauffage: List[str] = db.Column(postgresql.ARRAY(db.String))
    animal_de_compagnie: bool = db.Column(db.Boolean)
    jardinage: bool = db.Column(db.Boolean)
    balcon_terasse: bool = db.Column(db.Boolean)
    velo_trott_skate: bool = db.Column(db.Boolean)
    transport_en_commun: bool = db.Column(db.Boolean)
    voiture: bool = db.Column(db.Boolean)
    activite_physique: bool = db.Column(db.Boolean)
    enfants: bool = db.Column(db.Boolean)
    personnes_sensibles: bool = db.Column(db.Boolean)
    autres: bool = db.Column(db.Boolean)
    autres_conditions: str = db.Column(db.String)
    sources: str = db.Column(db.String)
    categorie: str = db.Column(db.String)
    objectif: str = db.Column(db.String)
    automne: bool = db.Column(db.Boolean, nullable=True)
    hiver: bool = db.Column(db.Boolean, nullable=True)
    printemps: bool = db.Column(db.Boolean, nullable=True)
    ete: bool = db.Column(db.Boolean, nullable=True)
    ozone: bool = db.Column(db.Boolean, nullable=True)
    dioxyde_azote: bool = db.Column(db.Boolean, nullable=True)
    dioxyde_soufre: bool = db.Column(db.Boolean, nullable=True)
    particules_fines: bool = db.Column(db.Boolean, nullable=True)
    episode_pollution: bool = db.Column(db.Boolean, nullable=True)
    min_raep: int = db.Column(db.Integer, nullable=True)
    personne_allergique: bool = db.Column(db.Boolean, nullable=True)
    ordre: int = db.Column(db.Integer, nullable=True)
    potentiel_radon: List[int] = db.Column(postgresql.ARRAY(db.Integer), nullable=True)
    montrer_dans: List[str] = db.Column(postgresql.ARRAY(db.String, dimensions=1), nullable=True)

    @property
    def velo(self) -> bool:
        return self.velo_trott_skate

    @property
    def sport(self) -> bool:
        return self.activite_physique

    @sport.setter
    def sport(self, value):
        self.activite_physique = value

    def _multi_getter(self, prefix, list_):
        to_return = []
        for v in list_:
            if getattr(self, prefix + v):
                to_return.append(v)
        return to_return

    def _multi_setter(self, prefix, list_, values):
        if type(values) != list:
            return
        for v in list_:
            setattr(self, prefix + v, v in values)

    @property
    def qa(self):
        return self._multi_getter("qa_", ['bonne', 'mauvaise'])

    @qa.setter
    def qa(self, value):
        self._multi_setter('qa_', ['bonne', 'mauvaise'], value)

    @property
    def polluants(self):
        return self._multi_getter("", ['ozone', 'dioxyde_azote', 'dioxyde_soufre', 'particules_fines'])

    @polluants.setter
    def polluants(self, value):
        self._multi_setter("", ['ozone', 'dioxyde_azote', 'dioxyde_soufre', 'particules_fines'], value)

    @property
    def population(self):
        return self._multi_getter("", ['enfants', 'personnes_sensibles', 'autres'])

    @population.setter
    def population(self, value):
        return self._multi_setter("", ['enfants', 'personnes_sensibles', 'autres'], value)

    @property
    def saison(self):
        return self._multi_getter("", ['hiver', 'printemps', 'ete', 'automne'])

    @saison.setter
    def saison(self, value):
        return self._multi_setter("", ['hiver', 'printemps', 'ete', 'automne'], value)

    @property
    def activites(self):
        return self._multi_getter("", ['menage', 'bricolage', 'jardinage', 'activite_physique'])

    @activites.setter
    def activites(self, value):
        return self._multi_setter("", ['menage', 'bricolage', 'jardinage', 'activite_physique'], value)

    @property
    def deplacement(self):
        return self._multi_getter("", ['velo_trott_skate', 'transport_en_commun', 'voiture'])

    @deplacement.setter
    def deplacement(self, value):
        return self._multi_setter("", ['velo_trott_skate', 'transport_en_commun', 'voiture'], value)

    @staticmethod
    def qualif_categorie(qualif):
        # On garde "tres_bon" et "mediocre" dans un souci de retro-compatibilité
        if qualif in (['bon', 'moyen'] + ['tres_bon', 'mediocre']):
            return "bon"
        elif qualif in ['degrade', 'mauvais', 'tres_mauvais', 'extrement_mauvais']:
            return "mauvais"

    def is_relevant_qualif(self, qualif):
        if not qualif and self.qa_bonne is None and self.qa_mauvaise is None:
            return True
        # Si la qualité de l’air est bonne
        # que la reco concerne la qualité de l’air bonne
        if self.qualif_categorie(qualif) == "bon" and self.qa_bonne:
            return True
        # Si la qualité de l’air est mauvaise
        # que la reco concerne la qualité de l’air mauvaise
        elif self.qualif_categorie(qualif) == "mauvais" and self.qa_mauvaise:
            return True
        # Sinon c’est pas bon
        else:
            return False

    @property
    def criteres(self) -> Set[str]:
        liste_criteres = ["menage", "bricolage", "jardinage", "velo", "transport_en_commun", "voiture", "sport"]
        return set([critere for critere in liste_criteres
                if getattr(self, critere)])

    def is_relevant(self, inscription: Inscription, qualif, polluants: List[str], raep: int, date_: date, media: str = 'newsletter', types: List[str] = ["generale", "episode_pollution", "pollens"]):
        #Inscription
        if inscription:
            if self.criteres and self.criteres.isdisjoint(inscription.criteres):
                return False
            if self.chauffage and set(self.chauffage).isdisjoint(set(inscription.chauffage or [])):
                return False
            if self.personnes_sensibles and (not inscription.personne_sensible and not inscription.has_enfants):
                return False
            if self.autres and inscription.personne_sensible:
                return False
            if self.enfants and not inscription.has_enfants:
                return False
            if self.personne_allergique is not None and self.personne_allergique != inscription.allergie_pollens:
                return False
        # Environnement
        if "episode_pollution" in types:
            if polluants:
                for polluant in polluants:
                    if getattr(self, polluant):
                        return True
                return False
            else:
                if self.polluants:
                    return False
        if "generale" in types:
            if qualif and (not self.qa_bonne == None or not self.qa_mauvaise == None):
                if not self.is_relevant_qualif(qualif):
                    return False
        # Pollens
        if "pollens" in types:
            if self.type_ == "pollens":
                if raep == None or raep == 0:
                    return False
                if 0 < raep < 4: #RAEP Faible
                    if inscription and inscription.allergie_pollens:
                        return date_.weekday() in [2, 5] #On envoie le mercredi et le samedi
                    else:
                        return False
                if raep >= 4:
                    if inscription and inscription.allergie_pollens:
                        return date_.weekday() in [2, 5] #On envoie le mercredi et le samedi
                    else:
                        return False
        # Voir https://stackoverflow.com/questions/44124436/python-datetime-to-season/44124490
        # Pour déterminer la saison
        season = date_.month%12//3 + 1
        if self.hiver and season != 1:
            return False
        elif self.printemps and season != 2:
            return False
        elif self.ete and season != 3:
            return False
        elif self.automne and season != 4:
            return False

        return media in self.montrer_dans and self.type_ in types

    def format(self, inscription):
        return self.recommandation if inscription.diffusion == 'mail' else self.recommandation_format_SMS

    @property
    def filtres(self):
        for attr, emoji, description in RECOMMANDATION_FILTERS:
            if getattr(self, attr):
                yield (attr, emoji, description)

    @classmethod
    def shuffled(cls, user_seed=None, preferred_reco=None, remove_reco=[]):
        recommandations = cls.published_query().all()
        user_seed = 1/(uuid.UUID(user_seed, version=4).int) if user_seed else random.random()
        random.Random(user_seed).shuffle(recommandations)
        recommandations = list(filter(lambda r: str(r.id) not in set(remove_reco), recommandations))
        if preferred_reco:
            recommandations = [cls.query.get(preferred_reco)] + recommandations
        return recommandations

    def delete(self):
        self.status = "deleted"

    @classmethod
    def published_query(cls):
        return cls.query.filter_by(status="published").order_by(func.random())

    def to_dict(self):
        return asdict(self)

    def sanitizer(self, s):
        if s is None:
            return s
        soup = BeautifulSoup(s, 'html.parser')
        for link in  soup.find_all('a'):
            link['target'] = '_blank'
        result = str(soup)
        for punc in ['?', '!', ';', ':']:
            result = result.replace(f' {punc}', f' {punc}')
        for punc in [';', ':']:
            result = result.replace(f'{punc} ', f'{punc} ')
        return result.replace("'", '’')


    @property
    def recommandation_sanitized(self) -> str:
        return self.sanitizer(self.recommandation)

    @property
    def precisions_sanitized(self) -> str:
        return self.sanitizer(self.precisions)

