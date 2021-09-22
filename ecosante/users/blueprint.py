from ecosante.extensions import rebar, db
from .schemas import Request, Response

registry = rebar.create_handler_registry('/users/')

@registry.handles(
    rule='/',
    method='POST',
    request_body_schema=Request(),
    response_body_schema={
        201: Response()
    }
)
def post_users():
    inscription = rebar.validated_body
    db.session.add(inscription)
    return inscription, 201
