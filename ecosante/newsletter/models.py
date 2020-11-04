from dataclasses import dataclass
from datetime import datetime, timedelta
from flask import current_app
from ecosante.inscription.models import Inscription
from ecosante.recommandations.models import Recommandation
from ecosante.utils.funcs import (
    convert_boolean_to_oui_non,
    generate_line
)
from ecosante.extensions import db
from indice_pollution import bulk_forecast, today, forecast as get_forecast

@dataclass
class Newsletter(db.Model):
    qai: int
    forecast: dict
    date: datetime
    inscription: Inscription
    recommandation: Recommandation


    id = db.Column(db.Integer, primary_key=True)
    inscription_id = db.Column(db.Integer, db.ForeignKey('inscription.id'))
    inscription = db.relationship("Inscription", backref="inscription")
    recommandation_id = db.Column(db.Integer, db.ForeignKey('recommandation.id'))
    recommandation = db.relationship("Recommandation")
    date = db.Column(db.Date())

    QUALIFICATIF_TRES_BON = 'très bon'
    QUALIFICATIF_BON = 'bon'
    QUALIFICATIF_MOYEN = 'moyen'
    QUALIFICATIF_MÉDIOCRE = 'médiocre'
    QUALIFICATIF_MAUVAIS = 'mauvais'
    QUALIFICATIF_TRÈS_MAUVAIS = 'très mauvais'

    INDICE_ATMO_TO_QUALIFICATIF = {
        1: QUALIFICATIF_TRES_BON,
        2: QUALIFICATIF_TRES_BON,
        3: QUALIFICATIF_BON,
        4: QUALIFICATIF_BON,
        5: QUALIFICATIF_MOYEN,
        6: QUALIFICATIF_MÉDIOCRE,
        7: QUALIFICATIF_MÉDIOCRE,
        8: QUALIFICATIF_MAUVAIS,
        9: QUALIFICATIF_MAUVAIS,
        10: QUALIFICATIF_TRÈS_MAUVAIS,
    }

    QUALIF_TO_BACKGROUND = {
        QUALIFICATIF_TRES_BON: '#37C55F',
        QUALIFICATIF_BON: '#8FDA2C',
        QUALIFICATIF_MOYEN: '#F9E000',
        QUALIFICATIF_MÉDIOCRE: '#FFAA27',
        QUALIFICATIF_MAUVAIS: '#FF090D',
        QUALIFICATIF_TRÈS_MAUVAIS: '#800103'
    }

    def __init__(self, inscription, seed=None, preferred_reco=None, recommandations=None, forecast=None, recommandation_id=None):
        recommandations = recommandations or Recommandation.shuffled(random_uuid=seed, preferred_reco=preferred_reco)
        self.date = today()
        self.inscription = inscription
        self.inscription_id = inscription.id
        try:
            self.forecast = forecast or get_forecast(self.inscription.ville_insee, self.date, True)
        except KeyError as e:
            current_app.logger.error(f'Unable to find region for {inscription.ville_name} ({inscription.ville_insee})')
            current_app.logger.error(e)
            self.forecast = None
        try:
            self.qai = int(next(iter([v['indice'] for v in self.forecast['data'] if v['date'] == str(self.date)]), None))
        except (TypeError, ValueError) as e:
            current_app.logger.error(f'Unable to get qai for inscription: id: {inscription.id} insee: {inscription.ville_insee}')
            current_app.logger.error(e)
            self.qai = None

        self.recommandation =\
             Recommandation.query.get(recommandation_id) or\
             Recommandation.get_revelant(
                recommandations,
                inscription,
                self.qai
            )
        self.recommandation_id = self.recommandation.id

    @property
    def qualif(self):
        return self.INDICE_ATMO_TO_QUALIFICATIF.get(self.qai)
    
    @property
    def background(self):
        return self.QUALIF_TO_BACKGROUND.get(self.qualif)

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
    def export(cls, preferred_reco=None, seed=None, remove_reco=[]):
        recommandations = Recommandation.shuffled(random_uuid=seed, preferred_reco=preferred_reco, remove_reco=remove_reco)
        insee_region = {i.ville_insee: i.region_name for i in Inscription.query.distinct(Inscription.ville_insee)}
        insee_forecast = bulk_forecast(insee_region)
        for inscription in Inscription.query.all():
            newsletter = cls(inscription, recommandations=recommandations, forecast=insee_forecast[inscription.ville_insee])
            if inscription.frequence == "pollution" and newsletter.qai and newsletter.qai < 8:
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