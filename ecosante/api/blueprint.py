from datetime import date
import json
from indice_pollution.history.models.commune import Commune
from indice_pollution.history.models.episode_pollution import EpisodePollution
from sqlalchemy.orm import joinedload
from ecosante.extensions import rebar, db
from .schemas import ResponseSchema, QuerySchema
from indice_pollution import forecast, raep, episodes as get_episodes
from indice_pollution.history.models import PotentielRadon, IndiceATMO, VigilanceMeteo, vigilance_meteo
from ecosante.recommandations.models import Recommandation
from flask.wrappers import Response
from flask import stream_with_context
from flask_rebar import SwaggerV2Generator


registry = rebar.create_handler_registry(
    prefix='/v1',
    swagger_generator=SwaggerV2Generator(
            title="API recosante.beta.gouv.fr",
            description='Toutes les données sont diffusées sous la licence <a href="https://opendatacommons.org/licenses/odbl/1-0/">ODbL v1.0</a>'
    )
)

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
    date_ = rebar.validated_args.get('date')
    time_ = rebar.validated_args.get('time')
    show_raep = rebar.validated_args.get('show_raep')

    commune = Commune.get(insee)

    indice_atmo  = forecast(insee, date_=date_, use_make_resp=False)
    indice_raep = raep(insee, date_=date_) if show_raep else None
    potentiel_radon = PotentielRadon.get(insee)
    episodes = get_episodes(insee, date_=date_, use_make_resp=False)
    vigilance_meteo = VigilanceMeteo.get(insee=insee, date_=date_, time_=time_)

    advice_atmo = get_advice(advices, "indice_atmo", qualif=indice_atmo.indice) if indice_atmo and not hasattr(indice_atmo, "error") else None
    advice_raep = get_advice(advices, "pollens", raep=int(indice_raep["data"]["total"])) if indice_raep and indice_raep.get('data') else None
    advice_radon = get_advice(advices, "radon", potentiel_radon=potentiel_radon.classe_potentiel)
    advice_episode = get_advice(advices, "episode_pollution", polluants=[e.lib_pol_normalized for e in EpisodePollution.filter_etat_haut(episodes)])

    resp =  {
        "commune": commune,
        "indice_atmo": {
            "indice": indice_atmo,
            "advice": advice_atmo
        },
        "potentiel_radon": {
            "indice": potentiel_radon,
            "advice": advice_radon,
            "sources": [{
                "label": "Institut de radioprotection et de sûreté nucléaire (IRSN)",
                "url": "https://www.irsn.fr/FR/connaissances/Environnement/expertises-radioactivite-naturelle/radon/Pages/5-cartographie-potentiel-radon-commune.aspx#.YUyf32aA6dY"
            }],
            "validity": {
                "area": commune.nom
            }
        },
        "episodes_pollution": {
            "indice": episodes,
            "advice": advice_episode
        },
        "vigilance_meteo": {
            "indice": {
                "details": vigilance_meteo,
            },
            "sources": [{
                "label": "Météo France",
                "url": "https://donneespubliques.meteofrance.fr/?fond=produit&id_produit=299&id_rubrique=50"
            }],
            "validity": {
                "area": commune.departement_nom
            }
        }
    }
    if show_raep:
        resp['raep'] = {
            "indice": indice_raep,
            "advice": advice_raep,
            "sources": [{
                "label": "Le Réseau national de surveillance aérobiologique (RNSA)",
                "url": "https://www.pollens.fr/"
            }]
        }
    return resp


@registry.handles(
	rule='/_batch',
    method='GET',
    query_string_schema=QuerySchema(),
)
def batch():
    date_ = rebar.validated_args.get('date', date.today())

    def iter():
        indices = IndiceATMO.get_all_query(
                date_
            ).options(joinedload(IndiceATMO.zone)
            ).yield_per(100)
        schema = ResponseSchema()
        all_episodes = EpisodePollution.get_all(date_)
        yield "["
        first = True
        for commune_id, indice in indices:
            if not first:
                yield ","
            commune = Commune.get_from_id(commune_id)
            indice.region = commune.departement.region
            indice.commune = commune
            episodes = all_episodes.get(commune.zone_pollution_id)
            if episodes:
                for e in episodes:
                    e.commune = commune
            value = {
                "commune": commune,
                "indice_atmo": {
                    "indice": indice
                },
                "episodes_pollution": {
                    "indice": episodes or []
                }
            }
            r = schema.dump(value)
            yield json.dumps(r)
            first = False
        yield ']'
    return Response(stream_with_context(iter()))