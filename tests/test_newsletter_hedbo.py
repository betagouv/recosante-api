from ecosante.newsletter.models import Newsletter, NewsletterDB, NewsletterHebdoTemplate

def test_get_templates(templates):
    last_t = None
    for t in NewsletterHebdoTemplate.get_templates():
        if last_t:
            assert last_t.ordre < t.ordre
        last_t = t

def test_next_template_first(db_session, inscription, templates):
    assert NewsletterHebdoTemplate.next_template(inscription) != None

def test_next_template(db_session, inscription, templates):
    template = templates[1]
    nl = Newsletter(inscription=inscription, newsletter_hebdo_template=template)
    db_session.add(NewsletterDB(nl))

    assert NewsletterHebdoTemplate.next_template(inscription).ordre > template.ordre 

def test_next_template_last(db_session, inscription, templates):
    template = templates[0]
    nl = Newsletter(inscription=inscription, newsletter_hebdo_template=template)
    db_session.add(NewsletterDB(nl))

    assert NewsletterHebdoTemplate.next_template(inscription) == None

def test_hebdo_notification_web(db_session, inscription, templates):
    inscription.indicateurs_media = ['notification_web']
    db_session.add(inscription)
    db_session.commit()

    assert len(list(Newsletter.export(type_='hebdomadaire'))) == 1
