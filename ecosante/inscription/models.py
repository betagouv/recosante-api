from .. import db
from sqlalchemy.dialects import postgresql
from datetime import date
from dataclasses import dataclass
from typing import List
import csv
from io import StringIO

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
    diffusion = db.Column(db.String)
    telephone = db.Column(db.String)
    mail = db.Column(db.String)
    frequence = db.Column(db.String)
    #Habitudes
    deplacement = db.Column(postgresql.ARRAY(db.String))
    sport = db.Column(db.Boolean)
    apa = db.Column(db.Boolean)
    activites = db.Column(postgresql.ARRAY(db.String))
    enfants = db.Column(db.Boolean)
    #Sante
    pathologie_respiratoire = db.Column(db.Boolean)
    allergie_pollen = db.Column(db.Boolean)
    fumeur = db.Column(db.Boolean)

    date_inscription = db.Column(db.Date())

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.date_inscription = date.today()

    def has_habitudes(self):
        return any([getattr(self, k) is not None for k in ['deplacement', 'sport', 'apa', 'activites', 'enfants']])

    def has_sante(self):
        return any([getattr(self, k) is not None for k in ['pathologie_respiratoire', 'allergie_pollen', 'fumeur']])

    @classmethod
    def generate_csv(cls):
        def generate_line(line):
            stringio = StringIO()
            writer = csv.writer(stringio)
            writer.writerow(line)
            v = stringio.getvalue()
            stringio.close()
            return v

        yield generate_line(['Dans quelle ville vivez-vous ?',
            'Parmi les choix suivants, quel(s) moyen(s) de transport utilisez-vous principalement pour vos déplacements ?',
            "Pratiquez-vous une activité sportive au moins une fois par semaine ? On entend par activité sportive toute forme d'activité physique ayant pour objectif l'amélioration et le maintien de la condition physique.",
            "Pratiquez-vous une Activité Physique Adaptée au moins une fois par semaine ? Les APA regroupent l’ensemble des activités physiques et sportives adaptées aux capacités des personnes atteintes de maladie chronique ou de handicap.",
            "Pratiquez-vous au moins une fois par semaine les activités suivantes ?",
            "Vivez-vous avec une pathologie respiratoire ?",
            "Êtes-vous allergique aux pollens ?",
            "Êtes-vous fumeur.euse ?",
            "Vivez-vous avec des enfants ?",
            "Votre adresse e-mail : elle permettra à l'Equipe Ecosanté de communiquer avec vous si besoin.",
            "Souhaitez-vous recevoir les recommandations par : *",
            "Numéro de téléphone :",
            "A quelle fréquence souhaitez-vous recevoir les recommandations ? *",
            "Consentez-vous à partager vos données avec l'équipe Écosanté ? Ces données sont stockées sur nextcloud, dans le respect de la réglementation RGPD."
        ])

        for inscription in Inscription.query.all():
            diffusion = inscription.diffusion
            if diffusion == 'mail':
                diffusion = 'Mail'
            elif diffusion == 'sms':
                diffusion = 'SMS'

            yield generate_line([
                inscription.ville_entree,
                "; ".join(inscription.deplacement or []),
                cls.convert_boolean_to_oui_non(inscription.activites is not None and 'sport' in inscription.activites),
                "Non",
                ";".join(inscription.activites or []),
                cls.convert_boolean_to_oui_non(inscription.pathologie_respiratoire),
                cls.convert_boolean_to_oui_non(inscription.allergie_pollen),
                cls.convert_boolean_to_oui_non(inscription.fumeur),
                cls.convert_boolean_to_oui_non(inscription.enfants),
                inscription.mail,
                diffusion,
                inscription.telephone,
                inscription.frequence,
                "Oui"
            ])

    @classmethod
    def convert_boolean_to_oui_non(cls, value):
        return "Oui" if value else "Non"