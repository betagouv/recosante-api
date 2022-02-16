from sqlalchemy.sql.sqltypes import Date
from ecosante.newsletter.models import Newsletter, NewsletterDB, NewsletterHebdoTemplate
from datetime import date, timedelta
from psycopg2.extras import DateRange

def test_get_templates(templates):
    last_t = None
    for t in NewsletterHebdoTemplate.get_templates():
        if last_t:
            assert last_t.ordre < t.ordre
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

def test_chauffage(templates, inscription):
    t = templates[0]
    t.chauffage = []
    assert t.filtre_criteres(inscription) == True
    inscription.chauffage = ["bois"]
    assert t.filtre_criteres(inscription) == True

    t.chauffage = ["bois"]
    inscription.chauffage = None
    assert t.filtre_criteres(inscription) == False
    inscription.chauffage = ["bois"]
    assert t.filtre_criteres(inscription) == True

    t.chauffage = ["bois", "chaudiere"]
    inscription.chauffage = None
    assert t.filtre_criteres(inscription) == False
    inscription.chauffage = ["bois"]
    assert t.filtre_criteres(inscription) == True
    inscription.chauffage = ["chaudiere"]
    assert t.filtre_criteres(inscription) == True
    inscription.chauffage = ["chaudiere", "bois"]
    assert t.filtre_criteres(inscription) == True

def test_activites(templates, inscription):
    t = templates[0]
    t.activites = []
    assert t.filtre_criteres(inscription) == True
    inscription.activites = ["menage"]
    assert t.filtre_criteres(inscription) == True

    t.activites = ["menage"]
    inscription.activites = None
    assert t.filtre_criteres(inscription) == False
    inscription.activites = ["menage"]
    assert t.filtre_criteres(inscription) == True

    t.activites = ["menage", "bricolage"]
    inscription.activites = None
    assert t.filtre_criteres(inscription) == False
    inscription.activites = ["menage"]
    assert t.filtre_criteres(inscription) == True
    inscription.activites = ["bricolage"]
    assert t.filtre_criteres(inscription) == True
    inscription.activites = ["bricolage", "menage"]
    assert t.filtre_criteres(inscription) == True

def test_enfants(templates, inscription):
    t = templates[0]
    t.enfants = None
    assert t.filtre_criteres(inscription) == True
    inscription.enfants = "oui"
    assert t.filtre_criteres(inscription) == True

    t.enfants = True
    inscription.enfants = "non"
    assert t.filtre_criteres(inscription) == False
    inscription.enfants = "oui"
    assert t.filtre_criteres(inscription) == True

    t.enfants = False
    inscription.enfants = "oui"
    assert t.filtre_criteres(inscription) == False
    inscription.enfants = "non"
    assert t.filtre_criteres(inscription) == True

def test_deplacement(templates, inscription):
    t = templates[0]
    t.deplacement = []
    assert t.filtre_criteres(inscription) == True
    inscription.deplacement = ["velo"]
    assert t.filtre_criteres(inscription) == True

    t.deplacement = ["velo"]
    inscription.deplacement = None
    assert t.filtre_criteres(inscription) == False
    inscription.deplacement = ["velo"]
    assert t.filtre_criteres(inscription) == True

    t.deplacement = ["velo", "tec"]
    inscription.deplacement = None
    assert t.filtre_criteres(inscription) == False
    inscription.deplacement = ["velo"]
    assert t.filtre_criteres(inscription) == True
    inscription.deplacement = ["tec"]
    assert t.filtre_criteres(inscription) == True
    inscription.deplacement = ["tec", "velo"]
    assert t.filtre_criteres(inscription) == True

def test_animaux_domestiques(templates, inscription):
    t = templates[0]
    t.animaux_domestiques = None
    assert t.filtre_criteres(inscription) == True
    inscription.animaux_domestiques = ["chat"]
    assert t.filtre_criteres(inscription) == True

    t.animaux_domestiques = True
    inscription.animaux_domestiques = None
    assert t.filtre_criteres(inscription) == False
    inscription.animaux_domestiques = ["chat"]
    assert t.filtre_criteres(inscription) == True

    t.animaux_domestiques = False
    inscription.animaux_domestiques = ["chat"]
    assert t.filtre_criteres(inscription) == False
    inscription.animaux_domestiques = None
    assert t.filtre_criteres(inscription) == True

def test_deux_criteres(templates, inscription):
    t = templates[0]
    t.animaux_domestiques = True
    t.deplacement = ['velo']

    assert t.filtre_criteres(inscription) == False
    inscription.animaux_domestiques = ["chat"]
    assert t.filtre_criteres(inscription) == False
    inscription.deplacement = ["velo"]
    assert t.filtre_criteres(inscription) == True


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
    assert nls[0].newsletter_hebdo_template.id == templates[-1].id
