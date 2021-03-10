from ecosante.newsletter.models import Inscription, Newsletter, Recommandation

def test_formatted_polluants_generale_pm10():
    nl = Newsletter(
        Inscription(),
        forecast={"data": []},
        episodes={"data": [{"code_pol": "5", "etat": "INFORMATION ET RECOMMANDATION"}]},
        recommandations=[Recommandation(particules_fines=True)]
    )
    assert nl.polluants_formatted == "aux particules fines"
    assert nl.polluants_symbols == ['pm10']
    assert nl.lien_recommandations_alert == 'http://localhost:5000/recommandation-episodes-pollution?population=generale&polluants=pm10'

def test_formatted_polluants_generale_pm10_no2():
    nl = Newsletter(
        Inscription(),
        forecast={"data": []},
        episodes={"data": [
            {"code_pol": "5", "etat": "INFORMATION ET RECOMMANDATION"},
            {"code_pol": "8", "etat": "INFORMATION ET RECOMMANDATION"},
        ]},
        recommandations=[Recommandation(particules_fines=True)]
    )
    assert nl.polluants_formatted == "aux particules fines et au dioxyde d’azote"
    assert nl.polluants_symbols == ['pm10', 'no2']
    assert nl.lien_recommandations_alert == 'http://localhost:5000/recommandation-episodes-pollution?population=generale&polluants=pm10&polluants=no2'

def test_formatted_polluants_generale_tous():
    nl = Newsletter(
        Inscription(),
        forecast={"data": []},
        episodes={"data": [
            {"code_pol": "1", "etat": "INFORMATION ET RECOMMANDATION"},
            {"code_pol": "5", "etat": "INFORMATION ET RECOMMANDATION"},
            {"code_pol": "7", "etat": "INFORMATION ET RECOMMANDATION"},
            {"code_pol": "8", "etat": "INFORMATION ET RECOMMANDATION"},
        ]},
        recommandations=[Recommandation(particules_fines=True)]
    )
    assert nl.polluants_formatted == "au dioxyde de soufre, aux particules fines, à l’ozone, et au dioxyde d’azote"
    assert nl.polluants_symbols == ['so2', 'pm10', 'o3', 'no2']
    assert nl.lien_recommandations_alert == 'http://localhost:5000/recommandation-episodes-pollution?population=generale&polluants=so2&polluants=pm10&polluants=o3&polluants=no2'

def test_formatted_polluants_generale_pm10_o3_no2():
    nl = Newsletter(
        Inscription(),
        forecast={"data": []},
        episodes={"data": [
            {"code_pol": "1", "etat": "PAS DE DEPASSEMENT"},
            {"code_pol": "5", "etat": "INFORMATION ET RECOMMANDATION"},
            {"code_pol": "7", "etat": "INFORMATION ET RECOMMANDATION"},
            {"code_pol": "8", "etat": "INFORMATION ET RECOMMANDATION"},
        ]},
        recommandations=[Recommandation(particules_fines=True)]
    )
    assert nl.polluants_formatted == "aux particules fines, à l’ozone, et au dioxyde d’azote"
    assert nl.polluants_symbols == ['pm10', 'o3', 'no2']
    assert nl.lien_recommandations_alert == 'http://localhost:5000/recommandation-episodes-pollution?population=generale&polluants=pm10&polluants=o3&polluants=no2'


def test_formatted_polluants_vulnerable_no2(client):
    nl = Newsletter(
        Inscription(pathologie_respiratoire=True),
        forecast={"data": []},
        episodes={"data": [
            {"code_pol": "8", "etat": "INFORMATION ET RECOMMANDATION"},
        ]},
        recommandations=[
            Recommandation(particules_fines=True, autres=True, enfants=False, dioxyde_azote=True),
            Recommandation(particules_fines=True, personnes_sensibles=True, dioxyde_azote=True),
        ]
    )
    assert nl.lien_recommandations_alert == 'http://localhost:5000/recommandation-episodes-pollution?population=vulnerable&polluants=no2'
    assert nl.recommandation.personnes_sensibles == True