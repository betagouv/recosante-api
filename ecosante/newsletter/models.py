from calendar import different_locale
from dataclasses import dataclass, field
from typing import Dict, List
from datetime import datetime, date, timedelta
from itertools import chain, groupby
from math import inf
from flask.helpers import url_for
from sqlalchemy import ForeignKeyConstraint, text
from sqlalchemy.dialects import postgresql
from flask import current_app
from sqlalchemy.sql.functions import func
from sqlalchemy.sql.expression import cast
from psycopg2.extras import DateRange
from sqlalchemy.dialects.postgresql import DATERANGE
from ecosante.inscription.models import Inscription, WebpushSubscriptionInfo
from ecosante.recommandations.models import Recommandation
from ecosante.utils.funcs import (
    convert_boolean_to_oui_non,
    generate_line,
    oxford_comma
)
from ecosante.extensions import db, authenticator
from indice_pollution import bulk, today, forecast as get_forecast, episodes as get_episodes, raep as get_raep, get_all
from indice_pollution.history.models import VigilanceMeteo
from indice_pollution.history.models import IndiceUv

FR_DATE_FORMAT = '%d/%m/%Y'


@dataclass
class NewsletterHebdoTemplate(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    sib_id: int = db.Column(db.Integer, nullable=False)
    ordre: int = db.Column(db.Integer, nullable=False)

    deplacement: List[str] = db.Column(postgresql.ARRAY(db.String))
    activites: List[str] = db.Column(postgresql.ARRAY(db.String))
    _enfants: List[str] = db.Column("enfants", postgresql.ARRAY(db.String))
    chauffage: List[str] = db.Column(postgresql.ARRAY(db.String))
    _animaux_domestiques: List[str] = db.Column("animaux_domestiques", postgresql.ARRAY(db.String))

    _periode_validite: DateRange = db.Column(
        "periode_validite",
        DATERANGE(),
        nullable=False,
        default=lambda: DateRange('2022-01-01', '2023-01-01')
    )

    @classmethod
    def get_templates(cls):
        return cls.query.order_by(cls.ordre).all()

    def filtre_date(self, date_):
        periode_validite = self.periode_validite
        if periode_validite.lower.year != periode_validite.upper.year:
            return date(date_.year, 1, 1) <= date_ <= periode_validite.upper.replace(year=date_.year)\
                 or  periode_validite.lower.replace(year=date_.year) <= date_ <= date(date_.year, 12, 31)
        return date_ in self.periode_validite

    def filtre_criteres(self, inscription):
        for nom_critere in ['chauffage', 'activites', 'deplacement']:
            critere = getattr(self, nom_critere)
            if isinstance(critere, list) and len(critere) > 0:
                inscription_critere = getattr(inscription, nom_critere)
                if not isinstance(inscription_critere, list):
                    return False
                if len(set(critere).intersection(inscription_critere)) == 0:
                    return False
        if isinstance(self.enfants, bool) and self.enfants != inscription.has_enfants:
            return False
        if isinstance(self.animaux_domestiques, bool) and self.animaux_domestiques != inscription.has_animaux_domestiques:
            return False
        return True

    @classmethod
    def next_template(cls, inscription: Inscription, templates=None):
        templates = templates or cls.get_templates()
        already_sent_templates_ids = [nl.newsletter_hebdo_template_id for nl in inscription.last_newsletters_hebdo]
        valid_templates = sorted(
            [
                t
                for t in templates
                if t.filtre_date(date.today())\
                    and t.filtre_criteres(inscription)\
                    and t.id not in already_sent_templates_ids
            ],
            key=lambda t: t.ordre
        )
        if len(valid_templates) == 0:
            return None

        return [t for t in valid_templates][0]

    @property
    def periode_validite(self) -> DateRange:
        current_year = datetime.today().year
        if self._periode_validite.lower.replace(year=current_year) <= self._periode_validite.upper.replace(year=current_year):
            year_lower = current_year
        else:
            year_lower = current_year - 1
        # Si les dates sont sur deux années différentes ont veut conserver le saut d’année
        year_upper = year_lower + (self._periode_validite.upper.year - self._periode_validite.lower.year)
        return DateRange(self._periode_validite.lower.replace(year=year_lower), self._periode_validite.upper.replace(year=year_upper))

    @property
    def debut_periode_validite(self):
        return self.periode_validite.lower
    @debut_periode_validite.setter
    def debut_periode_validite(self, value):
        self._periode_validite = DateRange(
            value,
            self._periode_validite.upper if self._periode_validite else None)

    @property
    def fin_periode_validite(self):
        return self.periode_validite.upper
    @fin_periode_validite.setter
    def fin_periode_validite(self, value):
        self._periode_validite = DateRange(
            self._periode_validite.lower if self._periode_validite else None,
            value
        )

    @property
    def animaux_domestiques(self):
        if isinstance(self._animaux_domestiques, list):
            return self._animaux_domestiques[0] == 'true' if self._animaux_domestiques else False
        return None
    @animaux_domestiques.setter
    def animaux_domestiques(self, value):
        if isinstance(value, bool):
            self._animaux_domestiques = ["true" if value else "false"]
        else:
            self._animaux_domestiques = None

    @property
    def enfants(self):
        if isinstance(self._enfants, list):
            return self._enfants[0] == 'true' if self._enfants else False
        return None
    @enfants.setter
    def enfants(self, value):
        if isinstance(value, bool):
            self._enfants = ["true" if value else "false"]
        else:
            self._enfants = None

@dataclass
class Newsletter:
    webpush_subscription_info_id: int = None
    webpush_subscription_info: dict = None
    date: datetime = field(default_factory=today, init=True)
    recommandation: Recommandation = field(default=None, init=True)
    recommandation_qa: Recommandation = field(default=None, init=True)
    recommandation_raep: Recommandation = field(default=None, init=True)
    recommandation_episode: Recommandation = field(default=None, init=True)
    recommandation_indice_uv: Recommandation = field(default=None, init=True)
    recommandations: List[Recommandation] = field(default=None, init=True)
    user_seed: str = field(default=None, init=True)
    inscription: Inscription = field(default=None, init=True)
    forecast: dict = field(default_factory=dict, init=True)
    episodes: List[dict] = field(default=None, init=True)
    polluants: List[str] = field(default=None, init=True)
    raep: int = field(default=0, init=True)
    radon: int = field(default=0, init=True)
    allergenes: dict = field(default_factory=dict, init=True)
    validite_raep: dict = field(default_factory=dict, init=True)
    indice_uv: IndiceUv = field(default=None, init=True)
    newsletter_hebdo_template: NewsletterHebdoTemplate = field(default=None, init=True)
    type_: str = field(default="quotidien", init=True)

    vigilances: List[VigilanceMeteo]= field(default=None, init=True)
    vigilance_vent: VigilanceMeteo = field(default=None, init=True)
    vigilance_vent_recommandation: Recommandation = field(default=None, init=True)
    vigilance_pluie: VigilanceMeteo = field(default=None, init=True)
    vigilance_pluie_recommandation: Recommandation = field(default=None, init=True)
    vigilance_orages: VigilanceMeteo = field(default=None, init=True)
    vigilance_orages_recommandation: Recommandation = field(default=None, init=True)
    vigilance_crues: VigilanceMeteo = field(default=None, init=True)
    vigilance_crues_recommandation: Recommandation = field(default=None, init=True)
    vigilance_neige: VigilanceMeteo = field(default=None, init=True)
    vigilance_neige_recommandation: Recommandation = field(default=None, init=True)
    vigilance_canicule: VigilanceMeteo = field(default=None, init=True)
    vigilance_canicule_recommandation: Recommandation = field(default=None, init=True)
    vigilance_froid: VigilanceMeteo = field(default=None, init=True)
    vigilance_froid_recommandation: Recommandation = field(default=None, init=True)
    vigilance_avalanches: VigilanceMeteo = field(default=None, init=True)
    vigilance_avalanches_recommandation: Recommandation = field(default=None, init=True)
    vigilance_vagues: VigilanceMeteo = field(default=None, init=True)
    vigilance_vagues_recommandation: Recommandation = field(default=None, init=True)
    vigilance_globale: VigilanceMeteo = field(default=None, init=True)
    vigilance_globale_recommandation: Recommandation = field(default=None, init=True)
    
    phenomenes_sib = {1: 'vent', 2: 'pluie', 3: 'orages', 4: 'crues', 5: 'neige', 6: 'canicule', 7: 'froid', 8: 'avalanches', 9: 'vagues'}

    def __post_init__(self):
        if self.type_ != "quotidien":
            return
        if not 'label' in self.today_forecast:
            current_app.logger.error(f'No label for forecast for inscription: id: {self.inscription.id} insee: {self.inscription.commune.insee}')
        if not 'couleur' in self.today_forecast:
            current_app.logger.error(f'No couleur for forecast for inscription: id: {self.inscription.id} insee: {self.inscription.commune.insee}')
        if self.episodes:
            if 'data' in self.episodes:
                self.episodes = self.episodes['data']
            self.polluants = [
                e['lib_pol_normalized']
                for e in self.episodes
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
        self.recommandation_qa = self.get_recommandation(self.recommandations, types=["indice_atmo"])
        self.recommandation_raep = self.get_recommandation(self.recommandations, types=["pollens"])
        self.recommandation_episode = self.get_recommandation(self.recommandations, types=["episode_pollution"])
        self.recommandation_indice_uv = self.get_recommandation(self.recommandations, types=["indice_uv"])
        self.fill_vigilances()

    def fill_vigilances(self):
        if not self.vigilances:
            return
        for phenomene, v in self.vigilances.items():
            setattr(self, f"vigilance_{phenomene}", v['vigilance'])
            setattr(self, f"vigilance_{phenomene}_recommandation", v['recommandation'])
        self.vigilance_globale = self.vigilances['globale']['vigilance']
        self.vigilance_globale_recommandation = self.vigilances['globale']['recommandation']

    @classmethod
    def get_vigilances_recommandations(cls, vigilances, recommandations):
        vigilances_par_phenomenes = {
            k: list(g)
            for k, g in groupby(sorted(vigilances, key=lambda v: v.phenomene_id), lambda v: v.phenomene_id)}
        vigilances_max_couleur = {
            k: max(v, key=lambda v: v.couleur_id) if len(v) > 0 else None 
            for k, v in vigilances_par_phenomenes.items()
        }
        to_return = dict()
        for ph_id, vigilance in vigilances_max_couleur.items():
            if not isinstance(vigilance, VigilanceMeteo):
                continue
            phenomene = cls.phenomenes_sib.get(ph_id)
            try:
                recommandation = next(filter(lambda r: r.is_relevant(types=["vigilance_meteo"], media=["dashboard"], vigilances=[vigilance]), recommandations))
            except StopIteration:
                current_app.logger.info(f"Impossible de trouver une recommandation pour {vigilance.id}")
                recommandation = None
            to_return[phenomene] = {
                "vigilance": db.session.merge(vigilance),
                "recommandation": recommandation
            }
        to_return['globale'] = {"vigilance": None, 'recommandation': None}
        to_return['globale']['vigilance'] = max(chain(vigilances_max_couleur.values()), key=lambda v: v.couleur_id)
        if to_return['globale']['vigilance']:
            to_return['globale']['vigilance'] = db.session.merge(to_return['globale']['vigilance'])
            if to_return['globale']['vigilance'].couleur_id <= 2:
                to_return['globale']['recommandation'] = Recommandation.published_query().filter(
                    Recommandation.vigilance_couleur_ids.contains([to_return['globale']['vigilance'].couleur_id])
                ).first()
        return to_return
    

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
        if not isinstance(self.polluants, list):
            return []
        label_to_symbols = {
            'ozone': "o3",
            'particules_fines': "pm10",
            'dioxyde_azote': "no2",
            "dioxyde_soufre": "so2"
        }
        return [label_to_symbols.get(label) for label in self.polluants]

    @property
    def polluants_symbols_formatted(self):
        return oxford_comma([p.upper() for p in self.polluants_symbols])

    @property
    def today_forecast(self):
        if not self.forecast:
            return dict()
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
    def indice_uv_label(self):
        return self.indice_uv.label if self.indice_uv else None

    @property
    def indice_uv_value(self):
        return self.indice_uv.uv_j0 if self.indice_uv else None

    @property
    def has_depassement(self):
        return len(self.get_depassement) > 0


    @classmethod
    def export(cls, preferred_reco=None, user_seed=None, remove_reco=[], only_to=None, date_=None, media='mail', filter_already_sent=True, type_='quotidien', force_send=False):
        recommandations = Recommandation.shuffled(user_seed=user_seed, preferred_reco=preferred_reco, remove_reco=remove_reco)
        indices, all_episodes, allergenes, vigilances, indices_uv = get_all(date_)
        vigilances_recommandations = {
            dep_code: cls.get_vigilances_recommandations(v, recommandations)
            for dep_code, v in vigilances.items()
        }
        indices_uv = {k: db.session.merge(v) for k, v in indices_uv.items()}
        templates = NewsletterHebdoTemplate.get_templates()
        for inscription in Inscription.export_query(only_to, filter_already_sent, media, type_, date_).yield_per(100):
            init_dict = {"type_": type_}
            if type_ == 'quotidien':
                indice = indices.get(inscription.commune_id)
                episodes = all_episodes.get(inscription.commune.zone_pollution_id)
                if inscription.commune.departement:
                    raep = allergenes.get(inscription.commune.departement.zone_id, None)
                    vigilances_recommandations_dep = vigilances_recommandations.get(inscription.commune.departement.zone_id, {})
                else:
                    raep = None
                    vigilances_recommandations_dep = {}
                raep_dict = raep.to_dict() if raep else {}
                indice_uv = indices_uv.get(inscription.commune_id)
                init_dict.update({
                    "inscription": inscription,
                    "recommandations": recommandations,
                    "forecast": {"data": [indice.dict()]} if indice else None,
                    "episodes": [e.dict() for e in episodes] if episodes else [],
                    "raep": raep_dict.get("total"),
                    "allergenes": raep_dict.get("allergenes"),
                    "validite_raep": raep_dict.get("periode_validite", {}),
                    "vigilances": vigilances_recommandations_dep,
                    "indice_uv": indice_uv
                })
                if date_:
                    init_dict['date'] = date_
            elif type_ == 'hebdomadaire':
                next_template = NewsletterHebdoTemplate.next_template(inscription, templates)
                if not next_template:
                    continue
                init_dict.update({
                    'newsletter_hebdo_template': next_template,
                    'inscription': inscription
                })
            if media == 'notifications_web' and 'notifications_web' in inscription.indicateurs_media:
                for wp in WebpushSubscriptionInfo.query.filter_by(inscription_id=inscription.id):
                    init_dict.update({
                        'webpush_subscription_info_id': wp.id,
                        'webpush_subscription_info': wp
                        }
                    )
                    newsletter = cls(**init_dict)
                    if newsletter.to_send(type_, force_send):
                        yield newsletter
            else:
                newsletter = cls(**init_dict)
                if newsletter.to_send(type_, force_send):
                    yield newsletter

    def to_send(self, type_, force_send):
        if type_ == 'hebdomadaire':
            return self.newsletter_hebdo_template is not None
        if force_send and 'quotidien' in self.inscription.indicateurs_frequence:
            return True
        if self.inscription.indicateurs_frequence and "alerte" in self.inscription.indicateurs_frequence:
            if self.inscription.has_indicateur("indice_atmo") and self.polluants:
                return True
            if self.inscription.has_indicateur("raep") and isinstance(self.raep, int) and self.raep >= 4:
                return True
            if self.inscription.has_indicateur("vigilance_meteo") and isinstance(self.vigilance_globale, VigilanceMeteo) and self.vigilance_globale.couleur_id > 2:
                return True
            if self.inscription.has_indicateur("indice_uv") and isinstance(self.indice_uv_value, int) and self.indice_uv_value >= 3:
                return True
            return False
        if self.inscription.has_indicateur("indice_atmo") and not self.label:
            return False
        if self.inscription.has_indicateur("raep") and not isinstance(self.raep, int):
            return False
        if self.inscription.has_indicateur("vigilance_meteo") and not isinstance(self.vigilance_globale, VigilanceMeteo):
            return False
        return True

    @property
    def errors(self):
        errors = []
        if self.type_ == 'quotidien':
            if self.inscription.has_indicateur("indice_atmo") and not self.label:
                errors.append({
                    "type": "no_air_quality",
                    "region": self.inscription.commune.departement.region.nom if self.inscription.commune.departement else "",
                    "ville": self.inscription.commune.nom,
                    "insee": self.inscription.commune.insee
                })
            if self.inscription.has_indicateur("raep") and self.raep is None:
                errors.append({
                    "type": "no_raep",
                    "region": self.inscription.commune.departement.nom if self.inscription.commune.departement else "",
                    "ville": self.inscription.commune.nom,
                    "insee": self.inscription.commune.insee
                })
        elif self.type_ == 'hebdomadaire':
            if self.newsletter_hebdo_template == None:
                errors.append({
                    "type": "no_template_weekly_nl",
                    "inscription_id": self.inscription.id,
                    "mail": self.inscription.mail
                })
        return errors

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

    def eligible_recommandations(self, recommandations: Dict[int, Recommandation], types=["indice_atmo", "episode_pollution", "pollens", "indice_uv"]):
        if not recommandations:
            return
            yield # See https://stackoverflow.com/questions/13243766/python-empty-generator-function
        if self.inscription.last_month_newsletters:
            last_nl = self.inscription.last_month_newsletters[0]
        else:
            last_nl = None
        recommandations_id = set(recommandations.keys())
        sorted_recommandation_ids = list()
        for nl in self.inscription.last_month_newsletters:
            if nl.recommandation_id in recommandations_id:
                sorted_recommandation_ids.append((nl.date, nl.recommandation_id))
                recommandations_id.discard(nl.recommandation_id)
        for recommandation_id in recommandations_id:
            sorted_recommandation_ids.append((datetime.min.date(), recommandation_id))

        last_recommandation = recommandations.get(last_nl.recommandation_id) if last_nl else None
        last_criteres = last_recommandation.criteres if last_recommandation else set()
        last_type = last_recommandation.type_ if last_recommandation else ""

        sorted_recommandations_ids_by_criteria = sorted(
                sorted_recommandation_ids,
                key=lambda r: (r[0], recommandations[r[1]].ordre if recommandations[r[1]].ordre != None else inf, len(recommandations[r[1]].criteres.intersection(last_criteres)), recommandations[r[1]].type_ != last_type)
            )
        for r in sorted_recommandations_ids_by_criteria:
            if recommandations[r[1]].is_relevant(
                inscription=self.inscription,
                qualif=self.qualif,
                polluants=self.polluants,
                raep=self.raep,
                date_=self.date,
                indice_uv=self.indice_uv_value,
                media='mail',
                types=types
            ):
                yield recommandations[r[1]]


    def get_recommandation(self, recommandations: List[Recommandation], types=["indice_atmo", "episode_pollution", "pollens", "indice_uv"]):
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
        }.get(value, "")

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
        elif self.raep < 4 and isinstance(self.inscription.indicateurs_frequence, list) and "alerte" in self.inscription.indicateurs_frequence:
            return False
        return True

    @property
    def show_vigilance(self):
        return self.inscription.has_indicateur("vigilance_meteo")

    @property
    def show_qa(self):
        return self.inscription.has_indicateur("indice_atmo")

    @property
    def show_radon(self):
        if self.polluants:
            return False
        if type(self.raep) == int and isinstance(self.inscription.indicateurs, list):
            if "raep" in self.inscription.indicateurs and self.raep != 0:
                return False
            if not "raep" in self.inscription.indicateurs and self.raep >= 4:
                return False
        if self.qualif not in ['bon', 'moyen']:
            return False
        try:
            last_radon = next(filter(lambda nl: nl.show_radon, self.inscription.last_month_newsletters))
        except StopIteration:
            return True
        days_since_last_sent = (date.today() - last_radon.date).days
        if self.radon == 3 and days_since_last_sent >= 15:
            return True
        if self.radon < 3 and days_since_last_sent >= 30:
            return True
        return False

    @property
    def show_indice_uv(self):
        return self.inscription.has_indicateur("indice_uv")

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
    recommandation_episode_id: int = db.Column(db.Integer, db.ForeignKey('recommandation.id'))
    recommandation_episode: Recommandation = db.relationship("Recommandation", foreign_keys=[recommandation_episode_id])
    recommandation_indice_uv_id: int = db.Column(db.Integer, db.ForeignKey('recommandation.id'))
    recommandation_indice_uv: Recommandation = db.relationship("Recommandation", foreign_keys=[recommandation_indice_uv_id])
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
    indice_uv_label: str = db.Column(db.String())
    indice_uv_value: int = db.Column(db.Integer())
    indice_uv_zone_id: int = db.Column(db.Integer(), db.ForeignKey(IndiceUv.zone_id))
    indice_uv_date: date = db.Column(db.Date(), db.ForeignKey(IndiceUv.date))
    show_raep = db.Column(db.Boolean())
    show_radon = db.Column(db.Boolean())
    show_indice_uv = db.Column(db.Boolean())
    sous_indices: dict = db.Column(postgresql.JSONB)
    webpush_subscription_info_id: int = db.Column(db.Integer, db.ForeignKey('webpush_subscription_info.id'), index=True)
    webpush_subscription_info: WebpushSubscriptionInfo = db.relationship(WebpushSubscriptionInfo)
    mail_list_id: int = db.Column(db.Integer)
    newsletter_hebdo_template_id: int = db.Column(db.Integer(), db.ForeignKey('newsletter_hebdo_template.id'))
    newsletter_hebdo_template: NewsletterHebdoTemplate = db.relationship(NewsletterHebdoTemplate)

    vigilance_vent_id: VigilanceMeteo = db.Column(db.Integer(), db.ForeignKey(VigilanceMeteo.id))
    vigilance_vent: VigilanceMeteo = db.relationship(VigilanceMeteo, foreign_keys=[vigilance_vent_id])
    vigilance_vent_recommandation_id: Recommandation = db.Column(db.Integer, db.ForeignKey('recommandation.id'))
    vigilance_vent_recommandation: Recommandation = db.relationship("Recommandation", foreign_keys=[vigilance_vent_recommandation_id])

    vigilance_pluie_id: VigilanceMeteo = db.Column(db.Integer(), db.ForeignKey(VigilanceMeteo.id))
    vigilance_pluie: VigilanceMeteo = db.relationship(VigilanceMeteo, foreign_keys=[vigilance_pluie_id])
    vigilance_pluie_recommandation_id: Recommandation = db.Column(db.Integer, db.ForeignKey('recommandation.id'))
    vigilance_pluie_recommandation: Recommandation = db.relationship("Recommandation", foreign_keys=[vigilance_pluie_recommandation_id])

    vigilance_orages_id: VigilanceMeteo = db.Column(db.Integer(), db.ForeignKey(VigilanceMeteo.id))
    vigilance_orages: VigilanceMeteo = db.relationship(VigilanceMeteo, foreign_keys=[vigilance_orages_id])
    vigilance_orages_recommandation_id: Recommandation = db.Column(db.Integer, db.ForeignKey('recommandation.id'))
    vigilance_orages_recommandation: Recommandation = db.relationship("Recommandation", foreign_keys=[vigilance_orages_recommandation_id])

    vigilance_crues_id: VigilanceMeteo = db.Column(db.Integer(), db.ForeignKey(VigilanceMeteo.id))
    vigilance_crues: VigilanceMeteo = db.relationship(VigilanceMeteo, foreign_keys=[vigilance_crues_id])
    vigilance_crues_recommandation_id: Recommandation = db.Column(db.Integer, db.ForeignKey('recommandation.id'))
    vigilance_crues_recommandation: Recommandation = db.relationship("Recommandation", foreign_keys=[vigilance_crues_recommandation_id])

    vigilance_neige_id: VigilanceMeteo = db.Column(db.Integer(), db.ForeignKey(VigilanceMeteo.id))
    vigilance_neige: VigilanceMeteo = db.relationship(VigilanceMeteo, foreign_keys=[vigilance_neige_id])
    vigilance_neige_recommandation_id: Recommandation = db.Column(db.Integer, db.ForeignKey('recommandation.id'))
    vigilance_neige_recommandation: Recommandation = db.relationship("Recommandation", foreign_keys=[vigilance_neige_recommandation_id])

    vigilance_canicule_id: VigilanceMeteo = db.Column(db.Integer(), db.ForeignKey(VigilanceMeteo.id))
    vigilance_canicule: VigilanceMeteo = db.relationship(VigilanceMeteo, foreign_keys=[vigilance_canicule_id])
    vigilance_canicule_recommandation_id: Recommandation = db.Column(db.Integer, db.ForeignKey('recommandation.id'))
    vigilance_canicule_recommandation: Recommandation = db.relationship("Recommandation", foreign_keys=[vigilance_canicule_recommandation_id])

    vigilance_froid_id: VigilanceMeteo = db.Column(db.Integer(), db.ForeignKey(VigilanceMeteo.id))
    vigilance_froid: VigilanceMeteo = db.relationship(VigilanceMeteo, foreign_keys=[vigilance_froid_id])
    vigilance_froid_recommandation_id: Recommandation = db.Column(db.Integer, db.ForeignKey('recommandation.id'))
    vigilance_froid_recommandation: Recommandation = db.relationship("Recommandation", foreign_keys=[vigilance_froid_recommandation_id])

    vigilance_avalanches_id: VigilanceMeteo = db.Column(db.Integer(), db.ForeignKey(VigilanceMeteo.id))
    vigilance_avalanches: VigilanceMeteo = db.relationship(VigilanceMeteo, foreign_keys=[vigilance_avalanches_id])
    vigilance_avalanches_recommandation_id: Recommandation = db.Column(db.Integer, db.ForeignKey('recommandation.id'))
    vigilance_avalanches_recommandation: Recommandation = db.relationship("Recommandation", foreign_keys=[vigilance_avalanches_recommandation_id])

    vigilance_vagues_id: VigilanceMeteo = db.Column(db.Integer(), db.ForeignKey(VigilanceMeteo.id))
    vigilance_vagues: VigilanceMeteo = db.relationship(VigilanceMeteo, foreign_keys=[vigilance_vagues_id])
    vigilance_vagues_recommandation_id: Recommandation = db.Column(db.Integer, db.ForeignKey('recommandation.id'))
    vigilance_vagues_recommandation: Recommandation = db.relationship("Recommandation", foreign_keys=[vigilance_vagues_recommandation_id])

    vigilance_globale_id: VigilanceMeteo = db.Column(db.Integer(), db.ForeignKey(VigilanceMeteo.id))
    vigilance_globale: VigilanceMeteo = db.relationship(VigilanceMeteo, foreign_keys=[vigilance_globale_id])
    vigilance_globale_recommandation_id: Recommandation = db.Column(db.Integer, db.ForeignKey('recommandation.id'))
    vigilance_globale_recommandation: Recommandation = db.relationship("Recommandation", foreign_keys=[vigilance_globale_recommandation_id])
    __table_args__ = (
        ForeignKeyConstraint([indice_uv_zone_id, indice_uv_date], [IndiceUv.zone_id, IndiceUv.date]),
    )

    def __init__(self, newsletter: Newsletter, mail_list_id=None):
        self.inscription = newsletter.inscription
        self.inscription_id = newsletter.inscription.id
        self.lien_aasqa = newsletter.inscription.commune.departement.region.aasqa_website if newsletter.inscription.commune.departement else "",
        self.nom_aasqa = newsletter.inscription.commune.departement.region.aasqa_nom if newsletter.inscription.commune.departement else "",
        self.recommandation = newsletter.recommandation
        self.recommandation_id = newsletter.recommandation.id if newsletter.recommandation else None
        self.recommandation_qa = newsletter.recommandation_qa
        self.recommandation_qa_id = newsletter.recommandation_qa.id if newsletter.recommandation_qa else None
        self.recommandation_raep = newsletter.recommandation_raep
        self.recommandation_raep_id = newsletter.recommandation_raep.id if newsletter.recommandation_raep else None
        self.recommandation_episode = newsletter.recommandation_episode
        self.recommandation_episode_id = newsletter.recommandation_episode.id if newsletter.recommandation_episode else None
        self.recommandation_indice_uv = newsletter.recommandation_indice_uv
        self.recommandation_indice_uv_id = newsletter.recommandation_indice_uv.id if newsletter.recommandation_indice_uv else None
        self.date = newsletter.date
        self.qualif = newsletter.qualif
        self.label = newsletter.label
        self.couleur = newsletter.couleur
        self.polluants = newsletter.polluants
        self.raep = int(newsletter.raep) if newsletter.raep is not None else None
        self.allergenes = newsletter.allergenes
        self.raep_debut_validite = newsletter.validite_raep.get('debut')
        self.raep_fin_validite = newsletter.validite_raep.get('fin')
        self.indice_uv_label = newsletter.indice_uv_label
        self.indice_uv_value = newsletter.indice_uv_value
        self.indice_uv_zone_id = newsletter.indice_uv.zone_id if newsletter.indice_uv else None
        self.indice_uv_date = newsletter.indice_uv.date if newsletter.indice_uv else None
        self.indice_uv = newsletter.indice_uv
        self.show_raep = newsletter.show_raep
        self.show_radon = newsletter.show_radon
        self.show_indice_uv = newsletter.show_indice_uv
        self.sous_indices = newsletter.sous_indices
        self.webpush_subscription_info_id = newsletter.webpush_subscription_info_id
        self.webpush_subscription_info = newsletter.webpush_subscription_info
        self.mail_list_id = mail_list_id
        self.newsletter_hebdo_template = newsletter.newsletter_hebdo_template
        self.newsletter_hebdo_template_id = newsletter.newsletter_hebdo_template.id if newsletter.newsletter_hebdo_template else None
        for phenomene in self.phenomenes_sib.values():
            key = f"vigilance_{phenomene}"
            setattr(self, key, getattr(newsletter, key))
            if getattr(self, key):
                setattr(self, f"{key}_id", getattr(self, key).id)
            key = f"vigilance_{phenomene}_recommandation"
            setattr(self, key, getattr(newsletter, key))
            if getattr(self, key):
                setattr(self, f"{key}_id", getattr(self, key).id)
        self.vigilance_globale = newsletter.vigilance_globale
        self.vigilance_globale_id = newsletter.vigilance_globale.id if self.vigilance_globale else None
        self.vigilance_globale_recommandation = newsletter.vigilance_globale_recommandation
        self.vigilance_globale_recommandation_id = newsletter.vigilance_globale_recommandation.id if self.vigilance_globale_recommandation else None

    @property
    def vigilances_dict(self):
        max_couleur = VigilanceMeteo.make_max_couleur(
            list(filter(None, map(lambda ph: getattr(self, f"vigilance_{ph}"), self.phenomenes_sib.values())))
        )
        to_return = dict()
        for phenomene in self.phenomenes_sib.values():
            key = f"vigilance_{phenomene}"
            vigilance = getattr(self, key)
            recommandation = getattr(self, f"{key}_recommandation")
            to_return[f"{key.upper()}_RECOMMANDATION"] = ""
            to_return[f"{key.upper()}_COULEUR"] = ""
            if vigilance and vigilance.couleur_id == max_couleur:
                to_return[f"{key.upper()}_COULEUR"] = vigilance.couleur
            if recommandation:
                to_return[f"{key.upper()}_RECOMMANDATION"] = recommandation.recommandation_sanitized
        to_return['VIGILANCE_GLOBALE_COULEUR'] = ""
        if self.vigilance_globale:
            to_return['VIGILANCE_GLOBALE_COULEUR'] = self.vigilance_globale.couleur
        to_return['VIGILANCE_GLOBALE_RECOMMANDATION'] = ""
        if self.vigilance_globale_recommandation:
            to_return['VIGILANCE_GLOBALE_RECOMMANDATION'] = self.vigilance_globale_recommandation.recommandation_sanitized
        return to_return

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
                'RECOMMANDATION': (self.recommandation.format(self.inscription) or "") if self.recommandation else "",
                'LIEN_AASQA': self.lien_aasqa,
                'NOM_AASQA': self.nom_aasqa,
                'PRECISIONS': (self.recommandation.precisions or "") if self.recommandation else "",
                'QUALITE_AIR': self.label or "",
                'VILLE': self.inscription.commune.nom or "",
                'VILLE_CODE': self.inscription.commune.insee or "",
                'VILLE_SLUG': self.inscription.commune.slug or "",
                'BACKGROUND_COLOR': self.couleur or "",
                'SHORT_ID': self.short_id or "",
                'POLLUANT': self.polluants_symbols_formatted or "",
                'RAEP': self.qualif_raep.capitalize() or "",
                'BACKGROUND_COLOR_RAEP': self.couleur_raep or "",
                'USER_UID': self.inscription.uid,
                'AUTH_TOKEN': authenticator.make_token(self.inscription.uid),
                'DEPARTEMENT': self.inscription.commune.departement_nom,
                'DEPARTEMENT_PREPOSITION': self.departement_preposition or "",
                "RAEP_DEBUT_VALIDITE": self.raep_debut_validite,
                "RAEP_FIN_VALIDITE": self.raep_fin_validite,
                'QUALITE_AIR_VALIDITE': self.date.strftime('%d/%m/%Y'),
                'INDICE_UV_VALIDITE': self.date.strftime('%d/%m/%Y'),
                'POLLINARIUM_SENTINELLE': convert_bool_to_yes_no((False if not self.inscription.commune or not self.inscription.commune.pollinarium_sentinelle else True)),
                'INDICE_UV_LABEL': self.indice_uv_label or "",
                'INDICE_UV_VALUE': self.indice_uv_value or "",
                'SHOW_QA': convert_bool_to_yes_no(self.show_qa),
                'SHOW_RAEP': convert_bool_to_yes_no(self.show_raep),
                'SHOW_VIGILANCE': convert_bool_to_yes_no(self.show_vigilance),
                'SHOW_RADON': convert_bool_to_yes_no(self.show_radon),
                'SHOW_INDICE_UV': convert_bool_to_yes_no(self.show_indice_uv),
                'INDICATEURS_FREQUENCE': self.inscription.indicateurs_frequence[0] if self.inscription.indicateurs_frequence else "",
                'RECOMMANDATION_QA': (self.recommandation_qa.format(self.inscription) or "") if self.recommandation_qa else "",
                'RECOMMANDATION_RAEP': self.recommandation_raep.format(self.inscription) if self.recommandation_raep else "",
                'RECOMMANDATION_EPISODE': self.recommandation_episode.format(self.inscription) if self.recommandation_episode else "",
                'RECOMMANDATION_INDICE_UV': (self.recommandation_indice_uv.format(self.inscription) or "") if self.recommandation_indice_uv else "",
                'NEW_USER': convert_bool_to_yes_no(str(self.inscription.date_inscription) > '2021-10-14'),
                'INDICATEURS_MEDIA': self.inscription.indicateurs_medias_lib,
                "VIGILANCE_VALIDITE_DEBUT": VigilanceMeteo.make_start_date([self.vigilance_globale]).strftime('%d/%m/%Y à %H:%M') if self.vigilance_globale else "",
                "VIGILANCE_VALIDITE_FIN": VigilanceMeteo.make_end_date([self.vigilance_globale]).strftime('%d/%m/%Y à %H:%M') if self.vigilance_globale else "",
                "VIGILANCE_LABEL": VigilanceMeteo.make_label(self.vigilance_globale.couleur_id) if self.vigilance_globale else "",
            },
            **{f'ALLERGENE_{a[0]}': int(a[1]) for a in (self.allergenes if type(self.allergenes) == dict else dict() ).items()},
            **dict(chain(*[[(f'SS_INDICE_{si.upper()}_LABEL', get_sous_indice(si).get('label') or ""), (f'SS_INDICE_{si.upper()}_COULEUR', get_sous_indice(si).get('couleur') or "")] for si in noms_sous_indices])),
            **self.vigilances_dict
        }

    header = ['EMAIL','RECOMMANDATION','LIEN_AASQA','NOM_AASQA','PRECISIONS','QUALITE_AIR','VILLE','VILLE_CODE','VILLE_SLUG','BACKGROUND_COLOR','SHORT_ID','POLLUANT',
'LIEN_RECOMMANDATIONS_ALERTE','SHOW_RAEP','RAEP','BACKGROUND_COLOR_RAEP','USER_UID','AUTH_TOKEN','DEPARTEMENT','DEPARTEMENT_PREPOSITION','OBJECTIF','RAEP_DEBUT_VALIDITE',
'RAEP_FIN_VALIDITE','QUALITE_AIR_VALIDITE','INDICE_UV_VALIDITE','POLLINARIUM_SENTINELLE','INDICE_UV_LABEL','INDICE_UV_VALUE','SHOW_QA','SHOW_RADON','SHOW_INDICE_UV','INDICATEURS_FREQUENCE','RECOMMANDATION_QA','RECOMMANDATION_RAEP',
'RECOMMANDATION_EPISODE','RECOMMANDATION_INDICE_UV','NEW_USER','INDICATEURS_MEDIA','ALLERGENE_aulne','ALLERGENE_chene','ALLERGENE_frene','ALLERGENE_rumex','ALLERGENE_saule',
'ALLERGENE_charme','ALLERGENE_cypres','ALLERGENE_bouleau','ALLERGENE_olivier','ALLERGENE_platane','ALLERGENE_tilleul','ALLERGENE_armoises','ALLERGENE_peuplier',
'ALLERGENE_plantain','ALLERGENE_graminees','ALLERGENE_noisetier','ALLERGENE_ambroisies','ALLERGENE_urticacees','ALLERGENE_chataignier','SS_INDICE_NO2_LABEL',
'SS_INDICE_NO2_COULEUR','SS_INDICE_SO2_LABEL','SS_INDICE_SO2_COULEUR','SS_INDICE_O3_LABEL','SS_INDICE_O3_COULEUR','SS_INDICE_PM10_LABEL','SS_INDICE_PM10_COULEUR',
'SS_INDICE_PM25_LABEL','SS_INDICE_PM25_COULEUR', 'VIGILANCE_VALIDITE_FIN', 'VIGILANCE_LABEL', 'VIGILANCE_VALIDITE_DEBUT', 'VIGILANCE_GLOBALE_RECOMMANDATION',
 'SHOW_VIGILANCE', 'VIGILANCE_GLOBALE_COULEUR'] + [f'VIGILANCE_{ph.upper()}_COULEUR' for ph in Newsletter.phenomenes_sib.values()] + [f'VIGILANCE_{ph.upper()}_RECOMMANDATION' for ph in Newsletter.phenomenes_sib.values()]

    @property
    def webpush_data(self):
        commune = self.inscription.commune
        try:
            different_locale('fr_FR.utf8')
            different_locale('fr_FR.UTF-8')
        except Exception as e:
            current_app.logger.error(e)
        title = f'{commune.nom.capitalize()}, le {date.today().strftime("%A %d %B")}'
        array_body = []
        if self.inscription.has_indicateur("indice_atmo") and self.label:
            array_body.append(f"Indice de la qualité de l’air : {self.label.capitalize()}.")
        if self.inscription.has_indicateur("raep") and self.qualif_raep:
            array_body.append(f"Risque d’allergie aux pollens : {self.qualif_raep.capitalize()}.")
        if self.inscription.has_indicateur("vigilance_meteo") and self.vigilance_globale:
            array_body.append(f"Vigilance météo : {self.vigilance_globale.couleur}")
        if self.inscription.has_indicateur("indice_uv") and self.indice_uv_label:
            array_body.append(f"Indice UV : {self.indice_uv_label}.")
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
