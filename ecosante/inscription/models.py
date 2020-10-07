from .. import db
from ecosante.recommandations.models import Recommandation
from sqlalchemy.dialects import postgresql
from sqlalchemy import Enum
from datetime import date
from dataclasses import dataclass
from typing import List
import csv
import requests
import json
from io import StringIO
from indice_pollution import forecast, today
from flask import current_app

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
    telephone = db.Column(db.String)
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

    QUALIFICATIF_TRES_BON = 'Très bonne'
    QUALIFICATIF_BON = 'Bonne'
    QUALIFICATIF_MOYEN = 'Moyenne'
    QUALIFICATIF_MÉDIOCRE = 'Médiocre'
    QUALIFICATIF_MAUVAIS = 'Mauvaise'
    QUALIFICATIF_TRÈS_MAUVAIS = 'Très mauvaise'

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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.date_inscription = date.today()

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
        return json.loads(self._cache_api_commune)

    @property
    def ville_centre(self):
        return self.cache_api_commune.get('centre')

    @property
    def region_name(self):
        return self.cache_api_commune.get('region', {}).get('nom')

    @classmethod
    def generate_csv(cls, new_export=False, preferred_reco=None, random_uuid=None):
        def generate_line(line):
            stringio = StringIO()
            writer = csv.writer(stringio)
            writer.writerow(line)
            v = stringio.getvalue()
            stringio.close()
            return v

        recommandations = Recommandation.shuffled(random_uuid=random_uuid, preferred_reco=preferred_reco)

        yield generate_line([
            'VILLE' if new_export else 'Dans quelle ville vivez-vous ?',
            'Parmi les choix suivants, quel(s) moyen(s) de transport utilisez-vous principalement pour vos déplacements ?',
            "Pratiquez-vous une activité sportive au moins une fois par semaine ? On entend par activité sportive toute forme d'activité physique ayant pour objectif l'amélioration et le maintien de la condition physique.",
            "Pratiquez-vous une Activité Physique Adaptée au moins une fois par semaine ? Les APA regroupent l’ensemble des activités physiques et sportives adaptées aux capacités des personnes atteintes de maladie chronique ou de handicap.",
            "Pratiquez-vous au moins une fois par semaine les activités suivantes ?",
            "Vivez-vous avec une pathologie respiratoire ?",
            "Êtes-vous allergique aux pollens ?",
            "Êtes-vous fumeur.euse ?",
            "Vivez-vous avec des enfants ?",
            'MAIL' if new_export else "Votre adresse e-mail : elle permettra à l'Equipe Ecosanté de communiquer avec vous si besoin.",
            'FORMAT' if new_export else "Souhaitez-vous recevoir les recommandations par : *",
            'SMS' if new_export else "Numéro de téléphone :",
            "A quelle fréquence souhaitez-vous recevoir les recommandations ? *",
            "Consentez-vous à partager vos données avec l'équipe Écosanté ? Ces données sont stockées sur nextcloud, dans le respect de la réglementation RGPD.",
            "Date d'inscription"
        ] + ([
            "QUALITE_AIR",
            "Région",
            "LIEN_AASQA",
            "RECOMMANDATION",
            "PRECISIONS"
        ] if new_export else []))

        d = today()
        for inscription in Inscription.query.all():
            if new_export:
                try:
                    f = forecast(inscription.ville_insee, d, True)
                except KeyError as e:
                    current_app.logger.error(f'Unable to find region for {inscription.ville_name} ({inscription.ville_insee})')
                    current_app.logger.error(e)
                    f = {"data": [], "metadata": {"region": {"nom": "", "website": ""}}}
                try:
                    qai = int(next(iter([v['indice'] for v in f['data'] if v['date'] == str(d)]), None))
                except TypeError:
                    qai = None
                recommandation = Recommandation.get_revelant(recommandations, inscription, qai)
                if inscription.frequence == "pollution" and qai and qai < 8:
                    continue
            else:
                f, qai, recommandation = None, None, None


            yield generate_line([
                inscription.ville_name,
                "; ".join(inscription.deplacement or []),
                cls.convert_boolean_to_oui_non(inscription.sport),
                "Non",
                ";".join(inscription.activites or []),
                cls.convert_boolean_to_oui_non(inscription.pathologie_respiratoire),
                cls.convert_boolean_to_oui_non(inscription.allergie_pollen),
                cls.convert_boolean_to_oui_non(inscription.fumeur),
                cls.convert_boolean_to_oui_non(inscription.enfants),
                inscription.mail,
                inscription.diffusion,
                inscription.telephone,
                inscription.frequence,
                "Oui",
                inscription.date_inscription
            ] + ([
                cls.INDICE_ATMO_TO_QUALIFICATIF.get(qai),
                f['metadata']['region']['nom'],
                f['metadata']['region']['website'],
                recommandation.format(inscription),
                recommandation.precisions
            ] if new_export else []))

    @classmethod
    def convert_boolean_to_oui_non(cls, value):
        return "Oui" if value else "Non"

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