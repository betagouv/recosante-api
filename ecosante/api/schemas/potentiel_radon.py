from .indice import FullIndiceSchema, IndiceSchema
from marshmallow import fields

class PotentielRadonSchema(IndiceSchema):
    value = fields.Integer(attribute='classe_potentiel')

class FullPotentielRadonSchema(FullIndiceSchema):
    indice = fields.Nested(PotentielRadonSchema)