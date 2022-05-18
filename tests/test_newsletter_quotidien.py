from ecosante.inscription.models import Inscription
from ecosante.newsletter.models import Newsletter
from indice_pollution.history.models import Commune, IndiceATMO, VigilanceMeteo
from datetime import date, datetime, timedelta
from psycopg2.extras import DateTimeTZRange
import pytest


@pytest.mark.parametrize(
    "valeur",
    list(range(1, 7))
)
def test_indice(commune: Commune, inscription: Inscription, valeur):
    inscription.indicateurs = ['indice_atmo']
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
    nl = Newsletter(forecast={"data": [indice.dict()]}, inscription=inscription)
    assert nl.show_qa == True


def test_episode_pollution(inscription, episode_soufre):
    inscription.indicateurs = ['episode_pollution']
    nl = Newsletter(episodes=[episode_soufre.dict()], inscription=inscription)
    nl.show_vigilance == True
    nl = Newsletter(episodes=[], inscription=inscription)
    nl.show_vigilance == False

@pytest.mark.parametrize(
    "raep, expected",
    [(0, False)] + [(v, True) for v in range(1, 7)]
)
def test_raep(inscription, raep, expected):
    inscription.indicateurs = ["raep"]
    nl = Newsletter(raep=raep, inscription=inscription)
    assert nl.show_raep == expected

@pytest.mark.parametrize(
    "couleur_id",
    list(range(1, 5))
)
def test_vigilance(inscription, couleur_id):
    inscription.indicateurs = ["vigilance_meteo"]

    v = VigilanceMeteo(
            zone_id=inscription.commune.departement.zone_id,
            phenomene_id=1,
            couleur_id=couleur_id,
            date_export=datetime.now() - timedelta(hours=1),
            validity=DateTimeTZRange(date.today() - timedelta(days=1), date.today() + timedelta(days=1)),
        )
    nl = Newsletter(vigilances={'globale': {'vigilance': v, 'recommandation': None}}, inscription=inscription)
    assert nl.show_vigilance == True
