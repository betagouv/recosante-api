from re import I
from ecosante.extensions import rebar
from .schemas import ResponseSchema, QuerySchema
from indice_pollution import forecast, raep
from indice_pollution.history.models import PotentielRadon, potentiel_radon

registry = rebar.create_handler_registry(prefix='/v1')

@registry.handles(
	rule='/',
    method='GET',
    query_string_schema=QuerySchema(),
    response_body_schema=ResponseSchema()
)
def index():
    insee = rebar.validated_args.get('insee')
    indice_atmo  = forecast(insee, use_make_resp=False)
    indice_raep = raep(insee)
    potentiel_radon = PotentielRadon.get(insee)

    return {
        "commune": indice_atmo.commune,
        "indice_atmo": indice_atmo,
        "raep": indice_raep,
        "potentiel_radon": potentiel_radon
    }