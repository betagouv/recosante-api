from ecosante.recommandations.models import Recommandation
from ecosante.inscription.models import Inscription

def help_activites(nom_activite):
    r = Recommandation(**{nom_activite: True})
    i = Inscription(activites=[nom_activite])
    assert r.is_relevant(i, 0)

    r = Recommandation(**{nom_activite: True})
    i = Inscription(activites=[])
    assert not r.is_relevant(i, 0)

def help_deplacement(nom_deplacement, nom_deplacement_inscription=None):
    r = Recommandation(**{nom_deplacement: True})
    i = Inscription(deplacement=[nom_deplacement_inscription or nom_deplacement])
    assert r.is_relevant(i, 0)

    r = Recommandation(**{nom_deplacement: True})
    i = Inscription(deplacement=[])
    assert not r.is_relevant(i, 0)

def test_is_relevant_menage(db_session):
    help_activites('menage')

def test_is_relevant_bricolage(db_session):
    help_activites('bricolage')

def test_is_relevant_jardinage(db_session):
    help_activites('jardinage')

def test_is_relevant_sport(db_session):
    help_activites('sport')

def test_is_relevant_velo(db_session):
    r = Recommandation(velo_trott_skate=True)
    i = Inscription(deplacement=["velo"])
    assert r.is_relevant(i, 0)

    r = Recommandation(velo_trott_skate=True)
    i = Inscription(deplacement=[])
    assert not r.is_relevant(i, 0)

def test_is_relevant_transport_en_commun(db_session):
    help_deplacement("transport_en_commun", "tec")

def test_is_relevant_voiture(db_session):
    help_deplacement("voiture")


def test_is_relevant_allergie(db_session):
   r = Recommandation(allergies=True)
   i = Inscription(allergie_pollen=True)
   assert r.is_relevant(i, 0)

   r = Recommandation(allergies=True)
   i = Inscription(allergie_pollen=False)
   assert not r.is_relevant(i, 0)

def test_is_relevant_enfants(db_session):
    r = Recommandation(enfants=True)
    i = Inscription(enfants=True)
    assert r.is_relevant(i, 0)

    r = Recommandation(enfants=True)
    i = Inscription(enfants=False)
    assert not r.is_relevant(i, 0)

def test_is_relevant_fumeurs(db_session):
    r = Recommandation(fumeur=True)
    i = Inscription(fumeur=True)
    assert r.is_relevant(i, 0)

    r = Recommandation(fumeur=True)
    i = Inscription(fumeur=False)
    assert not r.is_relevant(i, 0)

def test_is_qualite_mauvaise(db_session):
    r = Recommandation(qa_mauvaise=True)
    i = Inscription()
    assert r.is_relevant(i, 9)
    assert not r.is_relevant(i, 1)

def test_is_qualite_moyenne(db_session):
    r = Recommandation(qa_moyenne=True)
    i = Inscription()
    assert r.is_relevant(i, 5)
    assert r.is_relevant(i, 6)
    assert not r.is_relevant(i, 1)
    assert not r.is_relevant(i, 4)
    assert not r.is_relevant(i, 8)
    assert not r.is_relevant(i, 9)

def test_is_qualite_bonne(db_session):
    r = Recommandation(qa_bonne=True)
    i = Inscription()
    assert r.is_relevant(i, 1)
    assert r.is_relevant(i, 4)
    assert not r.is_relevant(i, 5)
    assert not r.is_relevant(i, 9)