from calendar import different_locale
from dataclasses import dataclass
from datetime import date
from itertools import chain
from sqlalchemy import ForeignKeyConstraint, text
from sqlalchemy.dialects import postgresql
from typing import List

from ecosante.extensions import db, authenticator
from ecosante.inscription.models import Inscription, WebpushSubscriptionInfo
from ecosante.recommandations.models import Recommandation
from ecosante.newsletter.models.newsletter import Newsletter
from ecosante.newsletter.models.newsletter_hebdo_template import NewsletterHebdoTemplate

from indice_pollution.history.models import IndiceUv, VigilanceMeteo

from ecosante.utils.funcs import generate_line


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
    indice_uv_zone_id: int = db.Column(db.Integer)
    indice_uv_date: date = db.Column(db.Date())
    indice_uv: IndiceUv = db.relationship(IndiceUv, foreign_keys=[indice_uv_zone_id, indice_uv_date])
    show_raep = db.Column(db.Boolean())
    show_radon = db.Column(db.Boolean())
    show_indice_uv = db.Column(db.Boolean())
    show_qa = db.Column(db.Boolean())
    show_vigilance = db.Column(db.Boolean())
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
        self.show_indice_uv = newsletter.show_indice_uv
        self.show_qa = newsletter.show_qa
        self.show_vigilance = newsletter.show_vigilance
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
                'DEPARTEMENT': self.inscription.commune.departement.nom_charniere if self.inscription.commune and self.inscription.commune.departement else "",
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
'RAEP_FIN_VALIDITE','QUALITE_AIR_VALIDITE','INDICE_UV_VALIDITE','POLLINARIUM_SENTINELLE','INDICE_UV_LABEL','INDICE_UV_VALUE','SHOW_QA','SHOW_INDICE_UV','INDICATEURS_FREQUENCE','RECOMMANDATION_QA','RECOMMANDATION_RAEP',
'RECOMMANDATION_EPISODE','RECOMMANDATION_INDICE_UV','NEW_USER','INDICATEURS_MEDIA','ALLERGENE_aulne','ALLERGENE_chene','ALLERGENE_frene','ALLERGENE_rumex','ALLERGENE_saule',
'ALLERGENE_charme','ALLERGENE_cypres','ALLERGENE_bouleau','ALLERGENE_olivier','ALLERGENE_platane','ALLERGENE_tilleul','ALLERGENE_armoises','ALLERGENE_peuplier',
'ALLERGENE_plantain','ALLERGENE_graminees','ALLERGENE_noisetier','ALLERGENE_ambroisies','ALLERGENE_urticacees','ALLERGENE_chataignier','SS_INDICE_NO2_LABEL',
'SS_INDICE_NO2_COULEUR','SS_INDICE_SO2_LABEL','SS_INDICE_SO2_COULEUR','SS_INDICE_O3_LABEL','SS_INDICE_O3_COULEUR','SS_INDICE_PM10_LABEL','SS_INDICE_PM10_COULEUR',
'SS_INDICE_PM25_LABEL','SS_INDICE_PM25_COULEUR', 'VIGILANCE_VALIDITE_FIN', 'VIGILANCE_LABEL', 'VIGILANCE_VALIDITE_DEBUT', 'VIGILANCE_GLOBALE_RECOMMANDATION',
 'SHOW_VIGILANCE', 'VIGILANCE_GLOBALE_COULEUR'] + [f'VIGILANCE_{ph.upper()}_COULEUR' for ph in Newsletter.phenomenes_sib.values()] + [f'VIGILANCE_{ph.upper()}_RECOMMANDATION' for ph in Newsletter.phenomenes_sib.values()]

    @property
    def webpush_data(self):
        commune = self.inscription.commune
        with different_locale('fr_FR.utf8'):
            title = f'{commune.nom.capitalize()}, le {date.today().strftime("%A %d %B")}'
        body = ""
        first_line = []
        if self.inscription.has_indicateur("indice_atmo") and self.label:
            first_line.append(f"Air : {self.label.lower()}")
        if self.inscription.has_indicateur("raep") and self.qualif_raep:
            first_line.append(f"Pollens : {self.qualif_raep.lower()}")
        body += ". ".join(first_line)
        if len(body) > 0:
            body += "\n"
        second_line = []
        if self.inscription.has_indicateur("vigilance_meteo") and self.vigilance_globale and self.vigilance_globale.couleur:
            second_line.append(f"Vigilance météo : {self.vigilance_globale.couleur.lower()}")
        if self.inscription.has_indicateur("indice_uv") and self.indice_uv_value:
            second_line.append(f"UV : {self.indice_uv_value}")
        body += ". ".join(second_line)
        return {
            "title": title,
            "body": body,
            "link": f"https://recosante.beta.gouv.fr/place/{commune.insee}/{commune.slug}/"
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
