from marshmallow import Schema, ValidationError, post_load, pre_dump, validates
from marshmallow.decorators import pre_load, validates_schema
from marshmallow.validate import OneOf
from marshmallow.fields import Boolean, Str, List, Nested, Email 
import requests
from flask_rebar import ResponseSchema, RequestSchema
from ecosante.inscription.models import Inscription
from ecosante.utils.custom_fields import TempList
from ecosante.api.schemas.commune import CommuneSchema
from indice_pollution.history.models import Commune as CommuneModel

class User(Schema):
    commune = Nested(CommuneSchema, required=False, exclude=('departement', ), allow_none=True)
    uid = Str(dump_only=True)
    diffusion = TempList(Str(validate=OneOf(["mail"])), allow_none=True, required=False)
    mail = Email(required=True)
    frequence = TempList(Str(validate=OneOf(["quotidien", "pollution"])), required=False, allow_none=True)
    deplacement = List(Str(validate=OneOf(["velo", "tec", "sport", "voiture", "aucun"])), required=False, allow_none=True)
    apa = Boolean(required=False, allow_none=True)
    activites = List(Str(validate=OneOf(["jardinage", "bricolage", "menage", "sport", "aucun"])), required=False, allow_none=True)
    enfants = List(Str(validate=OneOf(["oui", "non", "aucun"])), required=False, allow_none=True)
    chauffage = List(Str(validate=OneOf(["bois", "chaudiere", "appoint", "aucun"])), required=False, allow_none=True)
    animaux_domestiques = List(Str(validate=OneOf(["chat", "chien", "aucun"])), required=False, allow_none=True)
    connaissance_produit = List(Str(validate=OneOf(["medecin", "association", "reseaux_sociaux", "publicite", "ami", "autrement"])), required=False, allow_none=True)
    population = List(Str(validate=OneOf(["pathologie_respiratoire", "allergie_pollens", "aucun"])), required=False, allow_none=True)
    recommandations = List(Str(validate=OneOf(["quotidien", "hebdomadaire"])), required=False, allow_none=True)
    notifications = List(Str(validate=OneOf(["quotidien", "aucun"])), required=False, allow_none=True)

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