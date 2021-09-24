from ecosante.extensions import rebar
from .schemas import ResponseSchema, QuerySchema
from indice_pollution import forecast, raep
from indice_pollution.history.models import PotentielRadon
from ecosante.recommandations.models import Recommandation

registry = rebar.create_handler_registry(prefix='/v1')

def get_advice(advices, type_, **kwargs):
    kwargs['types'] = [type_]
    kwargs['media'] = 'dashboard'
    try:
        return next(filter(
            lambda r: r.is_relevant(**kwargs),
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

    advice_atmo = get_advice(advices, "generale", qualif=indice_atmo.indice)
    advice_raep = get_advice(advices, "pollens", raep=int(indice_raep["data"]["total"]))
    advice_radon = get_advice(advices, "radon", potentiel_radon=potentiel_radon.classe_potentiel)

    return {
        "commune": indice_atmo.commune,
        "indice_atmo": {
            "indice": indice_atmo,
            "advice": advice_atmo
        },
        "raep": {
            "indice": indice_raep,
            "advice": advice_raep,
            "sources": [{
                "label": "Le Réseau National de Surveillance Aérobiologique (RNSA)",
                "url": "https://www.pollens.fr/"
            }]
        },
        "potentiel_radon": {
            "indice": potentiel_radon,
            "advice": advice_radon,
            "sources": [{
                "label": " Institut de radioprotection et de sûreté nucléaire (IRSN)",
                "url": "https://www.irsn.fr/FR/connaissances/Environnement/expertises-radioactivite-naturelle/radon/Pages/5-cartographie-potentiel-radon-commune.aspx#.YUyf32aA6dY"
            }],
            "valididy": {
                "area": indice_atmo.commune.nom
            }
        }
    }