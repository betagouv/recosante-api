from marshmallow import fields, Schema

class SourceSchema(Schema):
    label = fields.String()
    url = fields.URL()