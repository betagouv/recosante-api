from sqlalchemy.sql.sqltypes import Date
from ecosante.newsletter.models import Newsletter, NewsletterDB, NewsletterHebdoTemplate
from ecosante.inscription.models import Inscription
from datetime import date, timedelta
from psycopg2.extras import DateRange

def test_get_templates(templates):
    last_t = None
    for t in NewsletterHebdoTemplate.get_templates():
        if last_t:
            assert last_t.ordre <= t.ordre
        last_t = t

def test_next_template_first(db_session, inscription, templates):
    assert NewsletterHebdoTemplate.next_template(inscription) != None

def test_next_template(db_session, inscription, templates):
    template = min(templates, key=lambda t: t.ordre)
    nl = Newsletter(inscription=inscription, newsletter_hebdo_template=template)
    db_session.add(NewsletterDB(nl))

    assert NewsletterHebdoTemplate.next_template(inscription).ordre > template.ordre 

def test_next_template_last(db_session, inscription, templates):
    for template in templates:
        nl = Newsletter(inscription=inscription, newsletter_hebdo_template=template)
        db_session.add(NewsletterDB(nl))

    assert NewsletterHebdoTemplate.next_template(inscription) == None

def test_hebdo_notification_web(db_session, inscription, templates):
    inscription.indicateurs_media = ['notification_web']
    db_session.add(inscription)
    db_session.commit()

    assert len(list(Newsletter.export(type_='hebdomadaire'))) == 1

def test_hebdo_en_dehors_periode_validite(db_session, templates, inscription):
    for t in templates:
        t._periode_validite = DateRange(
            date.today() + timedelta(days=1),
            date.today() + timedelta(days=31)
        )
        db_session.add(t)
    db_session.commit()

    assert NewsletterHebdoTemplate.next_template(inscription) == None
    assert len(list(Newsletter.export(type_='hebdomadaire'))) == 0

def test_next_template_criteres(db_session, templates, inscription):
    for t in templates:
        t.activites = ["menage"]
        db_session.add(t)
    db_session.add(inscription)
    db_session.commit()

    assert NewsletterHebdoTemplate.next_template(inscription) == None
    assert len(list(Newsletter.export(type_='hebdomadaire'))) == 0

    inscription.activites = ["menage"]
    assert NewsletterHebdoTemplate.next_template(inscription) != None
    assert len(list(Newsletter.export(type_='hebdomadaire'))) > 0


def test_hebdo_periode_validite_default(db_session, templates):
    db_session.add_all(templates)
    db_session.commit()
    t = templates[0]
    assert t.filtre_date(date.today().replace(month=1, day=12))
    assert t.filtre_date(date.today().replace(month=1, day=1))
    assert t.filtre_date(date.today().replace(month=12, day=31))

def test_periode_validite_contains_periode_validite_one_month(db_session, templates):
    t = templates[0]
    t._periode_validite = DateRange(date(2022, 1, 1), date(2022, 2, 1))
    db_session.add(t)
    db_session.commit()

    assert t.filtre_date(date.today().replace(month=1, day=1))
    assert t.filtre_date(date.today().replace(month=1, day=10))
    assert t.filtre_date(date.today().replace(month=1, day=31))

def test_periode_validite_contains_periode_validite_two_month(db_session, templates):
    t = templates[0]
    t._periode_validite = DateRange(date(2022, 7, 1), date(2022, 9, 1))
    db_session.add(t)
    db_session.commit()

    for month in [7, 8]:
        assert t.filtre_date(date.today().replace(month=month, day=1))
        assert t.filtre_date(date.today().replace(month=month, day=10))
        assert t.filtre_date(date.today().replace(month=month, day=31))

def test_periode_validite_contains_periode_validite_two_years(db_session, templates):
    t = templates[0]
    t._periode_validite = DateRange(date(2022, 10, 1), date(2023, 2, 1))
    db_session.add(t)
    db_session.commit()

    assert t.filtre_date(date.today().replace(month=1, day=1))
    assert t.filtre_date(date.today().replace(month=10, day=1))
    assert t.filtre_date(date.today().replace(month=10, day=10))
    assert t.filtre_date(date.today().replace(month=12, day=31))
    assert t.filtre_date(date.today().replace(year=date.today().year+1, month=1, day=1))
    assert t.filtre_date(date.today().replace(year=date.today().year+1, month=2, day=1))
    assert t.filtre_date(date.today().replace(year=date.today().year+1, month=2, day=2)) == False
    assert t.filtre_date(date.today().replace(month=9, day=30)) == False

def test_chauffage(template, inscription):
    template.chauffage = []
    assert template.filtre_criteres(inscription) == True
    inscription.chauffage = ["bois"]
    assert template.filtre_criteres(inscription) == True

    template.chauffage = ["bois"]
    inscription.chauffage = None
    assert template.filtre_criteres(inscription) == False
    inscription.chauffage = ["bois"]
    assert template.filtre_criteres(inscription) == True

    template.chauffage = ["bois", "chaudiere"]
    inscription.chauffage = None
    assert template.filtre_criteres(inscription) == False
    inscription.chauffage = ["bois"]
    assert template.filtre_criteres(inscription) == True
    inscription.chauffage = ["chaudiere"]
    assert template.filtre_criteres(inscription) == True
    inscription.chauffage = ["chaudiere", "bois"]
    assert template.filtre_criteres(inscription) == True

def test_activites(template, inscription):
    template.activites = []
    assert template.filtre_criteres(inscription) == True
    inscription.activites = ["menage"]
    assert template.filtre_criteres(inscription) == True

    template.activites = ["menage"]
    inscription.activites = None
    assert template.filtre_criteres(inscription) == False
    inscription.activites = ["menage"]
    assert template.filtre_criteres(inscription) == True

    template.activites = ["bricolage"]
    inscription.activites = None
    assert template.filtre_criteres(inscription) == False
    inscription.activites = ["bricolage"]
    assert template.filtre_criteres(inscription) == True

    template.activites = ["jardinage"]
    inscription.activites = None
    assert template.filtre_criteres(inscription) == False
    inscription.activites = ["jardinage"]
    assert template.filtre_criteres(inscription) == True

    template.activites = ["activite_physique"]
    inscription.activites = None
    assert template.filtre_criteres(inscription) == False
    inscription.activites = ["sport"]
    assert template.filtre_criteres(inscription) == True

    template.activites = ["menage", "bricolage", "activite_physique"]
    inscription.activites = None
    assert template.filtre_criteres(inscription) == False
    inscription.activites = ["menage"]
    assert template.filtre_criteres(inscription) == True
    inscription.activites = ["bricolage"]
    assert template.filtre_criteres(inscription) == True
    inscription.activites = ["bricolage", "menage"]
    assert template.filtre_criteres(inscription) == True
    inscription.activites = ["bricolage", "menage", "sport"]
    assert template.filtre_criteres(inscription) == True

def test_enfants(template, inscription):
    template.enfants = None
    assert template.filtre_criteres(inscription) == True
    inscription.enfants = "oui"
    assert template.filtre_criteres(inscription) == True

    template.enfants = True
    inscription.enfants = "non"
    assert template.filtre_criteres(inscription) == False
    inscription.enfants = "oui"
    assert template.filtre_criteres(inscription) == True

    template.enfants = False
    inscription.enfants = "oui"
    assert template.filtre_criteres(inscription) == False
    inscription.enfants = "non"
    assert template.filtre_criteres(inscription) == True

def test_deplacement(template, inscription):
    template.deplacement = []
    assert template.filtre_criteres(inscription) == True
    inscription.deplacement = ["velo"]
    assert template.filtre_criteres(inscription) == True

    template.deplacement = ["velo"]
    inscription.deplacement = None
    assert template.filtre_criteres(inscription) == False
    inscription.deplacement = ["velo"]
    assert template.filtre_criteres(inscription) == True

    template.deplacement = ["velo", "tec"]
    inscription.deplacement = None
    assert template.filtre_criteres(inscription) == False
    inscription.deplacement = ["velo"]
    assert template.filtre_criteres(inscription) == True
    inscription.deplacement = ["tec"]
    assert template.filtre_criteres(inscription) == True
    inscription.deplacement = ["tec", "velo"]
    assert template.filtre_criteres(inscription) == True

def test_animaux_domestiques(template, inscription):
    template.animaux_domestiques = None
    assert template.filtre_criteres(inscription) == True
    inscription.animaux_domestiques = ["chat"]
    assert template.filtre_criteres(inscription) == True

    template.animaux_domestiques = True
    inscription.animaux_domestiques = None
    assert template.filtre_criteres(inscription) == False
    inscription.animaux_domestiques = ["chat"]
    assert template.filtre_criteres(inscription) == True

    template.animaux_domestiques = False
    inscription.animaux_domestiques = ["chat"]
    assert template.filtre_criteres(inscription) == False
    inscription.animaux_domestiques = None
    assert template.filtre_criteres(inscription) == True

def test_deux_criteres(template, inscription):
    template.animaux_domestiques = True
    template.deplacement = ['velo']

    assert template.filtre_criteres(inscription) == False
    inscription.animaux_domestiques = ["chat"]
    assert template.filtre_criteres(inscription) == False
    inscription.deplacement = ["velo"]
    assert template.filtre_criteres(inscription) == True


def test_vraie_vie(templates, inscription, db_session):
    templates = sorted(templates, key=lambda n: n.ordre)
    templates[1].animaux_domestiques = True
    templates[2].enfants = True
    templates[3].chauffage = ["bois"]

    db_session.add(inscription)
    db_session.add_all(templates)
    db_session.commit()

    nls = list(Newsletter.export(type_='hebdomadaire'))
    assert len(nls) == 1
    assert nls[0].newsletter_hebdo_template.id == templates[0].id
    db_session.add_all([NewsletterDB(nl) for nl in nls])
    db_session.commit()

    nls = list(Newsletter.export(type_='hebdomadaire', filter_already_sent=False))
    assert len(nls) == 1
    assert nls[0].newsletter_hebdo_template.id == templates[4].id

def test_indicateurs(template, inscription, db_session):
    template.indicateurs = None
    inscription.indicateurs = ["raep", "indice_atmo"]
    assert template.filtre_criteres(inscription) == True

    template.indicateurs = []
    assert template.filtre_criteres(inscription) == True

    template.indicateurs = inscription.indicateurs
    assert template.filtre_criteres(inscription) == True

    inscription.indicateurs = []
    assert template.filtre_criteres(inscription) == False

    template.indicateurs = []
    assert template.filtre_criteres(inscription) == True

    template.indicateurs = ["raep"]
    inscription.indicateurs = ["indice_atmo"]
    assert template.filtre_criteres(inscription) == False

    template.indicateurs = ["raep"]
    inscription.indicateurs = ["indice_atmo", "raep"]
    assert template.filtre_criteres(inscription) == True

    template.indicateurs = ["raep", "indice_atmo"]
    inscription.indicateurs = ["indice_atmo"]
    assert template.filtre_criteres(inscription) == False

    template.indicateurs = ["raep", "indice_atmo"]
    inscription.indicateurs = ["indice_atmo", "raep"]
    assert template.filtre_criteres(inscription) == True

def test_indicateurs_exclus(template, inscription, db_session):
    template.indicateurs_exclus = None
    inscription.indicateurs = ["raep", "indice_atmo"]
    assert template.filtre_criteres(inscription) == True

    template.indicateurs_exclus = []
    assert template.filtre_criteres(inscription) == True

    template.indicateurs_exclus = inscription.indicateurs
    assert template.filtre_criteres(inscription) == False

    inscription.indicateurs = []
    assert template.filtre_criteres(inscription) == True

    template.indicateurs_exclus = []
    assert template.filtre_criteres(inscription) == True

    template.indicateurs_exclus = ["raep"]
    inscription.indicateurs = ["indice_atmo"]
    assert template.filtre_criteres(inscription) == True

    template.indicateurs_exclus = ["raep"]
    inscription.indicateurs = ["indice_atmo", "raep"]
    assert template.filtre_criteres(inscription) == False

    template.indicateurs_exclus = ["raep", "indice_atmo"]
    inscription.indicateurs = ["indice_atmo"]
    assert template.filtre_criteres(inscription) == False

    template.indicateurs_exclus = ["raep", "indice_atmo"]
    inscription.indicateurs = ["indice_atmo", "raep"]
    assert template.filtre_criteres(inscription) == False

def test_meme_ordre(templates, inscription, db_session):
    for template in templates:
        if template.ordre >= 11:
            continue
        nl = Newsletter(newsletter_hebdo_template=template, inscription=inscription)
        db_session.add(NewsletterDB(nl))
    db_session.commit()
    inscription = Inscription.query.get(inscription.id)
    nlt = NewsletterHebdoTemplate.next_template(inscription)
    assert nlt.ordre == 11
    assert nlt.enfants == False

    inscription.enfants = 'oui'
    nlt = NewsletterHebdoTemplate.next_template(inscription)
    assert nlt.ordre == 11
    assert nlt.enfants == True

def test_meme_ordre_population_recoupe(templates, inscription, db_session):
    for template in templates:
        if template.ordre >= 12:
            continue
        nl = Newsletter(newsletter_hebdo_template=template, inscription=inscription)
        db_session.add(NewsletterDB(nl))
    db_session.commit()
    inscription = Inscription.query.get(inscription.id)
    nlt = NewsletterHebdoTemplate.next_template(inscription)
    nl = Newsletter(newsletter_hebdo_template=nlt, inscription=inscription)
    nl.date = date.today() - timedelta(days=1)
    db_session.add(NewsletterDB(nl))
    db_session.commit()

    nlt = NewsletterHebdoTemplate.next_template(inscription)
    assert nlt == None or nlt.ordre > 12
