import pytest
from ecosante.recommandations.models import Recommandation
from ecosante.inscription.models import Inscription
from ecosante.newsletter.models import NewsletterDB, Newsletter
from indice_pollution.history.models.vigilance_meteo import VigilanceMeteo
from datetime import date, timedelta
from itertools import product

def published_recommandation(**kw):
    kw.setdefault('type_', 'indice_atmo')
    kw.setdefault('status', 'published')
    return Recommandation(**kw)

def help_activites(nom_activite):
    r = published_recommandation(**{nom_activite: True})
    i = Inscription(activites=[nom_activite])
    assert r.is_relevant(i, None, [], 0, date.today())

    r = published_recommandation(**{nom_activite: True})
    i = Inscription(activites=[])
    assert not r.is_relevant(i, None, [], 0, date.today())

def help_deplacement(nom_deplacement, nom_deplacement_inscription=None):
    r = published_recommandation(**{nom_deplacement: True})
    i = Inscription(deplacement=[nom_deplacement_inscription or nom_deplacement])
    assert r.is_relevant(i, None, [], 0, date.today())

    r = published_recommandation(**{nom_deplacement: True})
    i = Inscription(deplacement=[])
    assert not r.is_relevant(i, None, [], 0, date.today())

def test_is_relevant_menage():
    help_activites('menage')

def test_is_relevant_bricolage():
    help_activites('bricolage')

def test_is_relevant_jardinage():
    help_activites('jardinage')

def test_is_relevant_sport():
    help_activites('sport')

def test_is_relevant_velo():
    r = published_recommandation(velo=True)
    i = Inscription(deplacement=["velo"])
    assert r.is_relevant(i, None, [], 0, date.today())

    r = published_recommandation(velo=True)
    i = Inscription(deplacement=[])
    assert not r.is_relevant(i, None, [], 0, date.today())

def test_is_relevant_transport_en_commun():
    help_deplacement("tec", "tec")

def test_is_relevant_voiture(db_session):
    help_deplacement("voiture")

def test_is_relevant_enfants():
    r = published_recommandation(enfants=True)
    i = Inscription(enfants='oui')
    assert r.is_relevant(i, None, [], 0, date.today())

    r = published_recommandation(enfants=True)
    i = Inscription(enfants='non')
    assert not r.is_relevant(i, None, [], 0, date.today())

def test_is_qualite_mauvaise():
    r = published_recommandation(qa_mauvaise=True)
    i = Inscription()
    assert r.is_relevant(i, "mauvais", [], 0, date.today())
    assert not r.is_relevant(i, "bon", [], 0, date.today())

def test_is_qualite_tres_mauvaise():
    r = published_recommandation(qa_mauvaise=True)
    i = Inscription()
    assert r.is_relevant(i, "tres_mauvais", [], 0, date.today())
    assert not r.is_relevant(i, "bon", [], 0, date.today())

def test_is_qualite_extrement_mauvaise():
    r = published_recommandation(qa_mauvaise=True)
    i = Inscription()
    assert r.is_relevant(i, "extrement_mauvais", [], 0, date.today())
    assert not r.is_relevant(i, "bon", [], 0, date.today())

def test_is_qualite_bonne():
    r = published_recommandation(qa_bonne=True)
    i = Inscription()
    assert r.is_relevant(i, "bon", [], 0, date.today())
    assert r.is_relevant(i, "moyen", [], 0, date.today())
    assert not r.is_relevant(i, "extrement_mauvais", [], 0, date.today())

def test_is_qualite_bonne_mauvaise():
    r = published_recommandation(qa_bonne=True, qa_mauvaise=True)
    i = Inscription()
    assert r.is_relevant(i, "bon", [], 0, date.today())
    assert r.is_relevant(i, "moyen", [], 0, date.today())
    assert r.is_relevant(i, "degrade", [], 0, date.today())
    assert r.is_relevant(i, "extrement_mauvais", [], 0, date.today())

def test_is_relevant_ozone():
    r = published_recommandation(ozone=True, type_="episode_pollution")
    i = Inscription()
    assert r.is_relevant(inscription=i, qualif="bon", polluants=["ozone"], raep=0, date_=date.today())
    assert r.is_relevant(inscription=i, qualif="moyen", polluants=["ozone", "particules_fines"], raep=0, date_=date.today())
    assert not r.is_relevant(inscription=i, qualif="degrade", polluants=[], raep=0, date_=date.today())
    assert not r.is_relevant(inscription=i, qualif="degrade", polluants=["particules_fines"], raep=0, date_=date.today())

def test_is_relevant_particules_fines():
    r = published_recommandation(particules_fines=True, type_="episode_pollution")
    i = Inscription()
    assert r.is_relevant(i, "degrade", ["particules_fines"], 0, date.today())
    assert r.is_relevant(i, "moyen", ["ozone", "particules_fines"], 0, date.today())
    assert not r.is_relevant(i, "degrade", [], 0, date.today())
    assert not r.is_relevant(i, "bon", ["ozone"], 0, date.today())

def test_is_relevant_dioxyde_azote():
    r = published_recommandation(dioxyde_azote=True, type_="episode_pollution")
    i = Inscription()
    assert r.is_relevant(i, "degrade", ["dioxyde_azote"], 0, date.today())
    assert r.is_relevant(i, "moyen", ["ozone", "dioxyde_azote"], 0, date.today())
    assert not r.is_relevant(i, "degrade", [], 0, date.today())
    assert not r.is_relevant(i, "bon", ["ozone"], 0, date.today())

def test_is_relevant_dioxyde_soufre():
    r = published_recommandation(dioxyde_soufre=True, type_="episode_pollution")
    i = Inscription()
    assert r.is_relevant(i, "degrade", ["dioxyde_soufre"], 0, date.today())
    assert r.is_relevant(i, "moyen", ["ozone", "dioxyde_soufre"], 0, date.today())
    assert not r.is_relevant(i, "degrade", [], 0, date.today())
    assert not r.is_relevant(i, "bon", ["ozone"], 0, date.today())

def test_qualite_air_bonne_menage_bricolage():
    r = published_recommandation(menage=True, bricolage=True, qa_bonne=True)

    i = Inscription(activites=["menage"])
    assert r.is_relevant(i, "bon", [], 0, date.today())

    i = Inscription(activites=["bricolage"])
    assert r.is_relevant(i, "bon", [], 0, date.today())

    i = Inscription(activites=["bricolage", "menage"])
    assert r.is_relevant(i, "bon", [], 0, date.today())


def test_reco_pollen_pollution():
    r = published_recommandation(type_="pollens")

    i = Inscription(allergie_pollens=False)
    assert not r.is_relevant(inscription=i, qualif="bon", polluants=["ozone"], raep=0, date_=date.today())

    i = Inscription(allergie_pollens=True)
    assert not r.is_relevant(inscription=i, qualif="bon", polluants=["ozone"], raep=0, date_=date.today())

    r = published_recommandation(type_="indice_atmo")

    i = Inscription(allergie_pollens=False)
    assert not r.is_relevant(inscription=i, qualif="bon", polluants=["ozone"], raep=0, date_=date.today())

    i = Inscription(allergie_pollens=True)
    assert not r.is_relevant(inscription=i, qualif="bon", polluants=["ozone"], raep=0, date_=date.today())

def test_reco_pollen_pas_pollution_raep_nul(commune):
    r = published_recommandation(type_="pollens")

    i = Inscription(allergie_pollens=False)
    assert not r.is_relevant(i, "bon", [], 0, date.today())

    i = Inscription(allergie_pollens=True)
    assert not r.is_relevant(i, "bon", [], 0, date.today())

    r = published_recommandation()

    i = Inscription(allergie_pollens=False)
    assert r.is_relevant(i, "bon", [], 0, date.today())

    i = Inscription(allergie_pollens=True)
    assert r.is_relevant(i, "bon", [], 0, date.today())

@pytest.mark.parametrize(
    "delta,qualif,raep",
    product(
        list(range(0, 7)),
        ["bon", "mauvais"],
        [1, 6]
    )
)
def test_reco_pollen_pas_pollution_raep_faible_atmo_bon(commune, delta, qualif, raep):
    r = published_recommandation(type_="pollens", min_raep=raep)

    date_ = date.today() + timedelta(days=delta)
    i = Inscription(indicateurs=["indice_atmo"])
    assert not r.is_relevant(inscription=i, qualif=qualif, polluants=[], raep=raep, date_=date_)

    #On veut envoyer le mercredi et le samedi
    i = Inscription(indicateurs=["raep"])
    assert r.is_relevant(inscription=i, qualif=qualif, polluants=[], raep=raep, date_=date_) == (date_.weekday() in [2, 5]) 


def test_chauffage():
    r = published_recommandation(chauffage=[])
    i = Inscription(chauffage=[])
    assert r.is_relevant(i, "bon", [], 0, date.today())

    r = published_recommandation(chauffage=[])
    i = Inscription(chauffage=["bois"])
    assert r.is_relevant(i, "bon", [], 0, date.today())

    r = published_recommandation(chauffage=["bois"])
    i = Inscription(chauffage=[""])
    assert not r.is_relevant(i, "bon", [], 0, date.today())

    r = published_recommandation(chauffage=["bois"])
    i = Inscription(chauffage=["bois"])
    assert r.is_relevant(i, "bon", [], 0, date.today())

    r = published_recommandation(chauffage=None)
    i = Inscription(chauffage=None)
    assert r.is_relevant(i, "bon", [], 0, date.today())

def test_get_relevant_recent(db_session, inscription):
    r1 = published_recommandation(status="published")
    r2 = published_recommandation(ordre=0)
    db_session.add_all([r1, r2, inscription])
    db_session.commit()
    nl1 = NewsletterDB(Newsletter(
        inscription=inscription,
        forecast={"data": []},
        episodes={"data": []},
        recommandations=[r1, r2]
    ))
    assert nl1.recommandation.ordre == 0
    db_session.add(nl1)
    db_session.commit()
    nl2 = NewsletterDB(Newsletter(
        inscription=inscription,
        forecast={"data": []},
        episodes={"data": []},
        recommandations=[r1, r2]
    ))

    assert nl1.recommandation_id != nl2.recommandation_id

def test_get_relevant_last_criteres(db_session, inscription):
    r1 = published_recommandation(menage=True)
    r2 = published_recommandation(menage=True)
    r3 = published_recommandation(velo=True)
    inscription.activites = ["menage"]
    inscription.deplacement = ["velo"]
    db_session.add_all([r1, r2, r3, inscription])
    db_session.commit()
    nl = Newsletter(
        inscription=inscription,
        forecast={"data": []},
        episodes={"data": []},
        recommandations=[r1, r2, r3]
    )
    nl1 = NewsletterDB(nl)
    db_session.add(nl1)
    db_session.commit()
    nl2 = NewsletterDB(Newsletter(
        inscription=inscription,
        forecast={"data": []},
        episodes={"data": []},
        recommandations=[r1, r2, r3]
    ))
    assert nl1.recommandation.criteres != nl2.recommandation.criteres


def test_min_raep():
    r = published_recommandation(type_="pollens", min_raep=0)
    i = Inscription()
    assert r.is_relevant(i, "bon", [], 0, date.today(), media="dashboard") == True
    assert r.is_relevant(i, "bon", [], 1, date.today(), media="dashboard") == False
    assert r.is_relevant(i, "bon", [], 3, date.today(), media="dashboard") == False
    assert r.is_relevant(i, "bon", [], 4, date.today(), media="dashboard") == False
    assert r.is_relevant(i, "bon", [], 6, date.today(), media="dashboard") == False

    r = published_recommandation(type_="pollens", min_raep=1)
    i = Inscription()
    assert r.is_relevant(i, "bon", [], 0, date.today(), media="dashboard") == False
    assert r.is_relevant(i, "bon", [], 1, date.today(), media="dashboard") == True
    assert r.is_relevant(i, "bon", [], 3, date.today(), media="dashboard") == True
    assert r.is_relevant(i, "bon", [], 4, date.today(), media="dashboard") == False
    assert r.is_relevant(i, "bon", [], 6, date.today(), media="dashboard") == False

    r = published_recommandation(type_="pollens", min_raep=4)
    i = Inscription()
    assert r.is_relevant(i, "bon", [], 0, date.today(), media="dashboard") == False
    assert r.is_relevant(i, "bon", [], 1, date.today(), media="dashboard") == False
    assert r.is_relevant(i, "bon", [], 3, date.today(), media="dashboard") == False
    assert r.is_relevant(i, "bon", [], 4, date.today(), media="dashboard") == True
    assert r.is_relevant(i, "bon", [], 6, date.today(), media="dashboard") == True

def test_vigilances():
    r = published_recommandation(type_="vigilance_meteo", vigilance_couleur_ids=[1], vigilance_phenomene_ids=[1])
    assert r.is_relevant(media="dashboard", types=["vigilance_meteo"]) == False

    v1 =  VigilanceMeteo(couleur_id=1, phenomene_id=1)
    assert r.is_relevant(media="dashboard", vigilances=[v1], types=["vigilance_meteo"]) == True

    v2 =  VigilanceMeteo(couleur_id=1, phenomene_id=2)
    assert r.is_relevant(media="dashboard", vigilances=[v2], types=["vigilance_meteo"]) == False

    v3 =  VigilanceMeteo(couleur_id=2, phenomene_id=1)
    assert r.is_relevant(media="dashboard", vigilances=[v3], types=["vigilance_meteo"]) == False

    assert r.is_relevant(media="dashboard", vigilances=[v2, v1, v3], types=["vigilance_meteo"]) == True