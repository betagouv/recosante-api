from calendar import different_locale
from dataclasses import dataclass, field
from typing import List
from datetime import datetime, date, timedelta
from itertools import chain
from flask.helpers import url_for
from indice_pollution.history.models.commune import Commune
import requests
from sqlalchemy import text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import subqueryload
from sqlalchemy.sql import or_
from flask import current_app
from sqlalchemy.sql.functions import func
from ecosante.inscription.models import Inscription, WebpushSubscriptionInfo
from ecosante.recommandations.models import Recommandation
from ecosante.utils.funcs import (
    convert_boolean_to_oui_non,
    generate_line,
    oxford_comma
)
from ecosante.extensions import db
from indice_pollution import bulk, today, forecast as get_forecast, episodes as get_episodes, raep as get_raep
from indice_pollution.history.models import Departement

FR_DATE_FORMAT = '%d/%m/%Y'

@dataclass
class Newsletter:
    webpush_subscription_info_id: int = None
    webpush_subscription_info: dict = None
    date: datetime = field(default_factory=today, init=True)
    recommandation: Recommandation = field(default=None, init=True)
    recommandation_qa: Recommandation = field(default=None, init=True)
    recommandation_raep: Recommandation = field(default=None, init=True)
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
            current_app.logger.error(f'No label for forecast for inscription: id: {self.inscription.id} insee: {self.inscription.commune.insee}')
        if not 'couleur' in self.today_forecast:
            current_app.logger.error(f'No couleur for forecast for inscription: id: {self.inscription.id} insee: {self.inscription.commune.insee}')
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
        if self.raep is None and self.allergenes is None and not self.validite_raep:
            raep = get_raep(self.inscription.commune.insee).get('data')
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
        self.recommandation_qa = self.recommandation or self.get_recommandation(self.recommandations, types=["generale", "episode_pollution"])
        self.recommandation_raep = self.recommandation or self.get_recommandation(self.recommandations, types=["pollens"])
    

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
            current_app.logger.error(f'No data for forecast of inscription "{self.inscription.id}" INSEE: "{self.inscription.commune.insee}"')
            return dict()
        try:
            return next(iter([v for v in data if v['date'] == str(self.date)]), dict())
        except (TypeError, ValueError, StopIteration) as e:
            current_app.logger.error(f'Unable to get forecast for inscription: id: {self.inscription.id} insee: {self.inscription.commune.insee}')
            current_app.logger.error(e)
            return dict()

    @property
    def today_episodes(self):
        data = self.episodes['data']
        try:
            return [v for v in data if v['date'] == str(self.date)]
        except (TypeError, ValueError, StopIteration) as e:
            current_app.logger.error(f'Unable to get episodes for inscription: id: {self.inscription.id} insee: {self.inscription.commune.insee}')
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
    def export(cls, preferred_reco=None, user_seed=None, remove_reco=[], only_to=None, date_=None, media='mail', filter_already_sent=False):
        query = Inscription.active_query()
        if only_to:
            query = query.filter(Inscription.mail.in_(only_to))
        if filter_already_sent:
            query_nl = NewsletterDB.query\
                .filter(
                    NewsletterDB.date==date.today(),
                    NewsletterDB.label != None,
                    NewsletterDB.label != "",
                    NewsletterDB.inscription.has(Inscription.indicateurs_media.contains([media])))\
                .with_entities(
                    NewsletterDB.inscription_id
            )
            query = query.filter(Inscription.id.notin_(query_nl))
        query = query\
            .filter(or_(Inscription.indicateurs_frequence == None, ~Inscription.indicateurs_frequence.contains(["hebdomadaire"])))\
            .filter(Inscription.commune_id != None)\
            .filter(Inscription.date_inscription < str(date.today()))\
            .filter(Inscription.indicateurs_media.contains([media]))\
            .options(subqueryload(
                Inscription.commune,
                Commune.departement,
                Departement.region,
            ))
        recommandations = Recommandation.shuffled(user_seed=user_seed, preferred_reco=preferred_reco, remove_reco=remove_reco)
        inscriptions = query.distinct(Inscription.commune_id)
        insee_region = {i.commune.insee: i.commune.departement.region.nom for i in inscriptions if i.commune.departement and i.commune.departement.region}
        try:
            insee_forecast = bulk(insee_region, fetch_episodes=True, fetch_allergenes=True, date_=date_)
        except requests.exceptions.HTTPError as e:
            current_app.logger.error(e)
            raise e
        for inscription in query.all():
            forecast_ville = insee_forecast.get(inscription.commune.insee)
            if not forecast_ville:
                continue
            init_dict = {
                "inscription": inscription,
                "recommandations": recommandations,
                "forecast": forecast_ville.get("forecast"),
                "episodes": forecast_ville.get("episode"),
                "raep": forecast_ville.get("raep", {}).get("total"),
                "allergenes": forecast_ville.get("raep", {}).get("allergenes"),
                "validite_raep": forecast_ville.get("raep", {}).get("periode_validite", {}),
            }
            if date_:
                init_dict['date'] = date_
            if media == 'notifications_web' and 'notifications_web' in inscription.indicateurs_media:
                for wp in WebpushSubscriptionInfo.query.filter_by(inscription_id=inscription.id):
                    init_dict['webpush_subscription_info_id'] = wp.id
                    init_dict['webpush_subscription_info'] = wp
                    newsletter = cls(**init_dict)
                    if inscription.indicateurs_frequence and "alerte" in inscription.indicateurs_frequence:
                        if Recommandation.qualif_categorie(newsletter.qualif) != "mauvais" and newsletter.raep < 4:
                            continue
                    yield newsletter
            else:
                newsletter = cls(**init_dict)
                if inscription.indicateurs_frequence and "alerte" in inscription.indicateurs_frequence:
                    if Recommandation.qualif_categorie(newsletter.qualif) != "mauvais" and newsletter.raep < 4:
                        continue
                yield newsletter

    @property
    def past_nl_query(self):
        return db.session.query(
                NewsletterDB.recommandation_id,
                func.max(NewsletterDB.date).label("date")
            )\
            .filter(NewsletterDB.inscription_id==self.inscription.id)\
            .group_by(NewsletterDB.recommandation_id)

    @property
    def sorted_recommandations_query(self):
        subquery_nl = self.past_nl_query.subquery("nl")
        return db.session.query(func.greatest(subquery_nl.c.date, (date.today() - timedelta(days=30))), Recommandation.id)\
            .join(subquery_nl, isouter=True)\
            .filter(Recommandation.status == "published")\
            .order_by(text("nl.date nulls first"), Recommandation.ordre)

    def eligible_recommandations(self, recommandations: List[Recommandation], types=["generale", "episode_pollution", "pollens"]):
        if not recommandations:
            return
            yield # See https://stackoverflow.com/questions/13243766/python-empty-generator-function
        last_nl = self.past_nl_query.order_by(text("date DESC")).limit(1).first()
        sorted_recommandation_ids = self.sorted_recommandations_query.all()

        last_recommandation = recommandations.get(last_nl[0]) if last_nl else None
        last_criteres = last_recommandation.criteres if last_recommandation else set()
        last_type = last_recommandation.type_ if last_recommandation else ""

        sorted_recommandations_ids_by_criteria = sorted(
                sorted_recommandation_ids,
                key=lambda r: (r[0], len(recommandations[r[1]].criteres.intersection(last_criteres)), recommandations[r[1]].type_ != last_type)
            )
        for r in sorted_recommandations_ids_by_criteria:
            if recommandations[r[1]].is_relevant(
                inscription=self.inscription,
                qualif=self.qualif,
                polluants=self.polluants,
                raep=self.raep,
                date_=self.date,
                media='newsletter',
                types=types
            ):
                yield recommandations[r[1]]


    def get_recommandation(self, recommandations: List[Recommandation], types=["generale", "episode_pollution", "pollens"]):
        try:
            return next(self.eligible_recommandations(recommandations, types))
        except StopIteration:
            return None


    def csv_line(self):
        return generate_line([
            self.inscription.commune.nom,
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

    @staticmethod
    def raep_value_to_couleur(value):
        return {
            0: "#31bcf0",
            1: "#21a84c",
            2: "#fdd401",
            3: "#f69321",
            4: "#ee6344",
            5: "#d94049"
        }.get(value)

    @property
    def couleur_raep(self):
        return self.raep_value_to_couleur(self.raep)

    @staticmethod
    def raep_value_to_qualif(value):
        return {
            0: "risque nul",
            1: "très faible",
            2: "faible",
            3: "moyen",
            4: "élevé",
            5: "très élevé"
        }.get(value)

    @property
    def qualif_raep(self):
        return self.raep_value_to_qualif(self.raep)

    @property
    def departement_preposition(self):
        commune = self.inscription.commune
        if commune and commune.departement and commune.departement.preposition:
            preposition = commune.departement.preposition
            if preposition[-1].isalpha():
                return preposition + " "
            return preposition
        return ""

    @property
    def show_raep(self):
        if not self.inscription.has_indicateur("raep"):
            return False
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
    def show_qa(self):
        return self.inscription.has_indicateur("indice_atmo")

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
    recommandation: Recommandation = db.relationship("Recommandation", foreign_keys=[recommandation_id])
    recommandation_qa_id: int = db.Column(db.Integer, db.ForeignKey('recommandation.id'))
    recommandation_qa: Recommandation = db.relationship("Recommandation", foreign_keys=[recommandation_qa_id])
    recommandation_raep_id: int = db.Column(db.Integer, db.ForeignKey('recommandation.id'))
    recommandation_raep: Recommandation = db.relationship("Recommandation", foreign_keys=[recommandation_raep_id])
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
    webpush_subscription_info_id: int = db.Column(db.Integer, db.ForeignKey('webpush_subscription_info.id'), index=True)
    webpush_subscription_info: WebpushSubscriptionInfo = db.relationship(WebpushSubscriptionInfo)
    mail_list_id: int = db.Column(db.Integer)

    def __init__(self, newsletter: Newsletter):
        self.inscription = newsletter.inscription
        self.inscription_id = newsletter.inscription.id
        self.lien_aasqa = newsletter.forecast.get('metadata', {}).get('region', {}).get('website') or ""
        self.nom_aasqa = newsletter.forecast.get('metadata', {}).get('region', {}).get('nom_aasqa') or ""
        self.recommandation = newsletter.recommandation
        self.recommandation_id = newsletter.recommandation.id
        self.recommandation_qa = newsletter.recommandation_qa
        self.recommandation_qa_id = newsletter.recommandation_qa.id
        self.recommandation_raep = newsletter.recommandation_raep
        self.recommandation_raep_id = newsletter.recommandation_raep.id
        self.date = newsletter.date
        self.qualif = newsletter.qualif
        self.label = newsletter.label
        self.couleur = newsletter.couleur
        self.polluants = newsletter.polluants
        self.raep = int(newsletter.raep) if newsletter.raep is not None else None
        self.allergenes = newsletter.allergenes
        self.raep_debut_validite = newsletter.validite_raep.get('debut')
        self.raep_fin_validite = newsletter.validite_raep.get('fin')
        self.show_raep = newsletter.show_raep
        self.show_radon = newsletter.show_radon
        self.sous_indices = newsletter.sous_indices
        self.webpush_subscription_info_id = newsletter.webpush_subscription_info_id
        self.webpush_subscription_info = newsletter.webpush_subscription_info

    def attributes(self):
        noms_sous_indices = ['no2', 'so2', 'o3', 'pm10', 'pm25']
        def get_sous_indice(nom):
            if not self.sous_indices:
                return {}
            try:
                return next(filter(lambda s: s.get('polluant_name', '').lower() == nom.lower(), self.sous_indices))
            except StopIteration:
                return {}
        def convert_bool_to_yes_no(b):
            return "Yes" if b else "No"
        return {
            **{
                'EMAIL': self.inscription.mail,
                'RECOMMANDATION': self.recommandation.format(self.inscription) or "",
                'LIEN_AASQA': self.lien_aasqa,
                'NOM_AASQA': self.nom_aasqa,
                'PRECISIONS': self.recommandation.precisions or "",
                'QUALITE_AIR': self.label or "",
                'VILLE': self.inscription.commune.nom or "",
                'BACKGROUND_COLOR': self.couleur or "",
                'SHORT_ID': self.short_id or "",
                'POLLUANT': self.polluants_formatted or "",
                'LIEN_RECOMMANDATIONS_ALERTE': self.lien_recommandations_alerte or "",
                'SHOW_RAEP': convert_bool_to_yes_no((self.show_raep or False)),
                'RAEP': self.qualif_raep or "",
                'BACKGROUND_COLOR_RAEP': self.couleur_raep or "",
                'USER_UID': self.inscription.uid,
                'DEPARTEMENT': self.inscription.commune.departement.nom or "",
                'DEPARTEMENT_PREPOSITION': self.departement_preposition or "",
                "OBJECTIF": self.recommandation.objectif,
                "RAEP_DEBUT_VALIDITE": self.raep_debut_validite,
                "RAEP_FIN_VALIDITE": self.raep_fin_validite,
                'QUALITE_AIR_VALIDITE': self.date.strftime('%d/%m/%Y'),
                'POLLINARIUM_SENTINELLE': convert_bool_to_yes_no((False if not self.inscription.commune or not self.inscription.commune.pollinarium_sentinelle else True)),
                'SHOW_QA': convert_bool_to_yes_no(self.show_qa),
                'SHOW_RAEP': convert_bool_to_yes_no(self.show_raep),
                'SHOW_RADON': convert_bool_to_yes_no(self.show_radon),
                'INDICATEURS_FREQUENCE': self.inscription.indicateurs_frequence[0] if self.inscription.indicateurs_frequence else "",
                'RECOMMANDATION_QA': self.recommandation_qa.format(self.inscription) or "",
                'RECOMMANDATION_RAEP': self.recommandation_raep.format(self.inscription) or "",
                'NEW_USER': convert_bool_to_yes_no(str(self.inscription.date_inscription) < '2021-10-14')
            },
            **{f'ALLERGENE_{a[0]}': int(a[1]) for a in (self.allergenes if type(self.allergenes) == dict else dict() ).items()},
            **dict(chain(*[[(f'SS_INDICE_{si.upper()}_LABEL', get_sous_indice(si).get('label') or ""), (f'SS_INDICE_{si.upper()}_COULEUR', get_sous_indice(si).get('couleur') or "")] for si in noms_sous_indices]))
        }

    @property
    def webpush_data(self):
        commune = self.inscription.commune
        with different_locale('fr_FR.utf8'):
            title = f'{commune.nom.capitalize()}, le {date.today().strftime("%A %d %B")}'
        array_body = []
        if "indice_atmo" in self.inscription.indicateurs:
            array_body.append(f"Indice de la qualité de l’air : {self.label.capitalize()}.")
        if "raep" in self.inscription.indicateurs:
            array_body.append(f"Risque d’allergie aux pollens : {self.qualif_raep.capitalize()}.")
        return {
            "title": title,
            "body": "\n".join(array_body),
            "link": f"https://recosante.beta.gouv.fr/place/{commune.insee}/{commune.nom.lower()}/"
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