from flask.globals import current_app
from .. import db
import sqlalchemy.types as types
import uuid
import random

class CustomBoolean(types.TypeDecorator):
    impl = db.Boolean

    def process_bind_param(self, value, dialect):
        return 'x' in value.lower()

class Recommandation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recommandabilite = db.Column(db.String)
    recommandation = db.Column(db.String)
    precisions = db.Column(db.String)
    recommandation_format_SMS = db.Column(db.String)
    qa_mauvaise = db.Column(CustomBoolean)
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
    niveau_difficulte = db.Column(db.String)
    autres_conditions = db.Column(db.String)
    sources = db.Column(db.String)
    categorie = db.Column(db.String)
    objectif = db.Column(db.String)

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

    def is_relevant(self, inscription, qai):
        for critere in ["menage", "bricolage", "jardinage", "velo",
                        "transport_en_commun", "voiture", "sport",
                        "allergie_pollen", "enfants", "fumeur"]:
            if not getattr(inscription, critere) and getattr(self, critere):
                return False

        #Quand la qualité de l'air est mauvaise
        if qai and (qai < 8) and self.qa_mauvaise:
            return False

        if self.id in [n.recommandation_id for n in inscription.last_month_newsletters()]:
            return False

        return True

    def format(self, inscription):
        return self.recommandation if inscription.diffusion == 'mail' else self.recommandation_format_SMS

    @classmethod
    def shuffled(cls, random_uuid=None, preferred_reco=None, remove_reco=[]):
        recommandations = cls.query.filter_by(recommandabilite="Utilisable").order_by(cls.id).all()
        recommandations = list(filter(lambda r: str(r.id) not in set(remove_reco), recommandations))
        seed = 1/(uuid.UUID(random_uuid, version=4).int) if random_uuid else random.random()
        random.Random(seed).shuffle(recommandations)
        if preferred_reco:
            recommandations = [cls.query.get(preferred_reco)] + recommandations
        return recommandations

    @classmethod
    def get_revelant(cls, recommandations, inscription, qai):
        return next(filter(lambda r: r.is_relevant(inscription, qai), recommandations))

    @classmethod
    def get_one(cls, inscription, qai):
        return cls.get_revelant(cls.shuffled(), inscription, qai)
