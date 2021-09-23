from marshmallow import fields, Schema

class DepartementSchema(Schema):
    code = fields.String()
    nom = fields.String()

class CommuneSchema(Schema):
    code = fields.String()
    nom = fields.String()
    codesPostaux = fields.List(fields.String(), attribute='codes_postaux')
    departement = fields.Nested(DepartementSchema)

