from marshmallow import Schema, ValidationError, post_load, pre_dump, validates
from marshmallow.decorators import pre_load, validates_schema
from marshmallow.validate import OneOf, Length
from marshmallow.fields import Boolean, Str, List, Nested, Email
from flask_rebar import ResponseSchema, RequestSchema
from ecosante.inscription.models import Inscription
from ecosante.utils.custom_fields import TempList
from ecosante.api.schemas.commune import CommuneSchema
from indice_pollution.history.models import Commune as CommuneModel


def list_str(choices, max_length=None, temp=False, **kwargs):
    t = TempList if temp else List
    return t(
        Str(validate=OneOf(choices=choices)),
        required=False,
        allow_none=True,
        validate=Length(min=0, max=max_length) if max_length else None,
        **kwargs
    )

class User(Schema):
    commune = Nested(CommuneSchema, required=False, allow_none=True)
    uid = Str(dump_only=True)
    mail = Email(required=True)
    deplacement = list_str(["velo", "tec", "voiture", "aucun"])
    activites = list_str(["jardinage", "bricolage", "menage", "sport", "aucun"])
    enfants = list_str(["oui", "non", "aucun"], temp=True)
    chauffage = list_str(["bois", "chaudiere", "appoint", "aucun"])
    animaux_domestiques = list_str(["chat", "chien", "aucun"])
    connaissance_produit = list_str(["medecin", "association", "reseaux_sociaux", "publicite", "ami", "autrement"])
    population = list_str(["pathologie_respiratoire", "allergie_pollens", "aucun"])
    indicateurs = list_str(["indice_atmo", "raep", "indice_uv", "vigilance_meteorologique"])
    indicateurs_frequence = list_str(["quotidien", "hebdomadaire", "alerte"], 1)
    indicateurs_media = list_str(["mail", "notifications_web"])
    recommandations = list_str(["oui", "non"], 1, attribute='recommandations_actives')
    recommandations_frequence = list_str(["quotidien", "hebdomadaire", "pollution"], 1)
    recommandations_media = list_str(["mail", "notifications_web"])
    webpush_subscription_info = Str(required=False, allow_none=True)


class Response(User, ResponseSchema):
    pass
    

class Request(User, RequestSchema):
    @post_load
    def make_inscription(self, data, **kwargs):
        inscription = Inscription.query.filter_by(mail=data['mail']).first()
        if inscription:
            for k, v in data.items():
                setattr(inscription, k, v)
        else:
            inscription = Inscription(**data)
        return inscription