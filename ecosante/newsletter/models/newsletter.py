from dataclasses import dataclass, field
from datetime import datetime
from flask import current_app, url_for
from itertools import groupby, chain
from math import inf
from typing import Dict, List

from ecosante.extensions import db
from ecosante.inscription.models import Inscription, WebpushSubscriptionInfo
from ecosante.newsletter.models.newsletter_hebdo_template import NewsletterHebdoTemplate
from ecosante.recommandations.models import Recommandation
from ecosante.utils.funcs import (
    convert_boolean_to_oui_non,
    generate_line,
    oxford_comma
)

from indice_pollution import today, raep as get_raep, get_all
from indice_pollution.history.models import VigilanceMeteo
from indice_pollution.history.models import IndiceUv

FR_DATE_FORMAT = '%d/%m/%Y'


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
    force_send: bool = False

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
    def valeur(self):
        return self.today_forecast.get('valeur')

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
            init_dict = {"type_": type_, "force_send": force_send}
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
        if force_send and self.inscription.has_frequence("quotidien"):
            return True
        if not self.is_init_qa and self.inscription.has_indicateur("indice_atmo"):
            return False
        if not self.is_init_raep and self.inscription.has_indicateur("raep"):
            return False
        if not self.is_init_vigilance and self.inscription.has_indicateur("vigilance_meteo"):
            return False
        if not self.is_init_indice_uv and self.inscription.has_indicateur("indice_uv"):
            return False
        return self.show_qa or self.show_raep or self.show_vigilance or self.show_indice_uv

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
            _external=True
        )

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
    def is_init_raep(self):
        return isinstance(self.raep, int)

    @property
    def show_raep(self):
        if not self.inscription.has_indicateur("raep"):
            return False
        if not self.is_init_raep:
            return self.force_send
        if self.inscription.has_frequence("alerte"):
            return self.raep >= 1
        else:
            return self.raep > 0

    @property
    def is_init_vigilance(self):
        return isinstance(getattr(self.vigilance_globale, 'couleur_id', None), int)

    @property
    def show_vigilance(self):
        if not self.inscription.has_indicateur("vigilance_meteo"):
            return False
        if not self.is_init_vigilance:
            return self.force_send
        if self.inscription.has_frequence("alerte"):
            return self.vigilance_globale.couleur_id > 2
        return True

    @property
    def is_init_qa(self):
        return  isinstance(self.valeur, int)

    @property
    def show_qa(self):
        if not self.inscription.has_indicateur("indice_atmo"):
            return False
        if not self.is_init_qa:
            return self.force_send
        if self.inscription.has_frequence("alerte"):
            return self.valeur > 2
        return self.valeur in range(1, 8)

    @property
    def is_init_indice_uv(self):
        return self.indice_uv != None and isinstance(self.indice_uv.uv_j0, int)

    @property
    def show_indice_uv(self):
        if not self.inscription.has_indicateur("indice_uv"):
            return False
        if not self.is_init_indice_uv:
            return self.force_send
        if self.inscription.has_frequence("alerte"):
            if self.indice_uv.uv_j0 <= 2:
                return False
            if 3 <= self.indice_uv.uv_j0 <= 5:
                return self.inscription.has_enfants
            return True # >= 8
        else:
            return True