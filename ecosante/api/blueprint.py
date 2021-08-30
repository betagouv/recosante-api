from ecosante.extensions import rebar
from .schemas import ResponseSchema, QuerySchema
from indice_pollution import forecast, raep
from indice_pollution.history.models import PotentielRadon
from ecosante.recommandations.models import Recommandation

registry = rebar.create_handler_registry(prefix='/v1')

def get_advice(advices, indice_atmo, indice_raep, type_):
    try:
        return next(filter(
            lambda r: r.is_relevant(None, indice_atmo.indice, [], int(indice_raep["data"]["total"]), indice_atmo.date_ech, "dashboard", [type_]),
            advices
        ))
    except StopIteration:
        return None


@registry.handles(
	rule='/',
    method='GET',
    query_string_schema=QuerySchema(),
    response_body_schema=ResponseSchema()
)
def index():
    advices = Recommandation.published_query().all()
    insee = rebar.validated_args.get('insee')

    indice_atmo  = forecast(insee, use_make_resp=False)
    indice_raep = raep(insee)
    potentiel_radon = PotentielRadon.get(insee)

    advice_atmo = get_advice(advices, indice_atmo, indice_raep, "generale")
    advice_raep = get_advice(advices, indice_atmo, indice_raep, "pollens")
    advice_radon = get_advice(advices, indice_atmo, indice_raep, "radon")

    return {
        "commune": indice_atmo.commune,
        "indice_atmo": {
            "indice": indice_atmo,
            "advice": advice_atmo
        },
        "raep": {
            "indice": indice_raep,
            "advice": advice_raep
        },
        "potentiel_radon": {
            "indice": potentiel_radon,
            "advice": advice_radon
        }
    }