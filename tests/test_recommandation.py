from ecosante.recommandations.models import Recommandation
from ecosante.inscription.models import Inscription
from ecosante.newsletter.models import NewsletterDB, Newsletter
from datetime import date, timedelta

def published_recommandation(**kw):
    kw.setdefault('type_', 'generale')
    kw.setdefault('medias', ['newsletter'])
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
    r = published_recommandation(velo_trott_skate=True)
    i = Inscription(deplacement=["velo"])
    assert r.is_relevant(i, None, [], 0, date.today())

    r = published_recommandation(velo_trott_skate=True)
    i = Inscription(deplacement=[])
    assert not r.is_relevant(i, None, [], 0, date.today())

def test_is_relevant_transport_en_commun():
    help_deplacement("transport_en_commun", "tec")

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

    r = published_recommandation(type_="generale")

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

    r = published_recommandation(type_="generale")

    i = Inscription(allergie_pollens=False)
    assert r.is_relevant(i, "bon", [], 0, date.today())

    i = Inscription(allergie_pollens=True)
    assert r.is_relevant(i, "bon", [], 0, date.today())

def test_reco_pollen_pas_pollution_raep_faible_atmo_bon(commune):
    r = published_recommandation(type_="pollens", min_raep=1)

    for delta in range(0, 7):
        date_ = date.today() + timedelta(days=delta)
        i = Inscription(allergie_pollens=False)
        assert not r.is_relevant(inscription=i, qualif="bon", polluants=[], raep=1, date_=date_)

        #On veut envoyer le mercredi et le samedi
        i = Inscription(allergie_pollens=True)
        assert r.is_relevant(inscription=i, qualif="bon", polluants=[], raep=1, date_=date_) == (date_.weekday() in [2, 5])

def test_reco_pollen_pas_pollution_raep_faible_atmo_mauvais(commune):
    r = published_recommandation(type_="pollens", min_raep=1)

    for delta in range(0, 7):
        date_ = date.today() + timedelta(days=delta)
        i = Inscription(allergie_pollens=False)
        assert not r.is_relevant(inscription=i, qualif="bon", polluants=[], raep=1, date_=date_)

        #On veut envoyer le mercredi et le samedi
        i = Inscription(allergie_pollens=True)
        assert r.is_relevant(inscription=i, qualif="bon", polluants=[], raep=1, date_=date_) == (date_.weekday() in [2, 5])

def test_reco_pollen_pas_pollution_raep_eleve_atmo_bon(commune):
    r = published_recommandation(type_="pollens", min_raep=1)

    for delta in range(0, 7):
        date_ = date.today() + timedelta(days=delta)
        i = Inscription(allergie_pollens=False)
        assert not r.is_relevant(inscription=i, qualif="bon", polluants=[], raep=6, date_=date_)

        #On veut envoyer le mercredi et le samedi
        i = Inscription(allergie_pollens=True)
        assert r.is_relevant(inscription=i, qualif="bon", polluants=[], raep=6, date_=date_) == (date_.weekday() in [2, 5])

def test_reco_pollen_pas_pollution_raep_eleve_atmo_mauvais(commune):
    r = published_recommandation(type_="pollens", min_raep=1)

    for delta in range(0, 7):
        date_ = date.today() + timedelta(days=delta)
        i = Inscription(allergie_pollens=False)
        assert not r.is_relevant(inscription=i, qualif="bon", polluants=[], raep=6, date_=date_)

        #On veut envoyer le mercredi et le samedi
        i = Inscription(allergie_pollens=True)
        assert r.is_relevant(inscription=i, qualif="bon", polluants=[], raep=6, date_=date_) == (date_.weekday() in [2, 5])

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
    r3 = published_recommandation(velo_trott_skate=True)
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
    r = published_recommandation(type_="pollens", min_raep=4)
    i = Inscription()
    assert r.is_relevant(i, "bon", [], 0, date.today()) == False

def test_personne_allergique():
    r = published_recommandation(personne_allergique=None)
    i = Inscription()
    assert r.is_relevant(i, "bon", [], 0, date.today()) == True
    i = Inscription(allergie_pollens=True)
    assert r.is_relevant(i, "bon", [], 0, date.today()) == True
    i = Inscription(allergie_pollens=False)
    assert r.is_relevant(i, "bon", [], 0, date.today()) == True

    r = published_recommandation(personne_allergique=True)
    i = Inscription()
    assert r.is_relevant(i, "bon", [], 0, date.today()) == False
    i = Inscription(allergie_pollens=True)
    assert r.is_relevant(i, "bon", [], 0, date.today()) == True
    i = Inscription(allergie_pollens=False)
    assert r.is_relevant(i, "bon", [], 0, date.today()) == False

    r = published_recommandation(personne_allergique=False)
    i = Inscription()
    assert r.is_relevant(i, "bon", [], 0, date.today()) == True
    i = Inscription(allergie_pollens=True)
    assert r.is_relevant(i, "bon", [], 0, date.today()) == False
    i = Inscription(allergie_pollens=False)
    assert r.is_relevant(i, "bon", [], 0, date.today()) == True

def test_widget():
    r = published_recommandation(personne_allergique=None, medias=['widget'])
    assert r.is_relevant(qualif="bon", media='widget', types=['generale']) == True

def test_dashboard():
    r = published_recommandation(medias=['dashboard'])
    assert r.is_relevant(qualif="bon", media='dashboard', types=['generale']) == True