from dataclasses import field
from marshmallow import Schema, ValidationError, post_load, schema
from marshmallow.validate import OneOf, Length
from marshmallow.fields import Bool, Str, List, Nested, Email
from flask_rebar import ResponseSchema, RequestSchema, errors
from ecosante.inscription.models import Inscription
from ecosante.utils.custom_fields import TempList
from ecosante.api.schemas.commune import CommuneSchema
from ecosante.extensions import celery
from indice_pollution.history.models import Commune as CommuneModel
from flask import request


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
    connaissance_produit = list_str(["medecin", "association", "reseaux_sociaux", "publicite", "ami", "pro", "autrement"])
    population = list_str(["pathologie_respiratoire", "allergie_pollens", "aucun"])
    indicateurs = list_str(["indice_atmo", "raep", "indice_uv", "vigilance_meteo"])
    indicateurs_frequence = list_str(["quotidien", "hebdomadaire", "alerte"], 1)
    indicateurs_media = list_str(["mail", "notifications_web"])
    recommandations = list_str(["oui", "non"], 1, attribute='recommandations_actives')
    recommandations_frequence = list_str(["quotidien", "hebdomadaire", "pollution"], 1)
    recommandations_media = list_str(["mail", "notifications_web"])
    webpush_subscriptions_info = Str(required=False, allow_none=True, load_only=True)


class Response(User, ResponseSchema):
    is_active = Bool(attribute='is_active')
    authentication_token = Str(dump_only=True, required=False)
    

class RequestPOST(User, RequestSchema):
    @post_load
    def make_inscription(self, data, **kwargs):
        inscription = Inscription.query.filter(Inscription.mail.ilike(data['mail'])).first()
        if inscription:
            raise ValidationError('mail already used', field_name='mail')
        inscription = Inscription(**data)
        return inscription

class RequestPOSTID(User, RequestSchema):
    def __init__(self, **kwargs):
        super_kwargs = dict(kwargs)
        partial_arg = super_kwargs.pop('partial', ['mail'])
        super(RequestPOSTID, self).__init__(partial=partial_arg, **super_kwargs)


    @post_load
    def make_inscription(self, data, **kwargs):
        uid = request.view_args.get('uid')
        if not uid:
            raise ValidationError('uid is required')
        inscription = Inscription.query.filter_by(uid=uid).first()
        if not inscription:
            raise errors.NotFound('uid unknown')
        if 'mail' in data:
            inscription_same_mail = Inscription.query.filter(
                Inscription.uid != uid,
                Inscription.mail == data['mail']
            ).first()
            if inscription_same_mail:
                raise errors.Conflict('user with this mail already exists')
        for k, v in data.items():
            setattr(inscription, k, v) 
        return inscription

class RequestUpdateProfile(Schema):
    mail = Email(required=True)