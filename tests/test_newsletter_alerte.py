from bisect import insort_right
from cmath import exp
import pytest
from datetime import date, datetime, timedelta
from psycopg2.extras import DateTimeTZRange
from indice_pollution.history.models import IndiceATMO, IndiceUv, VigilanceMeteo
from ecosante.newsletter.models.newsletter import Newsletter


@pytest.mark.parametrize(
    "valeur,expected",
    [(v, False) for v in range(0, 3)] + [(v, True) for v in range(3, 7)]
)
def test_indice_atmo(inscription_alerte, commune, valeur, expected):
    inscription_alerte.indicateurs = ['indice_atmo']
    indice = IndiceATMO(
        zone_id=commune.zone_id,
        date_ech=datetime.today(),
        date_dif=datetime.today(),
        no2=valeur,
        so2=valeur,
        o3=valeur,
        pm10=valeur,
        pm25=valeur,
        valeur=valeur,
    )
    nl = Newsletter(forecast={"data": [indice.dict()]}, inscription=inscription_alerte, type_="")
    assert nl.show_qa == expected
    if expected:
        assert nl.to_send('quotidien', False) == True
        nl = Newsletter(forecast={"data": []}, inscription=inscription_alerte, type_="")
        assert nl.to_send('quotidien', False) == False

def test_episode_pollution(inscription_alerte, episode_soufre):
    inscription_alerte.indicateurs = ['episode_pollution']
    nl = Newsletter(episodes=[episode_soufre.dict()], inscription=inscription_alerte)
    nl.show_vigilance == True
    nl = Newsletter(episodes=[], inscription=inscription_alerte)
    nl.show_vigilance == False

@pytest.mark.parametrize(
    "raep, expected",
    [(0, False)] + [(v, True) for v in range(1, 7)]
)
def test_raep(inscription_alerte, raep, expected):
    inscription_alerte.indicateurs = ["raep"]
    nl = Newsletter(raep=raep, inscription=inscription_alerte)
    assert nl.show_raep == expected
    if expected:
        assert nl.to_send('quotidien', False) == True
        nl = Newsletter(raep=None, inscription=inscription_alerte)
        assert nl.to_send('quotidien', False) == False

@pytest.mark.parametrize(
    "couleur_id, expected",
    [(1, False), (2, False), (3, True), (4, True)]
)
def test_vigilance(inscription_alerte, couleur_id, expected):
    inscription_alerte.indicateurs = ["vigilance_meteo"]

    v = VigilanceMeteo(
            zone_id=inscription_alerte.commune.departement.zone_id,
            phenomene_id=1,
            couleur_id=couleur_id,
            date_export=datetime.now() - timedelta(hours=1),
            validity=DateTimeTZRange(date.today() - timedelta(days=1), date.today() + timedelta(days=1)),
        )
    nl = Newsletter(vigilances={'globale': {'vigilance': v, 'recommandation': None}}, inscription=inscription_alerte)
    assert nl.show_vigilance == expected
    if expected:
        assert nl.to_send('quotidien', False) == True
        nl = Newsletter(vigilances={'globale': {'vigilance': None, 'recommandation': None}}, inscription=inscription_alerte)
        assert nl.to_send('quotidien', False) == False

@pytest.mark.parametrize(
    "valeur,enfants,expected",
    [
        # Pas d’enfant
        *[(v, False, False) for v in range(0, 6)], # Pas envoyé pour les valeurs < 6
        *[(v, False, True) for v in range(6, 9)], # Envoyé pour les valeurs >= 6
        # Avec enfant
        *[(v, True, False) for v in range(0, 3)], # Pas envoyé pour les valeurs < 3
        *[(v, True, True) for v in range(3, 8)], # Envoyé pour les valeurs >= 3
    ]
)
def test_indice_uv(inscription_alerte, valeur, enfants, expected):
    inscription_alerte.indicateurs = ["indice_uv"]
    inscription_alerte.enfants = "oui" if enfants else "non"
    indice_uv = IndiceUv(
        zone_id=inscription_alerte.commune.zone_id,
        date=date.today(),
        uv_j0=valeur,
    )
    nl = Newsletter(indice_uv=indice_uv, inscription=inscription_alerte)
    assert nl.show_indice_uv == expected