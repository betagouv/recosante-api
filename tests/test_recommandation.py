from re import A
from sqlalchemy.sql.operators import notendswith_op
from ecosante.recommandations.models import Recommandation
from ecosante.inscription.models import Inscription
from ecosante.newsletter.models import NewsletterDB, Newsletter
from ecosante.extensions import db
from datetime import date, timedelta

def help_activites(nom_activite):
    r = Recommandation(**{nom_activite: True})
    i = Inscription(activites=[nom_activite])
    assert r.is_relevant(i, None, [], 0, date.today())

    r = Recommandation(**{nom_activite: True})
    i = Inscription(activites=[])
    assert not r.is_relevant(i, None, [], 0, date.today())

def help_deplacement(nom_deplacement, nom_deplacement_inscription=None):
    r = Recommandation(**{nom_deplacement: True})
    i = Inscription(deplacement=[nom_deplacement_inscription or nom_deplacement])
    assert r.is_relevant(i, None, [], 0, date.today())

    r = Recommandation(**{nom_deplacement: True})
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
    r = Recommandation(velo_trott_skate=True)
    i = Inscription(deplacement=["velo"])
    assert r.is_relevant(i, None, [], 0, date.today())

    r = Recommandation(velo_trott_skate=True)
    i = Inscription(deplacement=[])
    assert not r.is_relevant(i, None, [], 0, date.today())

def test_is_relevant_transport_en_commun():
    help_deplacement("transport_en_commun", "tec")

def test_is_relevant_voiture(db_session):
    help_deplacement("voiture")

def test_is_relevant_enfants():
    r = Recommandation(enfants=True)
    i = Inscription(enfants='oui')
    assert r.is_relevant(i, None, [], 0, date.today())

    r = Recommandation(enfants=True)
    i = Inscription(enfants='non')
    assert not r.is_relevant(i, None, [], 0, date.today())

def test_is_qualite_mauvaise():
    r = Recommandation(qa_mauvaise=True)
    i = Inscription()
    assert r.is_relevant(i, "mauvais", [], 0, date.today())
    assert not r.is_relevant(i, "bon", [], 0, date.today())

def test_is_qualite_tres_mauvaise():
    r = Recommandation(qa_mauvaise=True)
    i = Inscription()
    assert r.is_relevant(i, "tres_mauvais", [], 0, date.today())
    assert not r.is_relevant(i, "bon", [], 0, date.today())

def test_is_qualite_extrement_mauvaise():
    r = Recommandation(qa_mauvaise=True)
    i = Inscription()
    assert r.is_relevant(i, "extrement_mauvais", [], 0, date.today())
    assert not r.is_relevant(i, "bon", [], 0, date.today())

def test_is_qualite_bonne():
    r = Recommandation(qa_bonne=True)
    i = Inscription()
    assert r.is_relevant(i, "bon", [], 0, date.today())
    assert r.is_relevant(i, "moyen", [], 0, date.today())
    assert not r.is_relevant(i, "extrement_mauvais", [], 0, date.today())

def test_is_qualite_bonne_mauvaise():
    r = Recommandation(qa_bonne=True, qa_mauvaise=True)
    i = Inscription()
    assert r.is_relevant(i, "bon", [], 0, date.today())
    assert r.is_relevant(i, "moyen", [], 0, date.today())
    assert r.is_relevant(i, "degrade", [], 0, date.today())
    assert r.is_relevant(i, "extrement_mauvais", [], 0, date.today())

def test_is_relevant_ozone():
    r = Recommandation(ozone=True)
    i = Inscription()
    assert r.is_relevant(i, "bon", ["ozone"], 0, date.today())
    assert r.is_relevant(i, "moyen", ["ozone", "particules_fines"], 0, date.today())
    assert not r.is_relevant(i, "degrade", [], 0, date.today())
    assert not r.is_relevant(i, "degrade", ["particules_fines"], 0, date.today())

def test_is_relevant_particules_fines():
    r = Recommandation(particules_fines=True)
    i = Inscription()
    assert r.is_relevant(i, "degrade", ["particules_fines"], 0, date.today())
    assert r.is_relevant(i, "moyen", ["ozone", "particules_fines"], 0, date.today())
    assert not r.is_relevant(i, "degrade", [], 0, date.today())
    assert not r.is_relevant(i, "bon", ["ozone"], 0, date.today())

def test_is_relevant_dioxyde_azote():
    r = Recommandation(dioxyde_azote=True)
    i = Inscription()
    assert r.is_relevant(i, "degrade", ["dioxyde_azote"], 0, date.today())
    assert r.is_relevant(i, "moyen", ["ozone", "dioxyde_azote"], 0, date.today())
    assert not r.is_relevant(i, "degrade", [], 0, date.today())
    assert not r.is_relevant(i, "bon", ["ozone"], 0, date.today())

def test_is_relevant_dioxyde_soufre():
    r = Recommandation(dioxyde_soufre=True)
    i = Inscription()
    assert r.is_relevant(i, "degrade", ["dioxyde_soufre"], 0, date.today())
    assert r.is_relevant(i, "moyen", ["ozone", "dioxyde_soufre"], 0, date.today())
    assert not r.is_relevant(i, "degrade", [], 0, date.today())
    assert not r.is_relevant(i, "bon", ["ozone"], 0, date.today())

def test_qualite_air_bonne_menage_bricolage():
    r = Recommandation(menage=True, bricolage=True, qa_bonne=True)

    i = Inscription(activites=["menage"])
    assert r.is_relevant(i, "bon", [], 0, date.today())

    i = Inscription(activites=["bricolage"])
    assert r.is_relevant(i, "bon", [], 0, date.today())

    i = Inscription(activites=["bricolage", "menage"])
    assert r.is_relevant(i, "bon", [], 0, date.today())


def test_reco_pollen_pollution():
    r = Recommandation(type_="pollens")

    i = Inscription(allergie_pollens=False)
    assert not r.is_relevant(i, "bon", ["ozone"], 0, date.today())

    i = Inscription(allergie_pollens=True)
    assert not r.is_relevant(i, "bon", ["ozone"], 0, date.today())

    r = Recommandation(type_="generale")

    i = Inscription(allergie_pollens=False)
    assert not r.is_relevant(i, "bon", ["ozone"], 0, date.today())

    i = Inscription(allergie_pollens=True)
    assert not r.is_relevant(i, "bon", ["ozone"], 0, date.today())

def test_reco_pollen_pas_pollution_raep_nul():
    r = Recommandation(type_="pollens")

    i = Inscription(allergie_pollens=False)
    assert not r.is_relevant(i, "bon", [], 0, date.today())

    i = Inscription(allergie_pollens=True)
    assert not r.is_relevant(i, "bon", [], 0, date.today())

    r = Recommandation(type_="generale")

    i = Inscription(allergie_pollens=False)
    assert r.is_relevant(i, "bon", [], 0, date.today())

    i = Inscription(allergie_pollens=True)
    assert r.is_relevant(i, "bon", [], 0, date.today())

def test_reco_pollen_pas_pollution_raep_faible_atmo_bon():
    r = Recommandation(type_="pollens")

    for delta in range(0, 7):
        date_ = date.today() + timedelta(days=delta)
        i = Inscription(allergie_pollens=False)
        assert not r.is_relevant(i, "bon", [], 1, date_)

        #On veut envoyer le mercredi et le samedi
        i = Inscription(allergie_pollens=True)
        assert r.is_relevant(i, "bon", [], 1, date_) == (date_.weekday() in [2, 5])

def test_reco_pollen_pas_pollution_raep_faible_atmo_mauvais():
    r = Recommandation(type_="pollens")

    for delta in range(0, 7):
        date_ = date.today() + timedelta(days=delta)
        i = Inscription(allergie_pollens=False)
        assert not r.is_relevant(i, "bon", [], 1, date_)

        #On veut envoyer le mercredi et le samedi
        i = Inscription(allergie_pollens=True)
        assert r.is_relevant(i, "bon", [], 1, date_) == (date_.weekday() in [2, 5])

def test_reco_pollen_pas_pollution_raep_eleve_atmo_bon():
    r = Recommandation(type_="pollens")

    for delta in range(0, 7):
        date_ = date.today() + timedelta(days=delta)
        i = Inscription(allergie_pollens=False)
        assert not r.is_relevant(i, "bon", [], 6, date_)

        #On veut envoyer le mercredi et le samedi
        i = Inscription(allergie_pollens=True)
        assert r.is_relevant(i, "bon", [], 6, date_) == (date_.weekday() in [2, 5])

def test_reco_pollen_pas_pollution_raep_eleve_atmo_mauvais():
    r = Recommandation(type_="pollens")

    for delta in range(0, 7):
        date_ = date.today() + timedelta(days=delta)
        i = Inscription(allergie_pollens=False)
        assert not r.is_relevant(i, "bon", [], 6, date_)

        #On veut envoyer le mercredi et le samedi
        i = Inscription(allergie_pollens=True)
        assert r.is_relevant(i, "bon", [], 6, date_) == (date_.weekday() in [2, 5])

def test_chauffage():
    r = Recommandation(chauffage=[])
    i = Inscription(chauffage=[])
    assert r.is_relevant(i, "bon", [], 0, date.today())

    r = Recommandation(chauffage=[])
    i = Inscription(chauffage=["bois"])
    assert r.is_relevant(i, "bon", [], 0, date.today())

    r = Recommandation(chauffage=["bois"])
    i = Inscription(chauffage=[""])
    assert not r.is_relevant(i, "bon", [], 0, date.today())

    r = Recommandation(chauffage=["bois"])
    i = Inscription(chauffage=["bois"])
    assert r.is_relevant(i, "bon", [], 0, date.today())

    r = Recommandation(chauffage=None)
    i = Inscription(chauffage=None)
    assert r.is_relevant(i, "bon", [], 0, date.today())

def test_get_relevant_recent(db_session):
    r1 = Recommandation()
    r2 = Recommandation(ordre=0)
    i = Inscription()
    db_session.add_all([r1, r2, i])
    db_session.commit()
    nl1 = NewsletterDB(Newsletter(
        inscription=i,
        forecast={"data": []},
        episodes={"data": []},
        recommandations=[r1, r2]
    ))
    assert nl1.recommandation.ordre == 0
    db_session.add(nl1)
    db_session.commit()
    nl2 = NewsletterDB(Newsletter(
        inscription=i,
        forecast={"data": []},
        episodes={"data": []},
        recommandations=[r1, r2]
    ))

    assert nl1.recommandation_id != nl2.recommandation_id

def test_get_relevant_last_criteres(db_session):
    r1 = Recommandation(menage=True)
    r2 = Recommandation(menage=True)
    r3 = Recommandation(velo_trott_skate=True)
    i = Inscription(activites=["menage"], deplacement=["velo"])
    db_session.add_all([r1, r2, r3, i])
    db_session.commit()
    nl1 = NewsletterDB(Newsletter(
        inscription=i,
        forecast={"data": []},
        episodes={"data": []},
        recommandations=[r1, r2, r3]
    ))
    db_session.add(nl1)
    db_session.commit()
    nl2 = NewsletterDB(Newsletter(
        inscription=i,
        forecast={"data": []},
        episodes={"data": []},
        recommandations=[r1, r2, r3]
    ))
    assert nl1.recommandation.criteres != nl2.recommandation.criteres


def test_min_raep():
    r = Recommandation(type_="pollens", min_raep=4)
    i = Inscription()
    assert r.is_relevant(i, "bon", [], 0, date.today()) == False