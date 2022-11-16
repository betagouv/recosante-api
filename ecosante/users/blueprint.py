from flask.globals import request
from ecosante.extensions import rebar, db, admin_authenticator
from .schemas import RequestPOST, Response, RequestPOSTID, RequestUpdateProfile
from ecosante.inscription.models import Inscription
from ecosante.extensions import celery, authenticator

registry = rebar.create_handler_registry('/users/')

@registry.handles(
    rule='/_search',
    hidden=True,
    response_body_schema={200:Response(many=True)},
    authenticators=[admin_authenticator]
)
@admin_authenticator.route
def search_users():
    mail = request.args.get('mail')
    return Inscription.active_query()\
        .filter(Inscription.mail.ilike(f'%{mail}%'))\
        .order_by(Inscription.mail)\
        .limit(10)

@registry.handles(
    rule='/',
    method='POST',
    request_body_schema=RequestPOST(),
    response_body_schema={
        201: Response()
    },
    authenticators=[admin_authenticator],
)
def post_users():
    inscription = rebar.validated_body
    db.session.add(inscription)
    db.session.commit()
    celery.send_task(
        "ecosante.inscription.tasks.send_success_email.send_success_email",
        (inscription.id, True),
        queue='send_email',
        routing_key='send_email.subscribe'
    )
    inscription.authentication_token = authenticator.make_token(uid=inscription.uid)
    return inscription, 201


@registry.handles(
    rule='/<uid>',
    method='GET',
    response_body_schema={200: Response()},
    authenticators=[authenticator, admin_authenticator]
)
def get_user(uid):
    inscription = Inscription.query.filter_by(uid=uid).first()
    return inscription, 200


@registry.handles(
    rule='/<uid>',
    method='POST',
    response_body_schema={200: Response()},
    request_body_schema=RequestPOSTID(),
    authenticators=[authenticator]
)
def post_user_id(uid):
    inscription = rebar.validated_body
    db.session.add(inscription)
    db.session.commit()
    return inscription, 200


@registry.handles(
    rule='/_send_update_profile',
    method='POST',
    request_body_schema=RequestUpdateProfile()
)
def send_update_profile():
    r = rebar.validated_body
    inscription = Inscription.query.filter_by(mail=r['mail']).first()
    if not inscription:
        return {}, 404
    celery.send_task(
        "ecosante.inscription.tasks.send_update_profile.send_update_profile",
        (inscription.id,),
        queue='send_email',
        routing_key='send_email.subscribe'
    )
    return 'ok', 200

@registry.handles(
    rule='/<uid>/_deactivate',
    method='POST',
    response_body_schema={200: Response()},
    authenticators=[authenticator]
)
def deactivate(uid):
    inscription = Inscription.query.filter_by(uid=uid).first()
    if not inscription:
        return 'error', 404
    inscription.unsubscribe()
    return inscription, 200

@registry.handles(
    rule='/<uid>/_reactivate',
    method='POST',
    response_body_schema={200: Response()},
    authenticators=[authenticator]
)
def reactivate(uid):
    inscription = Inscription.query.filter_by(uid=uid).first()
    if not inscription:
        return 'error', 404
    inscription.deactivation_date = None
    db.session.add(inscription)
    db.session.commit()
    return inscription, 200
