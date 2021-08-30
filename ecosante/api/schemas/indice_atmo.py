from marshmallow.utils import pprint
from .indice import FullIndiceSchema, IndiceDetailsSchema, IndiceSchema, NestedIndiceSchema
from marshmallow import fields, pre_dump
from datetime import timedelta


class NestedIndiceATMOSchema(NestedIndiceSchema):
    value = fields.Integer(attribute='valeur')
    color = fields.String(attribute='couleur')

class IndiceATMODetailsSchema(IndiceDetailsSchema):
    label = fields.String(attribute='polluant_name')
    indice = fields.Nested(NestedIndiceATMOSchema)

    @pre_dump
    def envelop_data(self, data, **kwargs):
        data['indice'] = {k: v for k, v in data.items() if k != 'polluant_name'}
        return data

class IndiceATMOSchema(NestedIndiceATMOSchema):
    details = fields.List(fields.Nested(IndiceATMODetailsSchema), attribute='sous_indices')

class IndiceATMO(FullIndiceSchema):
    indice = fields.Nested(IndiceATMOSchema)

    @pre_dump
    def load_indice_atmo(self, data, many, **kwargs):
        return {
            "indice": data["indice"].dict(),
            "validity": {
                "start": data["indice"].date_ech,
                "end": data["indice"].date_ech + timedelta(1) - timedelta(seconds=1),
                "area": data["indice"].commune.nom
            },
            "sources": [
                {
                   "label":  data["indice"].region.Service.nom_aasqa,
                   "url": data["indice"].region.Service.website
                }
            ],
            "advice": data['advice']
        }