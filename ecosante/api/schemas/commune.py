from marshmallow import fields, Schema

class DepartementSchema(Schema):
    code = fields.String()
    nom = fields.String()

class CommuneSchema(Schema):
    code = fields.String()
    nom = fields.String(dump_only=True, allow_none=True)
    codes_postaux = fields.List(fields.String(), dump_only=True, allow_none=True)
    departement = fields.Nested(DepartementSchema, dump_only=True, allow_none=True)

    @post_load
    def load_commune(self, data, **kwargs):
        return db.session.query(CommuneModel).filter_by(insee=data['code']).first()
