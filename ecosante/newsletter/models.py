from dataclasses import dataclass
from datetime import datetime
from sqlalchemy import text
from ecosante.inscription.blueprint import inscription
from flask import current_app
from ecosante.inscription.models import Inscription
from ecosante.recommandations.models import Recommandation
from ecosante.utils.funcs import (
    convert_boolean_to_oui_non,
    generate_line
)
from ecosante.extensions import db
from indice_pollution import bulk, today, forecast as get_forecast

@dataclass
class Newsletter:
    date: datetime
    recommandation: Recommandation
    inscription: Inscription
    forecast: dict

    def __init__(self, inscription, seed=None, preferred_reco=None, recommandations=None, forecast=None, recommandation_id=None):
        recommandations = recommandations or Recommandation.shuffled(user_seed=seed, preferred_reco=preferred_reco)
        self.date = today()
        self.inscription = inscription
        self._forecast = None
        if not 'label' in self.today_forecast:
            current_app.logger.error(f'No label for forecast for inscription: id: {inscription.id} insee: {inscription.ville_insee}')
        if not 'couleur' in self.today_forecast:
            current_app.logger.error(f'No couleur for forecast for inscription: id: {inscription.id} insee: {inscription.ville_insee}')

        self.recommandation =\
             Recommandation.query.get(recommandation_id) or\
             Recommandation.get_revelant(
                recommandations,
                inscription,
                self.qualif
            )

    @property
    def forecast(self):
        if not self._forecast:
            self.init_forecast()
        return self._forecast

    def init_forecast(self, forecast=None):
        try:
            self._forecast = forecast or get_forecast(self.inscription.ville_insee, self.date, True)
        except KeyError as e:
            current_app.logger.error(f'Unable to find region for {inscription.ville_name} ({inscription.ville_insee})')
            current_app.logger.error(e)

    @classmethod
    def from_inscription_id(cls, inscription_id):
        inscription = Inscription.query.get(inscription_id)
        return cls(inscription)

    @classmethod
    def from_csv_line(cls, line):
        inscription = Inscription.query.filter_by(mail=line['MAIL']).first()
        return cls(
            inscription,
            recommandation_id=line['ID RECOMMANDATION']
        )

    @property
    def today_forecast(self):
        try:
            return next(iter([v for v in self.forecast['data'] if v['date'] == str(self.date)]), dict())
        except (TypeError, ValueError, StopIteration) as e:
            current_app.logger.error(f'Unable to get forecast for inscription: id: {inscription.id} insee: {inscription.ville_insee}')
            current_app.logger.error(e)
            return dict()

    @property
    def qualif(self):
        return self.today_forecast.get('indice')

    @property
    def label(self):
        return self.today_forecast.get('label')
    
    @property
    def couleur(self):
        return self.today_forecast.get('couleur')

    @classmethod
    def generate_csv(cls, preferred_reco=None, seed=None, remove_reco=[]):
        yield generate_line([
            'VILLE',
            'Moyens de transport',
            "Activité sportive",
            "Activité physique adaptée",
            "Activités",
            "Pathologie respiratoire",
            "Allergie aux pollens",
            "Fume",
            "Enfants",
            'MAIL',
            'FORMAT',
            'SMS',
            "Fréquence",
            "Consentement",
            "Date d'inscription",
            "QUALITE_AIR",
            "BACKGROUND_COLOR",
            "Région",
            "LIEN_AASQA",
            "RECOMMANDATION",
            "PRECISIONS",
            "ID RECOMMANDATION"
        ])
        for newsletter in cls.export(preferred_reco, seed, remove_reco):
            yield newsletter.csv_line()

    @classmethod
    def export(cls, preferred_reco=None, user_seed=None, remove_reco=[]):
        recommandations = Recommandation.shuffled(user_seed=user_seed, preferred_reco=preferred_reco, remove_reco=remove_reco)
        insee_region = {i.ville_insee: i.region_name for i in Inscription.query.distinct(Inscription.ville_insee)}
        insee_forecast = bulk(insee_region)
        for inscription in Inscription.query.all():
            newsletter = cls(
                inscription,
                recommandations=recommandations,
                forecast=insee_forecast[inscription.ville_insee]["forecast"]
            )
            if inscription.frequence == "pollution" and newsletter.qualif and newsletter.qualif in ['mauvais', 'tres_mauvais', 'extrement_mauvais']:
                continue
            yield newsletter

    def csv_line(self):
        return generate_line([
            self.inscription.ville_name,
            "; ".join(self.inscription.deplacement or []),
            convert_boolean_to_oui_non(self.inscription.sport),
            "Non",
            ";".join(self.inscription.activites or []),
            convert_boolean_to_oui_non(self.inscription.pathologie_respiratoire),
            convert_boolean_to_oui_non(self.inscription.allergie_pollen),
            convert_boolean_to_oui_non(self.inscription.fumeur),
            convert_boolean_to_oui_non(self.inscription.enfants),
            self.inscription.mail,
            self.inscription.diffusion,
            self.inscription.telephone,
            self.inscription.frequence,
            "Oui",
            self.inscription.date_inscription,
            self.qualif,
            self.background,
            self.forecast['metadata']['region']['nom'],
            self.forecast['metadata']['region']['website'],
            self.recommandation.format(self.inscription),
            self.recommandation.precisions,
            self.recommandation.id
        ])

class NewsletterDB(db.Model, Newsletter):
    __tablename__ = "newsletter"
    id = db.Column(db.Integer, primary_key=True)
    short_id = db.Column(
        db.String(),
        server_default=text("generate_random_id('public', 'newsletter', 'short_id', 8)")
    )
    inscription_id = db.Column(db.Integer, db.ForeignKey('inscription.id'))
    inscription = db.relationship("Inscription", backref="inscription")
    recommandation_id = db.Column(db.Integer, db.ForeignKey('recommandation.id'))
    recommandation = db.relationship("Recommandation")
    date = db.Column(db.Date())
    qai = db.Column(db.Integer())
    qualif = db.Column(db.String())
    appliquee = db.Column(db.Boolean())
    avis = db.Column(db.String())

    def __init__(self, newsletter):
        self.inscription = newsletter.inscription
        self.inscription_id = newsletter.inscription.id
        self.recommandation = newsletter.recommandation
        self.recommandation_id = newsletter.recommandation.id
        self.date = newsletter.date
        self.qualif = newsletter.qualif
        self._forecast = newsletter._forecast

    def attributes(self):
        to_return = {
            'FORMAT': self.inscription.diffusion,
            'QUALITE_AIR': self.label,
            'LIEN_AASQA': self.forecast['metadata']['region']['website'],
            'RECOMMANDATION': self.recommandation.format(self.inscription),
            'PRECISIONS': self.recommandation.precisions,
            'VILLE': self.inscription.ville_name,
            'BACKGROUND_COLOR': self.couleur,
            'SHORT_ID': self.short_id,
        }
        if self.inscription.telephone and len(self.inscription.telephone) == 12:
            to_return['SMS'] = self.inscription.telephone
        return to_return
