from typing import List
from indice_pollution.history.models.episode_pollution import EpisodePollution
from ecosante.api.schemas.indice import FullIndiceSchema, IndiceDetailsSchema, NestedIndiceSchema
from marshmallow import fields, pre_dump
from ecosante.utils.funcs import oxford_comma

class EpisodeIndiceDetailsSchema(IndiceDetailsSchema):
    level = fields.String()
    @pre_dump
    def dump_details(self, data, **kwargs):
        return {
            "label": data.lib_pol_normalized.capitalize(),
            "level": data.lib_etat.capitalize()
        }

class IndiceSchema(EpisodeIndiceDetailsSchema):
    details = fields.List(fields.Nested(EpisodeIndiceDetailsSchema))

    def make_label_level(self, episodes: List[EpisodePollution]):
        if len(episodes) == 0:
            return {"label": "", "level": ""}
        episodes_etat_haut = EpisodePollution.filter_etat_haut(episodes)
        if episodes_etat_haut == []:
            return {"label": "Pas de depassement", "level": "Pas de depassement"}
        preposition = "au"
        if len(episodes_etat_haut) > 1 or 'particules' in episodes_etat_haut[0].lib_pol.lower():
            preposition = "aux"
        return  {
            "label": f"Épisode de pollution {preposition} : {oxford_comma([v.lib_pol_normalized for v in episodes_etat_haut])}",
            "level": episodes_etat_haut[0].lib_etat.capitalize()
        }

    @pre_dump
    def dump_details(self, episodes, **kwargs):
        label_level = self.make_label_level(episodes)
        return {
            "label": label_level['label'],
            "level": label_level['level'],
            "details": episodes
        }

class EpisodePollutionSchema(FullIndiceSchema):
    indice = fields.Nested(IndiceSchema)