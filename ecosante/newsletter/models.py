from dataclasses import dataclass, field
from typing import List
from datetime import datetime, date
from itertools import chain
from flask.helpers import url_for
from indice_pollution.history.models.commune import Commune
import requests
from sqlalchemy import text
from sqlalchemy.dialects import postgresql
from flask import current_app
from sqlalchemy.sql.functions import func
from ecosante.inscription.models import Inscription
from ecosante.recommandations.models import Recommandation
from ecosante.utils.funcs import (
    convert_boolean_to_oui_non,
    generate_line,
    oxford_comma
)
from ecosante.extensions import db
from indice_pollution import bulk, today, forecast as get_forecast, episodes as get_episodes, raep as get_raep

FR_DATE_FORMAT = '%d/%m/%Y'

@dataclass
class Newsletter:
    date: datetime = field(default_factory=today, init=True)
    recommandation: Recommandation = field(default=None, init=True)
    recommandations: List[Recommandation] = field(default=None, init=True)
    user_seed: str = field(default=None, init=True)
    inscription: Inscription = field(default=None, init=True)
    forecast: dict = field(default_factory=dict, init=True)
    episodes: List[dict] = field(default=None, init=True)
    raep: int = field(default=0, init=True)
    radon: int = field(default=0, init=True)
    allergenes: dict = field(default_factory=dict, init=True)
    validite_raep: dict = field(default_factory=dict, init=True)


    def __post_init__(self):
        if not 'label' in self.today_forecast:
            current_app.logger.error(f'No label for forecast for inscription: id: {self.inscription.id} insee: {self.inscription.ville_insee}')
        if not 'couleur' in self.today_forecast:
            current_app.logger.error(f'No couleur for forecast for inscription: id: {self.inscription.id} insee: {self.inscription.ville_insee}')
        if self.episodes and 'data' in self.episodes:
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
        else:
            self.polluants = []
        if not self.raep and not self.allergenes and not self.validite_raep:
            raep = get_raep(self.inscription.ville_insee).get('data')
            if raep:
                self.raep = raep['total']
                self.allergenes = raep['allergenes']
                self.validite_raep = raep['periode_validite']
        try:
            self.raep = int(self.raep)
        except ValueError as e:
            current_app.logger.error(f"Parsing error for raep of {self.inscription.mail}")
            current_app.logger.error(e)
        except TypeError as e:
            current_app.logger.error(f"Parsing error for raep of {self.inscription.mail}")
            current_app.logger.error(e)
        self.recommandations = self.recommandations or Recommandation.shuffled(user_seed=self.user_seed)
        if type(self.recommandations) == list:
            self.recommandations = {r.id: r for r in self.recommandations}
        self.recommandation = self.recommandation or self.get_recommandation(self.recommandations)
    

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
    def sous_indices(self):
        return self.today_forecast.get('sous_indices')

    @property
    def get_episodes_depassements(self):
        return [e for e in self.today_episodes if e['etat'] != 'PAS DE DEPASSEMENT']

    @property
    def has_depassement(self):
        return len(self.get_depassement) > 0


    @classmethod
    def export(cls, preferred_reco=None, user_seed=None, remove_reco=[], only_to=None, date_=None):
        query = Inscription.active_query()
        if only_to:
            query = query.filter(Inscription.mail.in_(only_to))
        query_nl = NewsletterDB.query\
            .filter(
                NewsletterDB.date==date.today(),
                NewsletterDB.label != None)\
            .with_entities(
                NewsletterDB.inscription_id
        )
        query = query\
            .filter(Inscription.id.notin_(query_nl))\
            .filter(Inscription.date_inscription < str(date.today()))
        recommandations = Recommandation.shuffled(user_seed=user_seed, preferred_reco=preferred_reco, remove_reco=remove_reco)
        inscriptions = query.distinct(Inscription.ville_insee)
        insee_region = {i.ville_insee: i.region_name for i in inscriptions}
        try:
            insee_forecast = bulk(insee_region, fetch_episodes=True, fetch_allergenes=True, date_=date_)
        except requests.exceptions.HTTPError as e:
            current_app.logger.error(e)
            raise e
        for inscription in query.all():
            if inscription.ville_insee not in insee_forecast:
                continue
            init_dict = {
                "inscription": inscription,
                "recommandations": recommandations,
                "forecast": insee_forecast[inscription.ville_insee].get("forecast"),
                "episodes": insee_forecast[inscription.ville_insee].get("episode"),
                "raep": insee_forecast[inscription.ville_insee].get("raep", {}).get("total"),
                "allergenes": insee_forecast[inscription.ville_insee].get("raep", {}).get("allergenes"),
                "validite_raep": insee_forecast[inscription.ville_insee].get("raep", {}).get("periode_validite", {}),
            }
            if date_:
                init_dict['date'] = date_
            newsletter = cls(**init_dict)
            yield newsletter

    def get_recommandation(self, recommandations: List[Recommandation]):
        if not recommandations:
            return None
        query_nl = db.session.query(
                NewsletterDB.recommandation_id,
                func.max(NewsletterDB.date).label("date")
            )\
            .filter(NewsletterDB.inscription_id==self.inscription.id)\
            .group_by(NewsletterDB.recommandation_id)
        subquery_nl = query_nl.subquery("nl")
        last_nl = query_nl.order_by(text("date DESC")).limit(1).first()

        sorted_recommandation_ids = db.session.query(
                text("""LEAST(
                    extract(
                        epoch from (
                            current_date - coalesce(nl.date, (current_date + interval '1 day'))
                        )
                    )/86400,
                    30) AS d
                    """),
                Recommandation.id)\
            .join(subquery_nl, isouter=True)\
            .filter(Recommandation.status == "published")\
            .order_by(text("d"), Recommandation.ordre)\
            .all()
        last_recommandation = recommandations.get(last_nl[0]) if last_nl else None
        last_criteres = last_recommandation.criteres if last_recommandation else set()
        last_type = last_recommandation.type_ if last_recommandation else ""

        eligible_recommandations = filter(
            lambda r: recommandations[r[1]].is_relevant(self.inscription, self.qualif, self.polluants, self.raep, self.date), 
            sorted(
                sorted_recommandation_ids,
                key=lambda r: (r[0], len(recommandations[r[1]].criteres.intersection(last_criteres)), recommandations[r[1]].type_ != last_type)
            )
        )
        return recommandations[next(eligible_recommandations)[1]]


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

    @property
    def show_raep(self):
        #On envoie pas en cas de polluants
        #ni en cas de risque faible à un personne non-allergique
        if type(self.raep) != int:
            return False
        if self.polluants:
            return False
        if self.raep == 0:
            return False
        elif self.raep < 4 and not self.inscription.allergie_pollens:
            return False
        return True


    @property
    def show_radon(self):
        if self.polluants:
            return False
        if type(self.raep) == int:
            if self.inscription.allergie_pollens and self.raep != 0:
                return False
            if not self.inscription.allergie_pollens and self.raep >= 4:
                return False
        if self.qualif not in ['bon', 'moyen']:
            return False
        last_radon = db.session.query(NewsletterDB.date)\
            .filter(NewsletterDB.inscription_id == self.inscription.id)\
            .filter(NewsletterDB.show_radon == True)\
            .order_by(NewsletterDB.id.desc())\
            .limit(1)\
            .first()

        if not last_radon:
            return True
        days_since_last_sent = (date.today() - last_radon[0]).days
        if self.radon == 3 and days_since_last_sent >= 15:
            return True
        if self.radon < 3 and days_since_last_sent >= 30:
            return True
        return False


@dataclass
class NewsletterDB(db.Model, Newsletter):
    __tablename__ = "newsletter"

    id: int = db.Column(db.Integer, primary_key=True)
    short_id: str = db.Column(
        db.String(),
        server_default=text("generate_random_id('public', 'newsletter', 'short_id', 8)")
    )
    inscription_id: int = db.Column(db.Integer, db.ForeignKey('inscription.id'), index=True)
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
    radon: int = db.Column(db.Integer())
    allergenes: dict = db.Column(postgresql.JSONB)
    raep_debut_validite = db.Column(db.String())
    raep_fin_validite = db.Column(db.String())
    show_raep = db.Column(db.Boolean())
    show_radon = db.Column(db.Boolean())
    sous_indices: dict = db.Column(postgresql.JSONB)

    def __init__(self, newsletter: Newsletter):
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
        self.raep = int(newsletter.raep) if newsletter.raep else None
        self.allergenes = newsletter.allergenes
        self.raep_debut_validite = newsletter.validite_raep.get('debut')
        self.raep_fin_validite = newsletter.validite_raep.get('fin')
        self.show_raep = newsletter.show_raep
        self.show_radon = newsletter.show_radon
        self.sous_indices = newsletter.sous_indices


    def attributes(self):
        noms_sous_indices = ['no2', 'so2', 'o3', 'pm10', 'pm25']
        def get_sous_indice(nom):
            if not self.sous_indices:
                return {}
            try:
                return next(filter(lambda s: s.get('polluant_name', '').lower() == nom.lower(), self.sous_indices))
            except StopIteration:
                return {}
        commune = Commune.get(self.inscription.ville_insee)
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
                "OBJECTIF": self.recommandation.objectif,
                "RAEP_DEBUT_VALIDITE": self.raep_debut_validite,
                "RAEP_FIN_VALIDITE": self.raep_fin_validite,
                "QUALITE_AIR_VALIDITE": self.date.strftime("%d/%m/%Y"),
                "POLLINARIUM_SENTINELLE": False if not commune or not commune.pollinarium_sentinelle else True
            },
            **{f'ALLERGENE_{a[0]}': int(a[1]) for a in (self.allergenes if type(self.allergenes) == dict else dict() ).items()},
            **dict(chain(*[[(f'SS_INDICE_{si.upper()}_LABEL', get_sous_indice(si).get('label') or ""), (f'SS_INDICE_{si.upper()}_COULEUR', get_sous_indice(si).get('couleur') or "")] for si in noms_sous_indices]))
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

    @property
    def something_to_show(self):
        return self.label or self.polluants_formatted or self.show_radon or self.show_raep