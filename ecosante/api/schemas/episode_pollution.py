from ecosante.api.schemas.indice import FullIndiceSchema, IndiceDetailsSchema, NestedIndiceSchema
from marshmallow import fields, pre_dump
from ecosante.utils.funcs import oxford_comma

class EpisodeIndiceDetailsSchema(IndiceDetailsSchema):
    level = fields.String()
    @pre_dump
    def dump_details(self, data, **kwargs):
        return {
            "label": data["lib_pol"],
            "level": data["etat"].capitalize()
        }

class IndiceSchema(EpisodeIndiceDetailsSchema):
    details = fields.List(fields.Nested(EpisodeIndiceDetailsSchema))

    def make_label_level(self, data):
        if len(data) == 0:
            return {"label": "", "level": ""}
        def sorter(v):
            etat = v['etat'].lower()
            if "alerte" in etat:
                return 0
            elif "information" in etat:
                return 1
            else:
                return 2
        sorted_polluants = sorted(data, key=sorter)
        higher_level = sorted_polluants[0]['etat']
        if higher_level == "PAS DE DEPASSEMENT":
            return {"label": "Pas de dépassement", "level": "Pas de dépassement"}
        higher_polluants = filter(lambda v: higher_level == v['etat'], sorted_polluants)
        preposition = "au"
        if len(higher_polluants) > 1 or 'PM' in higher_polluants[0]:
            preposition = "aux"
        if "alerte" in higher_level:
            level = "Alerte"
        else:
            level = "Information"
        return  {
            "label": f"Épisode de pollution {preposition} : {oxford_comma([v['lib_pol'] for v in higher_polluants])}",
            "level": level
        }

    @pre_dump
    def dump_details(self, data, **kwargs):
        label_level = self.make_label_level(data['data'])
        return {
            "label": label_level['label'],
            "level": label_level['level'],
            "details": data['data']
        }

class EpisodePollutionSchema(FullIndiceSchema):
    indice = fields.Nested(IndiceSchema)
    @pre_dump
    def dump_details(self, data, **kwargs):
        return data