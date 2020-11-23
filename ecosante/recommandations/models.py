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
    niveau_difficulte = db.Column(db.String)
    autres_conditions = db.Column(db.String)
    sources = db.Column(db.String)
    categorie = db.Column(db.String)
    objectif = db.Column(db.String)
    automne = db.Column(CustomBoolean, nullable=True)
    hiver = db.Column(CustomBoolean, nullable=True)
    ete = db.Column(CustomBoolean, nullable=True)

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

    @property
    def qa(self):
        if self.qa_bonne:
            return "bonne"
        elif self.qa_moyenne:
            return "moyenne"
        elif self.qa_mauvaise:
            return "mauvaise"
        return ""

    @qa.setter
    def qa(self, value):
        if not value:
            return
        for v in ['bonne', 'moyenne', 'mauvaise']:
            setattr(self, f'qa_{v}', v == value)

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
        for v in ['automne', 'hiver']:
            setattr(self, v, v == value)
        setattr(self, "ete", value == "été")


    def is_relevant(self, inscription, qai):
        for critere in ["menage", "bricolage", "jardinage", "velo",
                        "transport_en_commun", "voiture", "sport",
                        "allergie_pollen", "enfants", "fumeur"]:
            if not getattr(inscription, critere) and getattr(self, critere):
                return False
        #Quand la qualité de l'air est mauvaise
        if qai and (qai < 8) and self.qa_mauvaise:
            return False
        #Voir https://stackoverflow.com/questions/44124436/python-datetime-to-season/44124490
        #Pour déterminer la saison
        season = (date.today().month%12 +3)//3
        if self.automne and season != 3:
            return False
        if self.hiver and season != 4:
            return False
        return True

    def format(self, inscription):
        return self.recommandation if inscription.diffusion == 'mail' else self.recommandation_format_SMS

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
