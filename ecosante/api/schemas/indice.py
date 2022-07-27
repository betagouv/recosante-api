from marshmallow import fields, Schema
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
    main = fields.Function(lambda recommandation, context:recommandation.format(context.get('commune')))
    details = fields.String(attribute='precisions_sanitized')

class IndiceSchema(NestedIndiceSchema):
    details = fields.List(fields.Nested(IndiceDetailsSchema))

class FullIndiceSchema(Schema):
    indice = fields.Nested(IndiceSchema)
    advice = fields.Nested(AdviceSchema, allow_none=True)
    validity = fields.Nested(ValiditySchema)
    sources = fields.List(fields.Nested(SourceSchema))
    error = fields.String()