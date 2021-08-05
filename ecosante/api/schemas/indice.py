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
    main = fields.String()
    details = fields.String()

class IndiceSchema(NestedIndiceSchema):
    details = fields.List(fields.Nested(IndiceDetailsSchema))

class FullIndiceSchema(Schema):
    indice = fields.Nested(IndiceSchema)
    advice = fields.Nested(AdviceSchema)
    validity = fields.Nested(ValiditySchema)
    sources = fields.List(fields.Nested(SourceSchema))