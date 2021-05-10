from dataclasses import dataclass
from typing import List
from datetime import datetime, date
from flask.helpers import url_for
from indice_pollution.history.models.commune import Commune
import requests
from sqlalchemy import text
from sqlalchemy.dialects import postgresql
from flask import current_app
from ecosante.inscription.models import Inscription
from ecosante.recommandations.models import Recommandation
from ecosante.utils.funcs import (
    convert_boolean_to_oui_non,
    generate_line,
    oxford_comma
)
from ecosante.extensions import db
from indice_pollution import bulk, today, forecast as get_forecast, episodes as get_episodes

@dataclass
class Newsletter:
    date: datetime = date.today()
    recommandation: Recommandation = None
    inscription: Inscription = None
    forecast: dict = None
    episodes: List[dict] = None
    raep: int = None
    allergenes: List[str] = None

    def __init__(self, inscription, seed=None, preferred_reco=None, recommandations=None, forecast=None, recommandation_id=None, episodes=None, raep=None, allergenes=None, date_=None):
        recommandations = recommandations or Recommandation.shuffled(user_seed=seed, preferred_reco=preferred_reco)
        self.date = date_ or today()
        self.inscription = inscription
        try:
            self.forecast = forecast or get_forecast(self.inscription.ville_insee, self.date, True)
        except KeyError as e:
            current_app.logger.error(f'Unable to find region for {self.inscription.ville_name} ({self.inscription.ville_insee})')
            current_app.logger.error(e)
            self.forecast = dict()
        try:
            self.episodes = episodes or get_episodes(self.inscription.ville_insee, self.date)
        except KeyError as e:
            current_app.logger.error(f'Unable to find region for {self.inscription.ville_name} ({self.inscription.ville_insee})')
            current_app.logger.error(e)
            self.episodes = [dict()]
        if not 'label' in self.today_forecast:
            current_app.logger.error(f'No label for forecast for inscription: id: {inscription.id} insee: {inscription.ville_insee}')
        if not 'couleur' in self.today_forecast:
            current_app.logger.error(f'No couleur for forecast for inscription: id: {inscription.id} insee: {inscription.ville_insee}')
        self.polluants = [
            {
                '1': 'dioxyde_soufre',
                '5': 'particules_fines',
                '7': 'ozone',
                '8': 'dioxyde_azote',
            }.get(str(e['code_pol']), f'erreur: {e["code_pol"]}')
            for e in self.episodes['data']
            if e['etat'] != 'PAS DE DEPASSEMENT'\
               and 'date' in e\
               and e['date'] == str(self.date)
        ]

        if raep:
            try:
                self.raep = int(raep)
            except ValueError as e:
                current_app.logger.error(f"Parsing error for raep of {inscription.mail}")
                current_app.logger.error(e)
                self.raep = 0
            except TypeError:
                current_app.logger.error(f"Parsing error for raep of {inscription.mail}")
                current_app.logger.error(e)
                self.raep = 0
        else:
            current_app.logger.error(f'No RAEP for {inscription.mail}')
            self.raep = 0

        if allergenes:
            self.allergenes = allergenes
        else:
            current_app.logger.error(f'No allergenes for {inscription.mail}')
            self.allergenes = dict()

        self.recommandation =\
            Recommandation.query.get(recommandation_id) or\
            self.get_recommandation(recommandations)

    @property
    def polluants_formatted(self):
        label_to_formatted_text ={
            'dioxyde_soufre': 'au dioxyde de soufre',
            'particules_fines': 'aux particules fines',
            'ozone': 'à l’ozone',
            'dioxyde_azote': 'au dioxyde d’azote'
        }
        return oxford_comma([label_to_formatted_text.get(pol) for pol in self.polluants])

    @property
    def polluants_symbols(self):
        label_to_symbols = {
            'ozone': "o3",
            'particules_fines': "pm10",
            'dioxyde_azote': "no2",
            "dioxyde_soufre": "so2"
        }
        return [label_to_symbols.get(label) for label in self.polluants]

    @property
    def today_forecast(self):
        try:
            data = self.forecast['data']
        except KeyError:
            current_app.logger.error(f'No data for forecast of inscription "{self.inscription.id}" INSEE: "{self.inscription.ville_insee}"')
            return dict()
        try:
            return next(iter([v for v in data if v['date'] == str(self.date)]), dict())
        except (TypeError, ValueError, StopIteration) as e:
            current_app.logger.error(f'Unable to get forecast for inscription: id: {self.inscription.id} insee: {self.inscription.ville_insee}')
            current_app.logger.error(e)
            return dict()

    @property
    def today_episodes(self):
        data = self.episodes['data']
        try:
            return [v for v in data if v['date'] == str(self.date)]
        except (TypeError, ValueError, StopIteration) as e:
            current_app.logger.error(f'Unable to get episodes for inscription: id: {self.inscription.id} insee: {self.inscription.ville_insee}')
            current_app.logger.error(e)
            return [dict()]

    @property
    def qualif(self):
        return self.today_forecast.get('indice')

    @property
    def label(self):
        return self.today_forecast.get('label')
    
    @property
    def couleur(self):
        return self.today_forecast.get('couleur')

    @property
    def get_episodes_depassements(self):
        return [e for e in self.today_episodes if e['etat'] != 'PAS DE DEPASSEMENT']

    @property
    def has_depassement(self):
        return len(self.get_depassement) > 0


    @classmethod
    def export(cls, preferred_reco=None, user_seed=None, remove_reco=[], only_to=None):
        query = Inscription.active_query()
        if only_to:
            query = query.filter(Inscription.mail.in_(only_to))
        recommandations = Recommandation.shuffled(user_seed=user_seed, preferred_reco=preferred_reco, remove_reco=remove_reco)
        inscriptions = query.distinct(Inscription.ville_insee)
        insee_region = {i.ville_insee: i.region_name for i in inscriptions}
        try:
            insee_forecast = bulk(insee_region, fetch_episodes=True, fetch_allergenes=True)
        except requests.exceptions.HTTPError as e:
            current_app.logger.error(e)
            raise e
        for inscription in query.all():
            if inscription.ville_insee not in insee_forecast:
                continue
            newsletter = cls(
                inscription,
                recommandations=recommandations,
                forecast=insee_forecast[inscription.ville_insee].get("forecast"),
                episodes=insee_forecast[inscription.ville_insee].get("episode"),
                raep=insee_forecast[inscription.ville_insee].get("raep", {}).get("total"),
                allergenes=insee_forecast[inscription.ville_insee].get("raep", {}).get("allergenes")
            )
            if inscription.frequence == "pollution" and newsletter.qualif and newsletter.qualif not in ['mauvais', 'tres_mauvais', 'extrement_mauvais']:
                continue
            yield newsletter

    def get_recommandation(self, recommandations: List[Recommandation]):
        query_nl = NewsletterDB.query\
            .join(Inscription)\
            .filter(Inscription.mail==self.inscription.mail)
        sorted_recommandation_ids = db.session.query(Recommandation.id)\
            .join(query_nl.subquery("nl"), isouter=True)\
            .group_by(Recommandation.id)\
            .order_by(text("max(nl.date) nulls first"), Recommandation.ordre)\
            .all()
        last_nl = query_nl.order_by(text("date DESC")).first()
        eligible_recommandations = filter(
            lambda r: r.is_relevant(self.inscription, self.qualif, self.polluants, self.raep, self.date), 
            sorted(
                recommandations,
                key=lambda r: sorted_recommandation_ids.index((r.id,))
            )
        )
        if not last_nl:
            return next(eligible_recommandations)
        else:
            to_send = None
            last_criteres = last_nl.recommandation.criteres
            last_type = last_nl.recommandation.type_
            for reco in eligible_recommandations:
                if reco.criteres != last_criteres and reco.type_ != last_type:
                    return reco
                to_send = to_send or reco # On veut envoyer la plus haute dans la liste
            return to_send


    def csv_line(self):
        return generate_line([
            self.inscription.ville_name,
            "; ".join(self.inscription.deplacement or []),
            convert_boolean_to_oui_non(self.inscription.sport),
            "Non",
            ";".join(self.inscription.activites or []),
            convert_boolean_to_oui_non(self.inscription.pathologie_respiratoire),
            convert_boolean_to_oui_non(self.inscription.allergie_pollens),
            self.inscription.enfants,
            self.inscription.mail,
            self.inscription.diffusion,
            self.inscription.frequence,
            "Oui",
            self.inscription.date_inscription,
            self.qualif,
            self.couleur,
            self.forecast['metadata']['region']['nom'],
            self.forecast['metadata']['region']['website'],
            self.recommandation.format(self.inscription),
            self.recommandation.precisions,
            self.recommandation.id
        ])

    @property
    def lien_recommandations_alerte(self):
        if not self.polluants:
            return
        population = "vulnerable" if self.inscription.personne_sensible else "generale"
        return url_for(
            "pages.recommandation_episode_pollution",
            population=population,
            polluants=self.polluants_symbols,
            _external=True)

    @property
    def show_raep(self):
        #On envoie pas en cas de polluants
        #ni en cas de risque faible à un personne non-allergique
        if self.polluants:
            return False
        if self.raep == 0:
            return False
        elif self.raep < 4 and not self.inscription.allergie_pollens:
            return False
        return True

    @property
    def couleur_raep(self):
        return {
            0: "#31bcf0",
            1: "#21a84c",
            2: "#fdd401",
            3: "#f69321",
            4: "#ee6344",
            5: "#d94049"
        }.get(self.raep)

    @property
    def qualif_raep(self):
        return {
            0: "nul",
            1: "très faible",
            2: "faible",
            3: "moyen",
            4: "élevé",
            5: "très élevé"
        }.get(self.raep)

    @property
    def departement_preposition(self):
        commune = Commune.get(self.inscription.ville_insee)
        if commune and commune.departement and commune.departement.preposition:
            preposition = commune.departement.preposition
            if preposition[-1].isalpha():
                return preposition + " "
            return preposition
        return ""

@dataclass
class NewsletterDB(db.Model, Newsletter):
    __tablename__ = "newsletter"

    id: int = db.Column(db.Integer, primary_key=True)
    short_id: str = db.Column(
        db.String(),
        server_default=text("generate_random_id('public', 'newsletter', 'short_id', 8)")
    )
    inscription_id: int = db.Column(db.Integer, db.ForeignKey('inscription.id'))
    inscription: Inscription = db.relationship(Inscription)
    lien_aasqa: str = db.Column(db.String())
    nom_aasqa: str = db.Column(db.String())
    recommandation_id: int = db.Column(db.Integer, db.ForeignKey('recommandation.id'))
    recommandation: Recommandation = db.relationship("Recommandation")
    date: date = db.Column(db.Date())
    qualif: str = db.Column(db.String())
    label: str = db.Column(db.String())
    couleur: str = db.Column(db.String())
    appliquee: bool = db.Column(db.Boolean())
    avis: str = db.Column(db.String())
    polluants: List[str] = db.Column(postgresql.ARRAY(db.String()))
    raep: int = db.Column(db.Integer())
    allergenes: dict = db.Column(postgresql.JSONB)

    def __init__(self, newsletter):
        self.inscription = newsletter.inscription
        self.inscription_id = newsletter.inscription.id
        self.lien_aasqa = newsletter.forecast.get('metadata', {}).get('region', {}).get('website') or ""
        self.nom_aasqa = newsletter.forecast.get('metadata', {}).get('region', {}).get('nom_aasqa') or ""
        self.recommandation = newsletter.recommandation
        self.recommandation_id = newsletter.recommandation.id
        self.date = newsletter.date
        self.qualif = newsletter.qualif
        self.label = newsletter.label
        self.couleur = newsletter.couleur
        self.polluants = newsletter.polluants
        self.raep = int(newsletter.raep)
        self.allergenes = newsletter.allergenes

    def attributes(self):
        return {
            **{
                'RECOMMANDATION': self.recommandation.format(self.inscription) or "",
                'LIEN_AASQA': self.lien_aasqa,
                'NOM_AASQA': self.nom_aasqa,
                'PRECISIONS': self.recommandation.precisions or "",
                'QUALITE_AIR': self.label or "",
                'VILLE': self.inscription.ville_nom or "",
                'BACKGROUND_COLOR': self.couleur or "",
                'SHORT_ID': self.short_id or "",
                'POLLUANT': self.polluants_formatted or "",
                'LIEN_RECOMMANDATIONS_ALERTE': self.lien_recommandations_alerte or "",
                'SHOW_RAEP': self.show_raep or False,
                'RAEP': self.qualif_raep or "",
                'BACKGROUND_COLOR_RAEP': self.couleur_raep or "",
                'USER_UID': self.inscription.uid,
                'DEPARTEMENT': self.inscription.departement.get('nom') or "",
                'DEPARTEMENT_PREPOSITION': self.departement_preposition or "",
                "LIEN_QA_POLLEN": self.recommandation.lien_qa_pollen or False,
                "OBJECTIF": self.recommandation.objectif
            },
            **{f'ALLERGENE_{a[0]}': int(a[1]) for a in (self.allergenes if type(self.allergenes) == dict else dict() ).items()}
        }

    @classmethod
    def generate_csv_avis(cls):
        yield generate_line([
            'Moyens de transport',
            "Activité sportive",
            "Activité physique adaptée",
            "Activités",
            "Pathologie respiratoire",
            "Allergie aux pollens",
            "Enfants",
            'MAIL',
            'FORMAT',
            "Fréquence",
            "Date d'inscription",
            "QUALITE_AIR",
            "RECOMMANDATION",
            "PRECISIONS",
            "ID RECOMMANDATION",
            "polluants"
            "avis"
        ])
        newsletters = cls.query\
            .filter(cls.avis.isnot(None))\
            .order_by(cls.date.desc())\
            .all()
        for newsletter in newsletters:
            yield newsletter.csv_line()