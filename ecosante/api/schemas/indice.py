from attr import attrib
from marshmallow import fields, Schema, pre_dump

from ecosante.recommandations.models import Recommandation
from .validity import ValiditySchema
from .source import SourceSchema

class NestedIndiceSchema(Schema):
    value = fields.Integer()
    label = fields.String()
    color = fields.String()

class IndiceDetailsSchema(Schema):
    label = fields.String()
    indice = fields.Nested(NestedIndiceSchema)

class AdviceSchema(Schema):
    main = fields.Function(
        lambda recommandation, context: recommandation.format(context.get('commune'))
    )
    details = fields.String(attribute='precisions_sanitized')

class RecommandationSchema(Schema):
    recommandation = fields.Function(
        lambda recommandation, context: recommandation.format(context.get('commune'))
    )
    type = fields.String(attribute='type_')

class RecommandationExportSchema(RecommandationSchema):
    qa_bonne = fields.Boolean()
    qa_mauvaise = fields.Boolean()
    qa_evenement = fields.Boolean()
    categorie = fields.String()
    ozone = fields.Boolean()
    dioxyde_azote = fields.Boolean()
    dioxyde_soufre = fields.Boolean()
    particules_fines = fields.Boolean()
    min_raep = fields.Integer()
    vigilance_couleur_ids = fields.List(fields.Integer())
    vigilance_phenomene_ids = fields.List(fields.Integer())
    min_indice_uv = fields.Integer()

    @pre_dump
    def filter_attributes(self, data, many, **kwargs):
        attributes_per_type = {
            "episode_pollution": ["ozone", "dioxyde_azote", "dioxyde_soufre", "particules_fines",],
            "indice_atmo": ["qa_bonne", "qa_mauvaise", "qa_evenement", "categorie",],
            "pollens": ["min_raep", "qa_bonne", "qa_mauvaise", "qa_evenement", "categorie"],
            "vigilance_meteo": ["vigilance_couleur_ids", "vigilance_phenomene_ids"],
            "indice_uv": ["min_indice_uv"],
            "radon": [],
            "baignades": []
        }
        return Recommandation(
            **{attribute: getattr(data, attribute) for attribute in attributes_per_type[data.type_] + ["type_", "recommandation"]}
        )

class IndiceSchema(NestedIndiceSchema):
    details = fields.List(fields.Nested(IndiceDetailsSchema))

class FullIndiceSchema(Schema):
    indice = fields.Nested(IndiceSchema)
    advice = fields.Nested(AdviceSchema, allow_none=True)
    validity = fields.Nested(ValiditySchema)
    sources = fields.List(fields.Nested(SourceSchema))
    error = fields.String()