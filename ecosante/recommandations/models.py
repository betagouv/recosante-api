from itertools import compress
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
    ("qa_bonne", "👍", "Qualité de l’air bonne"),
    ("menage", "🧹", "Ménage"),
    ("bricolage", "🔨", "Bricolage"),
    ("chauffage_a_bois", "🔥", "Chauffage à bois"),
    ("jardinage", "🌳", "Jardinage"),
    ("velo_trott_skate", "🚴", "Vélo, trotinette, skateboard"),
    ("transport_en_commun", "🚇", "Transport en commun"),
    ("voiture", "🚗", "Voiture"),
    ("activite_physique", "‍🏋", "Activité physique"),
    ("enfants", "🧒", "Enfants"),
    ("personnes_sensibles", "🤓", "Personnes sensibles"),
    ("population_generale", "🌐", "Population générale"),
    ("hiver", "☃", "Hiver"),
    ("printemps", "⚘", "Printemps"),
    ("ete", "🌞", "Été"),
    ("automne", "🍂", "Automne"),
    ("particules_fines", "🌫️", "Pollution aux particules fines"),
    ("ozone", "🧪", "Pollution à l’ozone"),
    ("dioxyde_azote", "🐮", "Dioxyde d’azote"),
    ("dioxyde_soufre", "🛢️", "Dioxyde de soufre"),
    ("episode_pollution", "⚠️", "Épisode de pollution"),
    ("raep", "🤧", "Risque allergique lié à l’exposition des pollens")
]

class Recommandation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String)
    recommandation = db.Column(db.String)
    precisions = db.Column(db.String)
    recommandation_format_SMS = db.Column(db.String)
    qa_mauvaise = db.Column(CustomBoolean, nullable=True)
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
    enfants = db.Column(CustomBoolean)
    personnes_sensibles = db.Column(CustomBoolean)
    population_generale = db.Column(CustomBoolean)
    autres_conditions = db.Column(db.String)
    sources = db.Column(db.String)
    categorie = db.Column(db.String)
    objectif = db.Column(db.String)
    automne = db.Column(CustomBoolean, nullable=True)
    hiver = db.Column(CustomBoolean, nullable=True)
    printemps = db.Column(CustomBoolean, nullable=True)
    ete = db.Column(CustomBoolean, nullable=True)
    ozone = db.Column(CustomBoolean, nullable=True)
    dioxyde_azote = db.Column(CustomBoolean, nullable=True)
    dioxyde_soufre = db.Column(CustomBoolean, nullable=True)
    particules_fines = db.Column(CustomBoolean, nullable=True)
    episode_pollution = db.Column(CustomBoolean, nullable=True)
    raep = db.Column(CustomBoolean, nullable=True)

    @property
    def velo(self):
        return self.velo_trott_skate

    @property
    def sport(self):
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
        return self._multi_getter("", ['enfants', 'personnes_sensibles', 'population_generale'])

    @population.setter
    def population(self, value):
        return self._multi_setter("", ['enfants', 'personnes_sensibles', 'population_generale'], value)

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

    def is_relevant_qualif(self, qualif):
        # Si la qualité de l’air est bonne
        # que la reco concerne la qualité de l’air bonne
        # On garde "tres_bon" et "mediocre" dans un souci de retro-compatibilité
        if qualif in (['bon', 'moyen'] + ['tres_bon', 'mediocre']) and self.qa_bonne:
            return True
        # Si la qualité de l’air est mauvaise
        # que la reco concerne la qualité de l’air mauvaise
        elif qualif in ['degrade', 'mauvais', 'tres_mauvais', 'extrement_mauvais'] and self.qa_mauvaise:
            return True
        # Sinon c’est pas bon
        else:
            return False

    @property
    def criteres(self):
        liste_criteres = ["menage", "bricolage", "jardinage", "velo", "transport_en_commun",
            "voiture", "sport"]
        return set([critere for critere in liste_criteres
                if getattr(self, critere)])

    def is_relevant(self, inscription, qualif, polluants):
        #Inscription
        if self.criteres.isdisjoint(inscription.criteres) and self.criteres != set():
            return False
        if self.personnes_sensibles and not inscription.personne_sensible:
            return False
        if self.population_generale and inscription.personne_sensible:
            return False
        if self.enfants and not inscription.enfants:
            return False
        # Environnement
        if self.raep:
            return False
        if polluants:
            for polluant in polluants:
                if getattr(self, polluant):
                    return True
            return False
        if qualif:
            if not self.is_relevant_qualif(qualif):
                return False
        # Voir https://stackoverflow.com/questions/44124436/python-datetime-to-season/44124490
        # Pour déterminer la saison
        season = date.today().month%12//3 + 1
        if self.hiver and season != 1:
            return False
        elif self.printemps and season != 2:
            return False
        elif self.ete and season != 3:
            return False
        elif self.automne and season != 4:
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
        recommandations = cls.published_query().all()
        user_seed = 1/(uuid.UUID(user_seed, version=4).int) if user_seed else random.random()
        random.Random(user_seed).shuffle(recommandations)
        recommandations = list(filter(lambda r: str(r.id) not in set(remove_reco), recommandations))
        if preferred_reco:
            recommandations = [cls.query.get(preferred_reco)] + recommandations
        return recommandations

    @classmethod
    def get_relevant(cls, recommandations, inscription, qualif, polluants):
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

        try:
            return next(filter(lambda r: r.is_relevant(inscription, qualif, polluants), copy_recommandations))
        except StopIteration as e:
            current_app.logger.error(f"Unable to get recommandation for {inscription.mail} and '{qualif}'")
            raise e

    @classmethod
    def get_one(cls, inscription, qai, polluants):
        return cls.get_relevant(cls.shuffled(), inscription, qai, polluants)

    def delete(self):
        self.status = "deleted"

    @classmethod
    def published_query(cls):
        return cls.query.filter_by(status="published").order_by(cls.id)

    def to_dict(self):
        return {
            "id": self.id,
            "recommandation": self.recommandation,
            "precisions": self.precisions,
            "recommandation_format_SMS": self.recommandation_format_SMS,
            "qa_mauvaise": self.qa_mauvaise,
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
            "enfants": self.enfants,
            "personnes_sensibles": self.personnes_sensibles,
            "population_generale": self.population_generale,
            "autres_conditions": self.autres_conditions,
            "sources": self.sources,
            "categorie": self.categorie,
            "objectif": self.objectif,
            "automne": self.automne,
            "hiver": self.hiver,
            "ete": self.ete,
            "ozone": self.ozone,
            "dioxyde_azote": self.dioxyde_azote,
            "dioxyde_soufre": self.dioxyde_soufre,
            "particules_fines": self.particules_fines,
            "episode_pollution": self.episode_pollution
        }