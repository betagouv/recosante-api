from csv import DictWriter
import json, os, io
from datetime import date
from indice_pollution.history.models.commune import Commune
from indice_pollution.history.models.episode_pollution import EpisodePollution
from sqlalchemy.orm import joinedload
from ecosante.extensions import rebar, cache
from .schemas import ResponseSchema, QuerySchema, BaignadesQuerySchema, RecommandationSchema, RecommandationExportSchema
from .baignades import make_baignades_response
from indice_pollution import forecast, raep, episodes as get_episodes
from indice_pollution.history.models import PotentielRadon, IndiceATMO, VigilanceMeteo, IndiceUv
from ecosante.recommandations.models import Recommandation
from flask.wrappers import Response
from flask import current_app, stream_with_context, redirect, url_for
from flask_rebar import SwaggerV3Generator
from ecosante.recommandations.models import Recommandation

registry = rebar.create_handler_registry(
    prefix='/v1',
    swagger_generator=SwaggerV3Generator(
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
    show_indice_uv = rebar.validated_args.get('show_indice_uv')

    commune = Commune.get(insee)

    indice_atmo  = forecast(insee, date_=date_, use_make_resp=False)
    indice_raep = raep(insee, date_=date_, departement_as_dict=False) if show_raep else None
    potentiel_radon = PotentielRadon.get(insee)
    episodes = get_episodes(insee, date_=date_, use_make_resp=False)
    vigilance_meteo = VigilanceMeteo.get(insee=insee, date_=date_, time_=time_)
    indice_uv = IndiceUv.get(insee=insee, date_=date_) if show_indice_uv else None

    advice_atmo = get_advice(advices, "indice_atmo", qualif=indice_atmo.indice) if indice_atmo and not hasattr(indice_atmo, "error") else None
    advice_raep = get_advice(advices, "pollens", raep=int(indice_raep["data"]["total"])) if indice_raep and indice_raep.get('data') else None
    advice_radon = get_advice(advices, "radon", potentiel_radon=potentiel_radon.classe_potentiel if potentiel_radon else None)
    advice_episode = get_advice(advices, "episode_pollution", polluants=[e.lib_pol_normalized for e in EpisodePollution.filter_etat_haut(episodes)])
    advice_indice_uv = get_advice(advices, "indice_uv", indice_uv=indice_uv.uv_j0) if indice_uv and indice_uv.uv_j0 is not None else None

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
                "area": commune.zone.lib,
                "area_details": commune.zone
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
                "area": commune.departement.zone.lib,
                "area_details": commune.departement.zone
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
    if show_indice_uv:
        resp['indice_uv'] = {
            "indice": indice_uv,
            "advice": advice_indice_uv,
            "sources": [{
                "label": "Météo France",
                "url": "https://meteofrance.com/comprendre-la-meteo/atmosphere/les-ultraviolets"
            }],
            "validity": {
                "area": commune.zone.lib,
                "area_details": commune.zone
            }
        }
    return resp

@registry.handles(
    rule='/baignades',
    method='GET',
    query_string_schema=BaignadesQuerySchema(),
    hidden=True
)
def baignades():
    insee = rebar.validated_args.get('insee')
    cache_key_format = f'baignades-{insee}'
    resp = None
    try:
        resp = cache.get(cache_key_format)
    except Exception as e:
        current_app.logger.error(f"Cache is unavailable: {e}")
    if resp is None:
        # Sans cache
        resp = make_baignades_response(insee)
        try:
            baignades_cache_timeout = os.getenv('BAIGNADES_CACHE_TIMEOUT', 86400) # seconds
            cache.set(cache_key_format, resp, timeout=baignades_cache_timeout)
        except Exception as e:
            current_app.logger.error(f"Cache is unavailable: {e}")
    else:
        # Avec cache
        current_app.logger.info("Cached version")
    # Ajout des recommandations baignades
    advices = Recommandation.published_query().all()
    advice_baignades = get_advice(advices, "baignades")
    advice_baignades_dict = None
    if advice_baignades is not None:
        advice_baignades_dict = {
            "details": advice_baignades.precisions_sanitized,
            "main": advice_baignades.recommandation_sanitized
        }
    resp['baignades']['advice'] = advice_baignades_dict
    return resp

@registry.handles(
    rule='/recommandations.json',
    method='GET',
    response_body_schema=RecommandationExportSchema(many=True)
)
def recommandations():
    return Recommandation.published_query().all()

@current_app.route('/v1/recommandations')
def reco_redirect():
    return redirect(url_for('v1.recommandations'))

@current_app.route('/v1/recommandations.csv')
def recommandations_csv():
    recommandations = RecommandationExportSchema(
        many=True
    ).dump(
        Recommandation.published_query().all()
    )
    output = io.StringIO()
    csv_writer = DictWriter(
        output,
        list(RecommandationExportSchema._declared_fields.keys()),
    )
    csv_writer.writeheader()
    csv_writer.writerows(recommandations)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=recommandations.csv"
        }
    )

@registry.handles(
    rule='/_batch',
    method='GET',
    query_string_schema=QuerySchema(),
    hidden=True
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