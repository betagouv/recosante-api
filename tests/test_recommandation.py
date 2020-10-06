from ecosante.recommandations.models import Recommandation
from ecosante.inscription.models import Inscription

class TestRecommandation:

    def help_activites(self, nom_activite):
        r = Recommandation(**{nom_activite: True})
        i = Inscription(activites=[nom_activite])
        assert r.is_relevant(i, 0)

        r = Recommandation(**{nom_activite: True})
        i = Inscription(activites=[])
        assert not r.is_relevant(i, 0)

    def help_deplacement(self, nom_deplacement, nom_deplacement_inscription=None):
        r = Recommandation(**{nom_deplacement: True})
        i = Inscription(deplacement=[nom_deplacement_inscription or nom_deplacement])
        assert r.is_relevant(i, 0)

        r = Recommandation(**{nom_deplacement: True})
        i = Inscription(deplacement=[])
        assert not r.is_relevant(i, 0)

    def test_is_revelant_menage(self):
        self.help_activites('menage')

    def test_is_revelant_bricolage(self):
        self.help_activites('bricolage')

    def test_is_revelant_jardinage(self):
        self.help_activites('jardinage')

    def test_is_revelant_sport(self):
        self.help_activites('sport')

    def test_is_revelant_velo(self):
        r = Recommandation(velo_trott_skate=True)
        i = Inscription(deplacement=["velo"])
        assert r.is_relevant(i, 0)

        r = Recommandation(velo_trott_skate=True)
        i = Inscription(deplacement=[])
        assert not r.is_relevant(i, 0)

    def test_is_revelant_transport_en_commun(self):
        self.help_deplacement("transport_en_commun", "tec")

    def test_is_revelant_voiture(self):
        self.help_deplacement("voiture")

    def test_is_revelant_allergie(self):
        r = Recommandation(allergies=True)
        i = Inscription(allergie_pollen=True)
        assert r.is_relevant(i, 0)

        r = Recommandation(allergies=True)
        i = Inscription(allergie_pollen=False)
        assert not r.is_relevant(i, 0)

    def test_is_revelant_enfants(self):
        r = Recommandation(enfants=True)
        i = Inscription(enfants=True)
        assert r.is_relevant(i, 0)

        r = Recommandation(enfants=True)
        i = Inscription(enfants=False)
        assert not r.is_relevant(i, 0)

    def test_is_revelant_fumeurs(self):
        r = Recommandation(fumeur=True)
        i = Inscription(fumeur=True)
        assert r.is_relevant(i, 0)

        r = Recommandation(fumeur=True)
        i = Inscription(fumeur=False)
        assert not r.is_relevant(i, 0)