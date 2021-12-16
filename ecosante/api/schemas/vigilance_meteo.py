from ecosante.recommandations.models import Recommandation
from .indice import FullIndiceSchema, IndiceSchema, ValiditySchema, AdviceSchema
from marshmallow import fields, pre_dump, Schema
from indice_pollution.history.models.vigilance_meteo import VigilanceMeteo
from ecosante.utils.funcs import oxford_comma

class VigilanceValiditySchema(ValiditySchema):
    start = fields.DateTime(attribute='lower')
    end = fields.DateTime(attribute='upper')

class NestedIndiceSchema(Schema):
    label = fields.String(attribute='phenomene')
    color = fields.String(attribute='couleur')
    validity = fields.Nested(VigilanceValiditySchema)
    advice = fields.Nested(AdviceSchema)

    @pre_dump
    def add_advice(self, data: VigilanceMeteo, *a, **kw):
        r = {"phenomene": data.phenomene, "couleur": data.couleur, "validity": data.validity}
        try:
            r['advice'] = next(filter(
                lambda r: r.is_relevant(types=["vigilance_meteo"], media="dashboard", vigilances=[data]),
                Recommandation.published_query().all()
            ))
        except StopIteration:
            r['advice'] = None
        return r

class IndiceDetailsSchema(Schema):
    label = fields.String()
    indice = fields.Nested(NestedIndiceSchema)

    @pre_dump
    def dict_to_dicts(self, data, *a, **kw):
        return {"indice": data}

class IndiceSchema(Schema):
    details = fields.List(fields.Nested(IndiceDetailsSchema))
    label = fields.String()
    color = fields.String()

    @pre_dump
    def dict_to_dicts(self, data, *a, **kw):
        max_couleur = max([v.couleur_id for v in data['details']]) if data['details'] else 1
        data['color'] = VigilanceMeteo.couleurs.get(max_couleur)
        data['label'] = self.make_label(max_couleur, data['details'])
        return data

    @classmethod
    def make_label(cls, max_couleur, vigilances):
        if not vigilances:
            return ""
        if max_couleur == 1:
            label = "Pas d’alerte"
        else:
            couleur = VigilanceMeteo.couleurs.get(max_couleur)
            if couleur:
                couleur = couleur.lower()
            label = f"Alerte {couleur} {oxford_comma([v.phenomene.lower() for v in vigilances if v.couleur_id == max_couleur])}"
        return label

class VigilanceMeteoSchema(FullIndiceSchema):
    indice = fields.Nested(IndiceSchema)
