from indice_pollution import today
from ecosante.newsletter.models import Inscription, Newsletter, NewsletterDB, Recommandation
from datetime import date, timedelta

def test_episode_passe(client):
    yesterday = date.today() - timedelta(days=1)
    nl = NewsletterDB(Newsletter(
        Inscription(diffusion='mail', ville_insee='38185'),
        forecast={"data": []},
        episodes={"data": [{"code_pol": "5", "etat": "INFORMATION ET RECOMMANDATION", "date": str(yesterday)}]},
        recommandations=[Recommandation(particules_fines=True), Recommandation(recommandation="ça va en fait")]
    ))
    assert nl.polluants_formatted == None
    assert nl.polluants_symbols == []
    assert nl.lien_recommandations_alerte == None
    assert nl.attributes()['POLLUANT'] == ""
    assert nl.attributes()['LIEN_RECOMMANDATIONS_ALERTE'] == ""
    assert nl.attributes()['RECOMMANDATION'] == 'ça va en fait'
    assert nl.attributes()['DEPARTEMENT'] == 'Isère'

def test_formatted_polluants_generale_pm10(client):
    nl = Newsletter(
        Inscription(),
        forecast={"data": []},
        episodes={"data": [{"code_pol": "5", "etat": "INFORMATION ET RECOMMANDATION", "date": str(date.today())}]},
        recommandations=[Recommandation(particules_fines=True)]
    )
    assert nl.polluants_formatted == "aux particules fines"
    assert nl.polluants_symbols == ['pm10']
    assert nl.lien_recommandations_alerte == 'http://localhost:5000/recommandation-episodes-pollution?population=generale&polluants=pm10'

def test_formatted_polluants_generale_pm10_no2(client):
    nl = Newsletter(
        Inscription(),
        forecast={"data": []},
        episodes={"data": [
            {"code_pol": "5", "etat": "INFORMATION ET RECOMMANDATION", "date": str(date.today())},
            {"code_pol": "8", "etat": "INFORMATION ET RECOMMANDATION", "date": str(date.today())},
        ]},
        recommandations=[Recommandation(particules_fines=True)]
    )
    assert nl.polluants_formatted == "aux particules fines et au dioxyde d’azote"
    assert nl.polluants_symbols == ['pm10', 'no2']
    assert nl.lien_recommandations_alerte == 'http://localhost:5000/recommandation-episodes-pollution?population=generale&polluants=pm10&polluants=no2'

def test_formatted_polluants_generale_tous(client):
    nl = Newsletter(
        Inscription(),
        forecast={"data": []},
        episodes={"data": [
            {"code_pol": "1", "etat": "INFORMATION ET RECOMMANDATION", "date": str(date.today())},
            {"code_pol": "5", "etat": "INFORMATION ET RECOMMANDATION", "date": str(date.today())},
            {"code_pol": "7", "etat": "INFORMATION ET RECOMMANDATION", "date": str(date.today())},
            {"code_pol": "8", "etat": "INFORMATION ET RECOMMANDATION", "date": str(date.today())},
        ]},
        recommandations=[Recommandation(particules_fines=True)]
    )
    assert nl.polluants_formatted == "au dioxyde de soufre, aux particules fines, à l’ozone, et au dioxyde d’azote"
    assert nl.polluants_symbols == ['so2', 'pm10', 'o3', 'no2']
    assert nl.lien_recommandations_alerte == 'http://localhost:5000/recommandation-episodes-pollution?population=generale&polluants=so2&polluants=pm10&polluants=o3&polluants=no2'

def test_formatted_polluants_generale_pm10_o3_no2(client):
    nl = Newsletter(
        Inscription(),
        forecast={"data": []},
        episodes={"data": [
            {"code_pol": "1", "etat": "PAS DE DEPASSEMENT", "date": str(date.today())},
            {"code_pol": "5", "etat": "INFORMATION ET RECOMMANDATION", "date": str(date.today())},
            {"code_pol": "7", "etat": "INFORMATION ET RECOMMANDATION", "date": str(date.today())},
            {"code_pol": "8", "etat": "INFORMATION ET RECOMMANDATION", "date": str(date.today())},
        ]},
        recommandations=[Recommandation(particules_fines=True)]
    )
    assert nl.polluants_formatted == "aux particules fines, à l’ozone, et au dioxyde d’azote"
    assert nl.polluants_symbols == ['pm10', 'o3', 'no2']
    assert nl.lien_recommandations_alerte == 'http://localhost:5000/recommandation-episodes-pollution?population=generale&polluants=pm10&polluants=o3&polluants=no2'


def test_formatted_polluants_vulnerable_no2(client):
    nl = Newsletter(
        Inscription(pathologie_respiratoire=True),
        forecast={"data": []},
        episodes={"data": [
            {"code_pol": "8", "etat": "INFORMATION ET RECOMMANDATION", "date": str(date.today())},
        ]},
        recommandations=[
            Recommandation(particules_fines=True, autres=True, enfants=False, dioxyde_azote=True),
            Recommandation(particules_fines=True, personnes_sensibles=True, dioxyde_azote=True),
        ]
    )
    assert nl.lien_recommandations_alerte == 'http://localhost:5000/recommandation-episodes-pollution?population=vulnerable&polluants=no2'
    assert nl.recommandation.personnes_sensibles == True


def test_pollens(client):
    for episodes in [[], [{"code_pol": "8", "etat": "INFORMATION ET RECOMMANDATION", "date": str(date.today())}]]:
        for raep in [0, 2, 6]:
            for allergie_pollens in [True, False]:
                for delta in range(0, 7):
                    date_ = date.today() + timedelta(days=delta)
                    for indice in ["bon", "degrade"]:
                        if delta == 0:
                            episode = episodes
                        else:
                            episode = []
                        nl = Newsletter(
                            Inscription(allergie_pollens=allergie_pollens),
                            forecast={"data": [{"date": date_, "indice": indice}]},
                            episodes={"data": episode},
                            recommandations=[
                                Recommandation(particules_fines=True, autres=True, enfants=False, dioxyde_azote=True),
                                Recommandation(particules_fines=True, personnes_sensibles=True, dioxyde_azote=True),
                                Recommandation(personne_allergique=True),
                                Recommandation(personne_allergique=False)
                            ],
                            raep=raep,
                            date_=date_
                        )

                        if episode:
                            assert nl.show_raep == False
                            assert not nl.recommandation.personne_allergique
                        else:
                            if raep == 0:
                                assert nl.show_raep == False
                                assert not nl.recommandation.personne_allergique
                            elif 0 < raep < 4:
                                if allergie_pollens:
                                    assert nl.show_raep == True
                                    assert nl.recommandation.personne_allergique == (date_.weekday() in [2, 5])
                                else:
                                    assert nl.show_raep == False
                                    assert not nl.recommandation.personne_allergique
                            else:
                                if allergie_pollens:
                                    assert nl.show_raep == True
                                    assert nl.recommandation.personne_allergique == (date_.weekday() in [2, 5])
                                else:
                                    assert nl.show_raep == True
                                    assert not nl.recommandation.personne_allergique