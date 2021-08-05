from marshmallow import fields, Schema

class ValiditySchema(Schema):
    start = fields.DateTime()
    end = fields.DateTime()
    area = fields.String()