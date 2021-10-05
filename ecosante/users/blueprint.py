from ecosante.extensions import rebar, db
from .schemas import RequestPOST, Response, RequestPOSTID
from ecosante.inscription.models import Inscription
import os

registry = rebar.create_handler_registry('/users/')

@registry.handles(
    rule='/',
    method='POST',
    request_body_schema=RequestPOST(),
    response_body_schema={
        201: Response()
    }
)
def post_users():
    inscription = rebar.validated_body
    db.session.add(inscription)
    db.session.commit()
    return inscription, 201

@registry.handles(
    rule='/<uid>',
    method='GET',
    response_body_schema={200: Response()}
)
def get_user(uid):
    inscription = Inscription.query.filter_by(uid=uid).first()
    return inscription, 200


@registry.handles(
    rule='/<uid>',
    method='POST',
    response_body_schema={200: Response()},
    request_body_schema=RequestPOSTID(),
)
def post_user_id(uid):
    inscription = rebar.validated_body
    db.session.add(inscription)
    db.session.commit()
    return inscription, 200

@registry.handles(rule='/_vapid_public_key', method='GET')
def vapid_public_key():
    APPLICATION_SERVER_KEY = os.getenv('APPLICATION_SERVER_KEY')
    return {"public_key": APPLICATION_SERVER_KEY}