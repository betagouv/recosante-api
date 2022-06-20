from .indice import FullIndiceSchema, IndiceSchema
from marshmallow import fields, pre_dump
from datetime import datetime, timedelta

class IndiceUv(IndiceSchema):
    value = fields.Integer(attribute='uv_j0')

class FullIndiceUv(FullIndiceSchema):
    indice = fields.Nested(IndiceUv)
    
    @pre_dump
    def add_validity_dates(self, data, many, **kwargs):
        if data["indice"] is None:
            resp = {}
        else: 
            resp = data
            dt = datetime.combine(data["indice"].date, datetime.min.time())
            resp['validity'] = {
                "start": dt,
                "end": dt + timedelta(1) - timedelta(seconds=1),
                "area": data["validity"]["area"],
                "area_details": data["validity"]["area_details"]
            }
        return resp