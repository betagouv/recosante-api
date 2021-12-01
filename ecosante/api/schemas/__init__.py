from marshmallow import fields, Schema
from .commune import CommuneSchema
from .indice_atmo import IndiceATMO
from .indice_raep import IndiceRAEP
from .potentiel_radon import FullPotentielRadonSchema
from .episode_pollution import EpisodePollutionSchema

class ResponseSchema(Schema):
    commune = fields.Nested(CommuneSchema)
    indice_atmo = fields.Nested(IndiceATMO)
    raep = fields.Nested(IndiceRAEP)
    potentiel_radon = fields.Nested(FullPotentielRadonSchema)
    episodes_pollution = fields.Nested(EpisodePollutionSchema)

class QuerySchema(Schema):
    insee = fields.String()
    date = fields.Date()
    show_raep = fields.Boolean()