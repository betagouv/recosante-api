from ecosante.newsletter.models import Inscription, Newsletter, NewsletterDB, Recommandation
from datetime import date, timedelta

def test_episode_passe(db_session):
    yesterday = date.today() - timedelta(days=1)
    recommandations = [Recommandation(particules_fines=True, status="published"), Recommandation(recommandation="ça va en fait", status="published")]
    db_session.add_all(recommandations)
    db_session.commit()
    nl = NewsletterDB(Newsletter(
        inscription=Inscription(diffusion='mail', ville_insee='38185'),
        forecast={"data": []},
        episodes={"data": [{"code_pol": "5", "etat": "INFORMATION ET RECOMMANDATION", "date": str(yesterday)}]},
        recommandations=recommandations
    ))
    assert nl.polluants_formatted == None
    assert nl.polluants_symbols == []
    assert nl.lien_recommandations_alerte == None
    assert nl.attributes()['POLLUANT'] == ""
    assert nl.attributes()['LIEN_RECOMMANDATIONS_ALERTE'] == ""
    assert nl.attributes()['RECOMMANDATION'] == 'ça va en fait'
    assert nl.attributes()['DEPARTEMENT'] == 'Isère'

def test_formatted_polluants_generale_pm10(db_session):
    recommandations = [Recommandation(particules_fines=True, status="published")]
    db_session.add_all(recommandations)
    db_session.commit()
    nl = Newsletter(
        inscription=Inscription(),
        forecast={"data": []},
        episodes={"data": [{"code_pol": "5", "etat": "INFORMATION ET RECOMMANDATION", "date": str(date.today())}]},
        recommandations=recommandations
    )
    assert nl.polluants_formatted == "aux particules fines"
    assert nl.polluants_symbols == ['pm10']
    assert nl.lien_recommandations_alerte == 'http://localhost:5000/recommandation-episodes-pollution?population=generale&polluants=pm10'

def test_formatted_polluants_generale_pm10_no2(db_session):
    recommandations = [Recommandation(particules_fines=True, status="published")]
    db_session.add_all(recommandations)
    db_session.commit()
    nl = Newsletter(
        inscription=Inscription(),
        forecast={"data": []},
        episodes={"data": [
            {"code_pol": "5", "etat": "INFORMATION ET RECOMMANDATION", "date": str(date.today())},
            {"code_pol": "8", "etat": "INFORMATION ET RECOMMANDATION", "date": str(date.today())},
        ]},
        recommandations=recommandations
    )
    assert nl.polluants_formatted == "aux particules fines et au dioxyde d’azote"
    assert nl.polluants_symbols == ['pm10', 'no2']
    assert nl.lien_recommandations_alerte == 'http://localhost:5000/recommandation-episodes-pollution?population=generale&polluants=pm10&polluants=no2'

def test_formatted_polluants_generale_tous(db_session):
    recommandations = [Recommandation(particules_fines=True, status="published")]
    db_session.add_all(recommandations)
    db_session.commit()
    nl = Newsletter(
        inscription=Inscription(),
        forecast={"data": []},
        episodes={"data": [
            {"code_pol": "1", "etat": "INFORMATION ET RECOMMANDATION", "date": str(date.today())},
            {"code_pol": "5", "etat": "INFORMATION ET RECOMMANDATION", "date": str(date.today())},
            {"code_pol": "7", "etat": "INFORMATION ET RECOMMANDATION", "date": str(date.today())},
            {"code_pol": "8", "etat": "INFORMATION ET RECOMMANDATION", "date": str(date.today())},
        ]},
        recommandations=recommandations
    )
    assert nl.polluants_formatted == "au dioxyde de soufre, aux particules fines, à l’ozone, et au dioxyde d’azote"
    assert nl.polluants_symbols == ['so2', 'pm10', 'o3', 'no2']
    assert nl.lien_recommandations_alerte == 'http://localhost:5000/recommandation-episodes-pollution?population=generale&polluants=so2&polluants=pm10&polluants=o3&polluants=no2'

def test_formatted_polluants_generale_pm10_o3_no2(db_session):
    recommandations = [Recommandation(particules_fines=True, status="published")]
    db_session.add_all(recommandations)
    db_session.commit()
    nl = Newsletter(
        inscription=Inscription(),
        forecast={"data": []},
        episodes={"data": [
            {"code_pol": "1", "etat": "PAS DE DEPASSEMENT", "date": str(date.today())},
            {"code_pol": "5", "etat": "INFORMATION ET RECOMMANDATION", "date": str(date.today())},
            {"code_pol": "7", "etat": "INFORMATION ET RECOMMANDATION", "date": str(date.today())},
            {"code_pol": "8", "etat": "INFORMATION ET RECOMMANDATION", "date": str(date.today())},
        ]},
        recommandations=recommandations
    )
    assert nl.polluants_formatted == "aux particules fines, à l’ozone, et au dioxyde d’azote"
    assert nl.polluants_symbols == ['pm10', 'o3', 'no2']
    assert nl.lien_recommandations_alerte == 'http://localhost:5000/recommandation-episodes-pollution?population=generale&polluants=pm10&polluants=o3&polluants=no2'


def test_formatted_polluants_vulnerable_no2(db_session):
    recommandations=[
        Recommandation(particules_fines=True, autres=True, enfants=False, dioxyde_azote=True, status="published"),
        Recommandation(particules_fines=True, personnes_sensibles=True, dioxyde_azote=True, status="published"),
    ]
    db_session.add_all(recommandations)
    db_session.commit()
    nl = Newsletter(
        inscription=Inscription(pathologie_respiratoire=True),
        forecast={"data": []},
        episodes={"data": [
            {"code_pol": "8", "etat": "INFORMATION ET RECOMMANDATION", "date": str(date.today())},
        ]},
        recommandations=recommandations
    )
    assert nl.lien_recommandations_alerte == 'http://localhost:5000/recommandation-episodes-pollution?population=vulnerable&polluants=no2'
    assert nl.recommandation.personnes_sensibles == True


def test_avis_oui(db_session, client):
    recommandations=[
        Recommandation(particules_fines=True, autres=True, enfants=False, dioxyde_azote=True, status="published"),
        Recommandation(particules_fines=True, personnes_sensibles=True, dioxyde_azote=True, status="published"),
    ]
    db_session.add_all(recommandations)
    db_session.commit()
    nl = Newsletter(
        inscription=Inscription(pathologie_respiratoire=True),
        forecast={"data": []},
        episodes={"data": [
            {"code_pol": "8", "etat": "INFORMATION ET RECOMMANDATION", "date": str(date.today())},
        ]},
        recommandations=recommandations
    )
    nldb = NewsletterDB(nl)
    db_session.add(nldb)
    db_session.commit()
    response = client.post(f'/newsletter/{nldb.short_id}/avis?appliquee=oui')
    assert response.status_code == 200
    nldb2 = NewsletterDB.query.get(nldb.id)
    assert nldb2.appliquee == True


def test_avis_non(db_session, client):
    recommandations=[
        Recommandation(particules_fines=True, autres=True, enfants=False, dioxyde_azote=True, status="published"),
        Recommandation(particules_fines=True, personnes_sensibles=True, dioxyde_azote=True, status="published"),
    ]
    db_session.add_all(recommandations)
    db_session.commit()
    nl = Newsletter(
        inscription=Inscription(pathologie_respiratoire=True),
        forecast={"data": []},
        episodes={"data": [
            {"code_pol": "8", "etat": "INFORMATION ET RECOMMANDATION", "date": str(date.today())},
        ]},
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


def test_pollens(db_session):
    recommandations=[
        Recommandation(particules_fines=True, autres=True, enfants=False, dioxyde_azote=True, status="published"),
        Recommandation(particules_fines=True, personnes_sensibles=True, dioxyde_azote=True, status="published"),
        Recommandation(type_="pollens", status="published"),
        Recommandation(type_="generale", status="published")
    ]
    db_session.add_all(recommandations)
    db_session.commit()
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
                            inscription=Inscription(allergie_pollens=allergie_pollens),
                            forecast={"data": [{"date": date_, "indice": indice}]},
                            episodes={"data": episode},
                            raep=raep,
                            date=date_,
                            recommandations=recommandations
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


def test_show_radon_polluants(db_session):
    nl = Newsletter(
        inscription=Inscription(),
        forecast={"data": []},
        episodes={"data": [{"code_pol": "8", "etat": "INFORMATION ET RECOMMANDATION", "date": str(date.today())}]},
        raep=0,
        recommandations=[]
    )

    assert nl.show_radon == False


def test_show_radon_raep(db_session):
    today_date = date.today()
    nl = Newsletter(
        inscription=Inscription(id=1, allergie_pollens=True),
        forecast={"data": [{"date": str(today_date), "indice": "bon"}]},
        episodes={"data": []},
        raep=0,
        recommandations=[]
    )
    assert nl.show_radon == True

    nl = Newsletter(
        inscription=Inscription(id=1, allergie_pollens=True),
        forecast={"data": [{"date": str(today_date), "indice": "bon"}]},
        episodes={"data": []},
        raep=4,
        recommandations=[]
    )
    assert nl.show_radon == False

    nl = Newsletter(
        inscription=Inscription(id=1, allergie_pollens=False),
        forecast={"data": [{"date": str(today_date), "indice": "bon"}]},
        episodes={"data": []},
        raep=1,
        recommandations=[]
    )
    assert nl.show_radon == True

    nl = Newsletter(
        inscription=Inscription(id=1, allergie_pollens=False),
        forecast={"data": [{"date": str(today_date), "indice": "bon"}]},
        episodes={"data": []},
        raep=4,
        recommandations=[]
    )
    assert nl.show_radon == False


def test_show_radon_indice(db_session):
    today_date = date.today()
    nl = Newsletter(
        inscription=Inscription(id=1, allergie_pollens=False),
        forecast={"data": [{"date": str(today_date), "indice": "bon"}]},
        episodes={"data": []},
        raep=0,
        recommandations=[]
    )
    assert nl.show_radon == True

    nl = Newsletter(
        inscription=Inscription(id=1, allergie_pollens=False),
        forecast={"data": [{"date": str(today_date), "indice": "moyen"}]},
        episodes={"data": []},
        raep=0,
        recommandations=[]
    )
    assert nl.show_radon == True

    today_date = date.today()
    nl = Newsletter(
        inscription=Inscription(id=1, allergie_pollens=False),
        forecast={"data": [{"date": str(today_date), "indice": "degrade"}]},
        episodes={"data": []},
        raep=0,
        recommandations=[]
    )
    assert nl.show_radon == False

def test_show_radon_recent(db_session):
    today_date = date.today()
    db_session.add(
        Recommandation(status="published"),
    )
    past_nl = NewsletterDB(
        Newsletter(
        inscription=Inscription(id=1, allergie_pollens=False),
        forecast={"data": [{"date": str(today_date), "indice": "bon"}]},
        episodes={"data": []},
        raep=0,
        recommandations=[]
    ))
    db_session.add(past_nl)
    db_session.commit()

    today_date = date.today()
    nl = Newsletter(
        inscription=Inscription(id=1, allergie_pollens=False),
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
        inscription=Inscription(id=1, allergie_pollens=False),
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
        inscription=Inscription(id=1, allergie_pollens=False),
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
        inscription=Inscription(id=1, allergie_pollens=False),
        forecast={"data": [{"date": str(today_date), "indice": "bon"}]},
        episodes={"data": []},
        raep=0,
        recommandations=[],
        radon=2
    )
    assert nl.show_radon == True