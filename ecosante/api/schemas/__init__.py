from marshmallow import fields, Schema
from .commune import CommuneSchema
from .indice_atmo import IndiceATMO
from .indice_raep import IndiceRAEP
from .potentiel_radon import FullPotentielRadonSchema
from .episode_pollution import EpisodePollutionSchema
from .vigilance_meteo import VigilanceMeteoSchema

class ResponseSchema(Schema):
    commune = fields.Nested(CommuneSchema)
    indice_atmo = fields.Nested(IndiceATMO)
    raep = fields.Nested(IndiceRAEP)
    potentiel_radon = fields.Nested(FullPotentielRadonSchema)
    episodes_pollution = fields.Nested(EpisodePollutionSchema)
    vigilance_meteo = fields.Nested(VigilanceMeteoSchema)

class QuerySchema(Schema):
    insee = fields.String()
    date = fields.Date()
    time = fields.Time()
    show_raep = fields.Boolean(description='If this argument is set to truthy value, the licence is now set to private, you can not share the data with users anymore')