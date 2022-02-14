from ecosante.newsletter.models import Inscription, Newsletter, NewsletterDB, Recommandation
from datetime import date, datetime, timedelta
from .utils import published_recommandation
import os, pytest
from itertools import product
from indice_pollution.history.models import VigilanceMeteo
from psycopg2.extras import DateTimeTZRange

def test_episode_passe(db_session, inscription):
    yesterday = date.today() - timedelta(days=1)
    recommandations = [
        published_recommandation(particules_fines=True, type_="episode_pollution"),
        published_recommandation(recommandation="ça va en fait", type_="indice_atmo")
    ]
    db_session.add_all(recommandations)
    db_session.commit()
    nl = Newsletter(
        inscription=inscription,
        forecast={"data": []},
        episodes={"data": [{"code_pol": "5", "etat": "INFORMATION ET RECOMMANDATION", "date": str(yesterday)}]},
        recommandations=recommandations,
        raep=1
    )
    nldb = NewsletterDB(nl)
    assert nldb.polluants_formatted == None
    assert nldb.polluants_symbols == []
    assert nldb.lien_recommandations_alerte == None
    assert nldb.attributes()['POLLUANT'] == ""
    assert nldb.attributes()['RECOMMANDATION'] == '<p>ça va en fait</p>'
    assert nldb.attributes()['DEPARTEMENT'] == 'Mayenne'

def test_formatted_polluants_indice_atmo_pm10(db_session, inscription, episode_pm10):
    recommandations = [published_recommandation(), published_recommandation(particules_fines=True, type_='episode_pollution')]
    db_session.add_all(recommandations)
    db_session.commit()
    nl = Newsletter(
        inscription=inscription,
        forecast={"data": []},
        episodes={"data": [episode_pm10.dict()]},
        recommandations=recommandations
    )
    assert nl.polluants_formatted == "aux particules fines"
    assert nl.polluants_symbols == ['pm10']
    assert nl.lien_recommandations_alerte == 'http://localhost:5000/recommandation-episodes-pollution?population=generale&polluants=pm10'
    assert nl.recommandation_qa.type_ == "indice_atmo"
    assert nl.recommandation_episode.type_ == "episode_pollution"

def test_formatted_polluants_indice_atmo_pm10_no2(db_session, inscription, episode_pm10, episode_azote):
    recommandations = [published_recommandation(particules_fines=True, type_='episode_pollution')]
    db_session.add_all(recommandations)
    db_session.commit()
    nl = Newsletter(
        inscription=inscription,
        forecast={"data": []},
        episodes={"data": [episode_pm10.dict(), episode_azote.dict()]},
        recommandations=recommandations
    )
    assert nl.polluants_formatted == "aux particules fines et au dioxyde d’azote"
    assert nl.polluants_symbols == ['pm10', 'no2']
    assert nl.lien_recommandations_alerte == 'http://localhost:5000/recommandation-episodes-pollution?population=generale&polluants=pm10&polluants=no2'
    assert nl.recommandation.particules_fines == True
    assert nl.recommandation_qa.particules_fines == True

def test_formatted_polluants_indice_atmo_tous(db_session, inscription, episode_soufre, episode_pm10, episode_ozone, episode_azote):
    recommandations = [published_recommandation(particules_fines=True, type_='episode_pollution')]
    db_session.add_all(recommandations)
    db_session.commit()
    nl = Newsletter(
        inscription=inscription,
        forecast={"data": []},
        episodes={"data": [episode_soufre.dict(), episode_pm10.dict(), episode_ozone.dict(), episode_azote.dict()]},
        recommandations=recommandations
    )
    assert nl.polluants_formatted == "au dioxyde de soufre, aux particules fines, à l’ozone, et au dioxyde d’azote"
    assert nl.polluants_symbols == ['so2', 'pm10', 'o3', 'no2']
    assert nl.lien_recommandations_alerte == 'http://localhost:5000/recommandation-episodes-pollution?population=generale&polluants=so2&polluants=pm10&polluants=o3&polluants=no2'

def test_formatted_polluants_indice_atmo_pm10_o3_no2(db_session, inscription, episode_soufre, episode_pm10, episode_ozone, episode_azote):
    recommandations = [published_recommandation(particules_fines=True, type_='episode_pollution')]
    db_session.add_all(recommandations)
    db_session.commit()
    episode_dict = episode_soufre.dict()
    episode_dict['etat'] = 'PAS DE DEPASSEMENT'
    nl = Newsletter(
        inscription=inscription,
        forecast={"data": []},
        episodes={"data": [ episode_dict, episode_pm10.dict(), episode_ozone.dict(), episode_azote.dict()]},
        recommandations=recommandations
    )
    assert nl.polluants_formatted == "aux particules fines, à l’ozone, et au dioxyde d’azote"
    assert nl.polluants_symbols == ['pm10', 'o3', 'no2']
    assert nl.lien_recommandations_alerte == 'http://localhost:5000/recommandation-episodes-pollution?population=generale&polluants=pm10&polluants=o3&polluants=no2'


def test_formatted_polluants_indice_atmo_no2(db_session, inscription, episode_azote):
    recommandations=[
        published_recommandation(particules_fines=True, autres=True, enfants=False, dioxyde_azote=True, type_='episode_pollution'),
        published_recommandation(particules_fines=True, personnes_sensibles=True, dioxyde_azote=True, type_='episode_pollution'),
    ]
    db_session.add_all(recommandations)
    db_session.commit()
    inscription.pathologie_respiratoire = True
    nl = Newsletter(
        inscription=inscription,
        forecast={"data": []},
        episodes={"data": [episode_azote.dict()]},
        recommandations=recommandations
    )
    assert nl.lien_recommandations_alerte == 'http://localhost:5000/recommandation-episodes-pollution?population=vulnerable&polluants=no2'
    assert nl.recommandation.personnes_sensibles == True


def test_avis_oui(db_session, client, inscription, episode_azote):
    recommandations=[
        published_recommandation(particules_fines=True, autres=True, enfants=False, dioxyde_azote=True, type_='episode_pollution'),
        published_recommandation(particules_fines=True, personnes_sensibles=True, dioxyde_azote=True, type_='episode_pollution'),
    ]
    db_session.add_all(recommandations)
    db_session.commit()
    inscription.pathologie_respiratoire = True
    nl = Newsletter(
        inscription=inscription,
        forecast={"data": []},
        episodes={"data": [episode_azote.dict()]},
        recommandations=recommandations
    )
    nldb = NewsletterDB(nl)
    db_session.add(nldb)
    db_session.commit()
    response = client.post(f'/newsletter/{nldb.short_id}/avis?appliquee=oui')
    assert response.status_code == 200
    nldb2 = NewsletterDB.query.get(nldb.id)
    assert nldb2.appliquee == True


def test_avis_non(db_session, client, inscription, episode_azote):
    recommandations=[
        published_recommandation(particules_fines=True, autres=True, enfants=False, dioxyde_azote=True, type_='episode_pollution'),
        published_recommandation(particules_fines=True, personnes_sensibles=True, dioxyde_azote=True, type_='episode_pollution'),
    ]
    db_session.add_all(recommandations)
    db_session.commit()
    inscription.pathologie_respiratoire = True
    nl = Newsletter(
        inscription=inscription,
        forecast={"data": []},
        episodes={"data": [episode_azote.dict()]},
        recommandations=recommandations
    )
    nldb = NewsletterDB(nl)
    db_session.add(nldb)
    db_session.commit()
    avis = "Je ne suis pas concerné !"
    response = client.post(f'/newsletter/{nldb.short_id}/avis?appliquee=non', data={"avis": avis}, headers={"Accept": "application/json"})
    assert response.status_code == 200
    nldb2 = NewsletterDB.query.get(nldb.id)
    assert nldb2.appliquee == False
    assert nldb2.avis == avis

@pytest.mark.parametrize(
    "episodes,raep,allergie_pollens,delta,indice",
    product(
        [[], ["episode_azote"]],
        [0, 2, 6],
        [True, False],
        range(0, 7),
        ["bon", "degrade"]
    )
)
def test_pollens(db_session, inscription, episodes, raep, allergie_pollens, delta, indice, request):
    if len(episodes) > 0:
        episodes = [request.getfixturevalue(episodes[0]).dict()]
    recommandations=[
        published_recommandation(particules_fines=True, autres=True, enfants=False, dioxyde_azote=True, type_='episode_pollution'),
        published_recommandation(particules_fines=True, personnes_sensibles=True, dioxyde_azote=True, type_='episode_pollution'),
        published_recommandation(type_="pollens", min_raep=raep),
        published_recommandation()
    ]
    db_session.add_all(recommandations)
    db_session.commit()
    date_ = date.today() + timedelta(days=delta)
    if delta == 0:
        episode = episodes
    else:
        episode = []
    if allergie_pollens:
        inscription.indicateurs = ['raep']
    else:
        inscription.indicateurs = ['indice_atmo']
    nl = Newsletter(
        inscription=inscription,
        forecast={"data": [{"date": date_, "indice": indice}]},
        episodes={"data": episode},
        raep=raep,
        date=date_,
        recommandations=recommandations
    )

    if episode:
        assert nl.show_raep == False
    else:
        if not allergie_pollens:
            assert nl.show_raep == False
        elif raep == 0:
            assert nl.show_raep == False
        elif 0 < raep < 4:
            if allergie_pollens:
                assert nl.show_raep == True
                assert (nl.recommandation.type_ == "pollens") == (date_.weekday() in [2, 5])
            else:
                assert nl.show_raep == False
                assert nl.recommandation.type_ != "pollens"
        else:
            if allergie_pollens:
                assert nl.show_raep == True
                assert (nl.recommandation.type_ == "pollens") == (date_.weekday() in [2, 5])
            else:
                assert nl.show_raep == True
                assert nl.recommandation.type_ != "pollens"
    inscription.allergie_pollens = allergie_pollens
    inscription.indicateurs = []
    nl = Newsletter(
        inscription=inscription,
        forecast={"data": [{"date": date_, "indice": indice}]},
        episodes={"data": episode},
        raep=raep,
        date=date_,
        recommandations=recommandations
    )
    assert nl.show_raep == False

def test_show_qa(inscription):
    inscription.indicateurs = ['indice_atmo']
    nl = Newsletter(
        inscription=inscription,
        forecast={"data": []},
        episodes={"data": []},
        raep=0,
        recommandations=[]
    )
    assert nl.show_qa == True

    inscription.indicateurs = []
    nl = Newsletter(
        inscription=inscription,
        forecast={"data": []},
        episodes={"data": []},
        raep=0,
        recommandations=[]
    )
    assert nl.show_qa == False

def test_show_radon_polluants(db_session, inscription, episode_pm10):
    nl = Newsletter(
        inscription=inscription,
        forecast={"data": []},
        episodes={"data": [episode_pm10.dict()]},
        raep=0,
        recommandations=[]
    )

    assert nl.show_radon == False


def test_show_radon_raep(db_session, inscription):
    today_date = date.today()
    inscription.id = 1
    inscription.indicateurs = ["indice_atmo", "raep"]
    nl = Newsletter(
        inscription=inscription,
        forecast={"data": [{"date": str(today_date), "indice": "bon"}]},
        episodes={"data": []},
        raep=0,
        recommandations=[]
    )
    assert nl.show_radon == True

    nl = Newsletter(
        inscription=inscription,
        forecast={"data": [{"date": str(today_date), "indice": "bon"}]},
        episodes={"data": []},
        raep=4,
        recommandations=[]
    )
    assert nl.show_radon == False

    inscription.indicateurs = ["indice_atmo"]
    nl = Newsletter(
        inscription=inscription,
        forecast={"data": [{"date": str(today_date), "indice": "bon"}]},
        episodes={"data": []},
        raep=1,
        recommandations=[]
    )
    assert nl.show_radon == True

    nl = Newsletter(
        inscription=inscription,
        forecast={"data": [{"date": str(today_date), "indice": "bon"}]},
        episodes={"data": []},
        raep=4,
        recommandations=[]
    )
    assert nl.show_radon == False


def test_show_radon_indice(inscription):
    today_date = date.today()
    inscription.allergie_pollens = False
    nl = Newsletter(
        inscription=inscription,
        forecast={"data": [{"date": str(today_date), "indice": "bon"}]},
        episodes={"data": []},
        raep=0,
        recommandations=[]
    )
    assert nl.show_radon == True

    nl = Newsletter(
        inscription=inscription,
        forecast={"data": [{"date": str(today_date), "indice": "moyen"}]},
        episodes={"data": []},
        raep=0,
        recommandations=[]
    )
    assert nl.show_radon == True

    today_date = date.today()
    nl = Newsletter(
        inscription=inscription,
        forecast={"data": [{"date": str(today_date), "indice": "degrade"}]},
        episodes={"data": []},
        raep=0,
        recommandations=[]
    )
    assert nl.show_radon == False

def test_show_radon_recent(db_session, inscription):
    today_date = date.today()
    db_session.add(
        published_recommandation(),
    )
    inscription.allergie_pollens=False
    past_nl = NewsletterDB(
        Newsletter(
        inscription=inscription,
        forecast={"data": [{"date": str(today_date), "indice": "bon"}]},
        episodes={"data": []},
        raep=0,
        recommandations=[]
    ))
    db_session.add(past_nl)
    db_session.commit()

    today_date = date.today()
    nl = Newsletter(
        inscription=inscription,
        forecast={"data": [{"date": str(today_date), "indice": "bon"}]},
        episodes={"data": []},
        raep=0,
        recommandations=[],
        radon=3
    )
    assert nl.show_radon == False

    past_nl.date = today_date - timedelta(days=15)
    db_session.add(past_nl)
    db_session.commit()
    nl = Newsletter(
        inscription=inscription,
        forecast={"data": [{"date": str(today_date), "indice": "bon"}]},
        episodes={"data": []},
        raep=0,
        recommandations=[],
        radon=3
    )
    assert nl.show_radon == True

    past_nl.date = today_date - timedelta(days=15)
    db_session.add(past_nl)
    db_session.commit()
    nl = Newsletter(
        inscription=inscription,
        forecast={"data": [{"date": str(today_date), "indice": "bon"}]},
        episodes={"data": []},
        raep=0,
        recommandations=[],
        radon=2
    )
    assert nl.show_radon == False

    past_nl.date = today_date - timedelta(days=30)
    db_session.add(past_nl)
    db_session.commit()
    nl = Newsletter(
        inscription=inscription,
        forecast={"data": [{"date": str(today_date), "indice": "bon"}]},
        episodes={"data": []},
        raep=0,
        recommandations=[],
        radon=2
    )
    assert nl.show_radon == True


def test_sous_indice(db_session, inscription):
    recommandations=[
        published_recommandation(particules_fines=True, autres=True, enfants=False, dioxyde_azote=True),
        published_recommandation(particules_fines=True, personnes_sensibles=True, dioxyde_azote=True),
        published_recommandation(type_="pollens"),
        published_recommandation(type_="generale")
    ]
    db_session.add_all(recommandations)
    db_session.commit()
    today_date = date.today()
    inscription.allergie_pollens = False
    nl = Newsletter(
        inscription=inscription,
        forecast={"data": [{"date": str(today_date), "indice": "bon"}]},
        episodes={"data": []},
        raep=0,
        recommandations=recommandations,
        radon=2
    )
    noms_sous_indices = ['no2', 'so2', 'o3', 'pm10', 'pm25']
    nldb = NewsletterDB(nl)
    for sous_indice in noms_sous_indices:
        assert nldb.attributes()[f'SS_INDICE_{sous_indice.upper()}_LABEL'] == ""
        assert nldb.attributes()[f'SS_INDICE_{sous_indice.upper()}_COULEUR'] == ""

    forecast = {
        'couleur': '#50CCAA',
        'date': str(today_date),
        'indice': 'moyen',
        'label': 'Moyen',
        'sous_indices': [{'couleur': '#50CCAA',
        'indice': 'moyen',
        'label': 'Moyen',
        'polluant_name': 'NO2'},
        {'couleur': '#50F0E6',
        'indice': 'bon',
        'label': 'Bon',
        'polluant_name': 'SO2'},
        {'couleur': '#50CCAA',
        'indice': 'moyen',
        'label': 'Moyen',
        'polluant_name': 'O3'},
        {'couleur': '#50F0E6',
        'indice': 'bon',
        'label': 'Bon',
        'polluant_name': 'PM10'},
        {'couleur': '#50F0E6',
        'indice': 'bon',
        'label': 'Bon',
        'polluant_name': 'PM25'}],
        'valeur': 2
    }

    nl = Newsletter(
        inscription=inscription,
        forecast={"data": [forecast]},
        episodes={"data": []},
        raep=0,
        recommandations=recommandations,
        radon=2
    )
    noms_sous_indices = ['no2', 'so2', 'o3', 'pm10', 'pm25']
    nldb = NewsletterDB(nl)
    for sous_indice in noms_sous_indices:
        assert nldb.attributes()[f'SS_INDICE_{sous_indice.upper()}_LABEL'] != ""
        assert type(nldb.attributes()[f'SS_INDICE_{sous_indice.upper()}_LABEL']) == str
        assert nldb.attributes()[f'SS_INDICE_{sous_indice.upper()}_COULEUR'] != ""
        assert type(nldb.attributes()[f'SS_INDICE_{sous_indice.upper()}_COULEUR']) == str


def test_sorted_recommandation_query(db_session, inscription):
    recommandations=[
        published_recommandation(ordre=1),
        published_recommandation(),
        published_recommandation(),
        published_recommandation()
    ]
    db_session.add_all(recommandations)
    db_session.commit()
    today_date = date.today()
    yesterday_date = today_date - timedelta(days=1)
    tomorrow_date = today_date + timedelta(days=1)
    nl = Newsletter(
        inscription=inscription,
        forecast={"data": [{"date": str(yesterday_date), "indice": "bon"}]},
        episodes={"data": []},
        raep=0,
        recommandations=recommandations,
        radon=2,
        date=yesterday_date
    )
    db_session.add(NewsletterDB(nl))
    db_session.commit()
    yesterday_recommandation = nl.recommandation
    assert yesterday_recommandation.ordre == 1

    nl = Newsletter(
        inscription=inscription,
        forecast={"data": [{"date": str(today_date), "indice": "bon"}]},
        episodes={"data": []},
        raep=0,
        recommandations=recommandations,
        radon=2,
        date=today_date
    )
    db_session.add(NewsletterDB(nl))
    db_session.commit()
    today_recommandation = nl.recommandation
    sorted_recommandations =  nl.sorted_recommandations_query.all()
    next(filter(lambda a: a[1] == yesterday_recommandation.id, sorted_recommandations))[0] == 1.0

    nl = Newsletter(
        inscription=inscription,
        forecast={"data": [{"date": str(tomorrow_date), "indice": "bon"}]},
        episodes={"data": []},
        raep=0,
        recommandations=recommandations,
        radon=2,
        date=tomorrow_date
    )
    nl.sorted_recommandations_query.all()[-1][0] == 2.0
    sorted_recommandations =  nl.sorted_recommandations_query.all()
    next(filter(lambda a: a[1] == yesterday_recommandation.id, sorted_recommandations))[0] == 2.0
    next(filter(lambda a: a[1] == today_recommandation.id, sorted_recommandations))[0] == 2.0

def test_export_simple(db_session, inscription, bonne_qualite_air, raep_nul):
    db_session.add(published_recommandation())
    db_session.add(inscription)
    db_session.commit()

    newsletters = list(Newsletter.export())
    assert len(newsletters) == 1

def test_export_user_hebdo(db_session, inscription, templates):
    inscription.recommandations_actives = ["non"]
    newsletters = list(Newsletter.export(type_='hebdomadaire'))
    assert len(newsletters) == 0

    inscription.recommandations_actives = ["oui"]
    db_session.add(inscription)
    db_session.commit()

    newsletters = list(Newsletter.export(type_='hebdomadaire'))
    assert len(newsletters) == 1
    nl = newsletters[0]
    assert nl.newsletter_hebdo_template is not None
    assert nl.newsletter_hebdo_template.ordre == 1

    db_session.add(NewsletterDB(nl))
    db_session.commit()

    newsletters = list(Newsletter.export(type_='hebdomadaire'))
    assert len(newsletters) == 0


def test_export_user_hebdo_ordre(db_session, inscription, templates):
    yesterday = date.today() - timedelta(days=1)
    nl1 = Newsletter(
        inscription=inscription,
        date=yesterday,
        newsletter_hebdo_template=templates[1]
    )
    db_session.add(NewsletterDB(nl1))
    db_session.commit()

    newsletters = list(Newsletter.export(type_='hebdomadaire'))
    nl2 = newsletters[0]
    assert nl2.newsletter_hebdo_template.ordre > nl1.newsletter_hebdo_template.ordre


def test_export_user_hebdo_quotidien(db_session, inscription, templates, bonne_qualite_air, raep_eleve):
    db_session.add(inscription)
    db_session.commit()
    newsletters_hebdo = list(Newsletter.export(type_='hebdomadaire'))
    assert len(newsletters_hebdo) == 1
    assert newsletters_hebdo[0].newsletter_hebdo_template is not None

    newsletters_quotidien = list(Newsletter.export(type_='quotidien'))
    assert len(newsletters_quotidien) == 1
    assert newsletters_quotidien[0].newsletter_hebdo_template is None

def test_export_user_hebdo_alerte(db_session, inscription, templates):
    inscription.indicateurs_frequence = ['alerte']
    db_session.add(inscription)

    newsletters_hebdo = list(Newsletter.export(type_='hebdomadaire'))
    assert len(newsletters_hebdo) == 1
    assert newsletters_hebdo[0].newsletter_hebdo_template is not None


@pytest.mark.parametrize(
    "inscription, episode, raep, nb_nls",
    [
        ("inscription_alerte", "episode_soufre", "raep_faible", 1),
        ("inscription_alerte", "", "raep_faible", 0),
        ("inscription_alerte", "episode_soufre", "raep_eleve", 1),
        ("inscription_alerte", "", "raep_eleve", 1)
    ]
)
def test_export(db_session, recommandation, bonne_qualite_air, inscription, episode, raep, nb_nls, request):
    inscription = request.getfixturevalue(inscription)
    db_session.add(inscription)
    raep = request.getfixturevalue(raep)
    if episode:
        episode = request.getfixturevalue(episode)
        db_session.add(episode)
    db_session.commit()
    
    newsletters = list(Newsletter.export())
    assert len(newsletters) == nb_nls

def test_get_recommandation_simple_case(inscription, recommandation):
    nl = Newsletter(
        inscription=inscription,
        forecast={"data": []},
        episodes={"data": []},
        recommandations=[recommandation],
    )

    assert nl.recommandation is not None

def test_get_recommandation_deja_recue(inscription, db_session):
    yesterday = date.today() - timedelta(days=1)
    recommandations = [
        published_recommandation(),
        published_recommandation()
    ]
    db_session.add_all(recommandations)
    nl1 = Newsletter(
        inscription=inscription,
        forecast={"data": []},
        episodes={"data": []},
        recommandations=recommandations,
        date=yesterday
    )
    db_session.add(NewsletterDB(nl1))
    db_session.commit()
    nl2 = Newsletter(
        inscription=inscription,
        forecast={"data": []},
        episodes={"data": []},
        recommandations=recommandations,
    )
    assert nl1.recommandation.id != nl2.recommandation.id

def test_get_recommandation_par_type(inscription, db_session):
    recommandations = [
        published_recommandation(),
        published_recommandation(type_="raep")
    ]
    db_session.add_all(recommandations)
    nl = Newsletter(
        inscription=inscription,
        forecast={"data": []},
        episodes={"data": []},
        recommandations=recommandations,
    )
    eligible_recommandations = list(nl.eligible_recommandations({r.id: r for r in recommandations}, types=["indice_atmo"]))
    assert all([r.type_ == "indice_atmo"] for r in eligible_recommandations)

def test_vigilance(db_session, inscription, bonne_qualite_air, raep_nul):
    db_session.add(published_recommandation())
    db_session.add(inscription)
    db_session.commit()

    for phenomene_id in VigilanceMeteo.phenomenes.keys():
        v = VigilanceMeteo(
            zone_id=inscription.commune.departement.zone_id,
            phenomene_id=phenomene_id,
            couleur_id=1,
            date_export=datetime.now() - timedelta(hours=1),
            validity=DateTimeTZRange(date.today() - timedelta(days=1), date.today() + timedelta(days=1)),
        )
        db_session.add(v)
        db_session.commit()
        newsletters = list(Newsletter.export())
        assert len(newsletters) == 1
        attributes = NewsletterDB(newsletters[0]).attributes()
        key = f'VIGILANCE_{Newsletter.phenomenes_sib[phenomene_id].upper()}'
        assert f'{key}_COULEUR' in attributes
        assert attributes[f'{key}_COULEUR'] == 'Vert'
        assert attributes[f'{key}_COULEUR'] == attributes['VIGILANCE_GLOBALE_COULEUR']

        db_session.delete(v)
        db_session.commit()

def test_vigilance_alerte(db_session, inscription, bonne_qualite_air, raep_nul):
    db_session.add(published_recommandation())
    inscription.indicateurs_frequence = ['alerte']
    inscription.indicateurs = ['vigilance_meteo']
    db_session.add(inscription)
    db_session.commit()

    for phenomene_id in VigilanceMeteo.phenomenes.keys():
        v = VigilanceMeteo(
            zone_id=inscription.commune.departement.zone_id,
            phenomene_id=phenomene_id,
            couleur_id=1,
            date_export=datetime.now() - timedelta(hours=1),
            validity=DateTimeTZRange(date.today() - timedelta(days=1), date.today() + timedelta(days=1)),
        )
        db_session.add(v)
        db_session.commit()
        newsletters = list(Newsletter.export())
        assert len(newsletters) == 0
        db_session.delete(v)
        db_session.commit()

    for phenomene_id in VigilanceMeteo.phenomenes.keys():
        v = VigilanceMeteo(
            zone_id=inscription.commune.departement.zone_id,
            phenomene_id=phenomene_id,
            couleur_id=3,
            date_export=datetime.now() - timedelta(hours=1),
            validity=DateTimeTZRange(date.today() - timedelta(days=1), date.today() + timedelta(days=1)),
        )
        db_session.add(v)
        db_session.commit()
        newsletters = list(Newsletter.export())
        assert len(newsletters) == 1
        attributes = NewsletterDB(newsletters[0]).attributes()
        key = f'VIGILANCE_{Newsletter.phenomenes_sib[phenomene_id].upper()}'
        assert f'{key}_COULEUR' in attributes
        assert attributes[f'{key}_COULEUR'] == 'Orange'
        assert attributes[f'{key}_COULEUR'] == attributes['VIGILANCE_GLOBALE_COULEUR']

        db_session.delete(v)
        db_session.commit()