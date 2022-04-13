from marshmallow import fields, Schema, pre_dump
from indice_pollution.history.models import Zone, Commune

class AreaDetails(Schema):
    label = fields.String()
    type = fields.String()
    charniere = fields.String()
    code = fields.String()

class ValiditySchema(Schema):
    start = fields.DateTime()
    end = fields.DateTime()
    area = fields.String()
    area_details = fields.Nested(AreaDetails)

    @pre_dump
    def load_area_details(self, data, many, **kwargs):
        area_details = data.get('area_details')
        if isinstance(area_details, Zone):
            data['area_details'] = {
                "type": area_details.type,
                "code": area_details.code,
                "label": area_details.attached_obj.nom,
                "charniere": area_details.attached_obj.charniere if hasattr(area_details.attached_obj, "charniere") else None
            }
        elif isinstance(area_details, Commune):
            data['area_details'] = {
                "type": "commune",
                "code": area_details.insee,
                "label": area_details.nom,
                "charniere": area_details.charniere
            }
        return data