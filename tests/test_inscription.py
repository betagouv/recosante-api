import json
from ecosante.inscription.models import Inscription
from datetime import date, datetime, timedelta

def premiere_etape(client):
    mail = f'dodo-{int(datetime.timestamp(datetime.now()))}@beta.gouv.fr'
    data = {'mail': mail}
    response = client.post('/inscription/premiere-etape', data=data)
    assert response.status_code == 201
    return mail, response.json['uid']

def data_tester(response, data):
    assert response.status_code == 200
    for k, v in data.items():
        assert response.json[k] == v

def test_inscription_multi_etapes(client):
    mail, uid = premiere_etape(client)

    data = {
        'ville_insee': '53130',
        'deplacement': ['velo', 'tec'],
        'activites': ['jardinage'],
        'population': ['pathologie_respiratoire', 'allergie_pollens']
    }
    response = client.post(f'/inscription/{uid}/', data=data)
    data_tester(response, data)

    inscription = Inscription.query.filter_by(uid=uid).first()

    assert inscription
    assert inscription.mail == mail
    assert inscription.diffusion == 'mail'
    assert inscription.frequence == 'quotidien'
    assert inscription.ville_insee == '53130'
    assert inscription.deplacement == ['velo', 'tec']
    assert inscription.activites == ['jardinage']

def test_errors(client):
    _mail, uid = premiere_etape(client)

    response = client.post(f'/inscription/{uid}/', data={"ville_insee": "13"}, headers={"Accept": "application/json"})
    assert response.status_code == 400
    assert 'ville_insee' in response.json

def test_changement_ville(client):
    _mail, uid = premiere_etape(client)
    response = client.post(f'/inscription/{uid}/', json={"ville_insee": "53130"})
    assert response.status_code == 200
    assert response.json['ville_nom'] == 'Laval'

    response = client.post(f'/inscription/{uid}/', json={"ville_insee": "53144"})
    assert response.status_code == 200
    assert response.json['ville_nom'] == 'Marcillé-la-Ville'


def test_query_inactive_accounts(db_session):
    i = Inscription(mail='test@test.com')
    db_session.add(i)
    db_session.commit()
    assert Inscription.query_inactive_accounts().count() == 0

    i = Inscription(mail='test1@test.com', deactivation_date=(date.today() - timedelta(days=29)))
    db_session.add(i)
    db_session.commit()
    assert Inscription.query_inactive_accounts().count() == 0

    i = Inscription(mail='test2@test.com', deactivation_date=(date.today() - timedelta(days=31)))
    db_session.add(i)
    db_session.commit()
    assert Inscription.query_inactive_accounts().count() == 1

def test_deactivate_accounts(db_session):
    i = Inscription(mail='test@test.com')
    db_session.add(i)
    i = Inscription(mail='test1@test.com', deactivation_date=(date.today() - timedelta(days=29)))
    db_session.add(i)
    i = Inscription(mail='test2@test.com', deactivation_date=(date.today() - timedelta(days=31)))
    db_session.add(i)
    i = Inscription(mail=None, deactivation_date=(date.today() - timedelta(days=31)))
    db_session.add(i)
    db_session.commit()

    assert db_session.query(Inscription).count() == 4
    assert db_session.query(Inscription).filter(Inscription.mail==None).count() == 1
    assert Inscription.deactivate_accounts() == 1
    assert db_session.query(Inscription).filter(Inscription.mail==None).count() == 2


def test_partial_update_same_mail(db_session, client):
    i = Inscription(mail='test@test.com')
    db_session.add(i)
    db_session.commit()

    mail, uid = premiere_etape(client)

    data = {
        'mail': 'test@test.com',
    }
    response = client.post(f'/inscription/{uid}/', data=data)
    assert response.status_code == 400


def test_add_webpush_subscriptions_info_bad_json(inscription):
    inscription.add_webpush_subscriptions_info("fifi")
    assert len(inscription.webpush_subscriptions_info) == 0


def test_make_new_value_webpush_subscriptions_info(inscription):
    old_value = [
       {
           "endpoint": "https://recosante.beta.gouv.fr/dashboard/",
            "keys": {
                "p256dh": "BIPUL12DLfytvTajnryr2PRdAgXS3HGKiLqndGcJGabyhHheJYlNGCeXl1dn18gSJ1WAkAPIxr4gK0_dQds4yiI=",
                "auth": "FPssNDTKnInHVndSTdbKFw=="
            }
        }
    ]
    new_value = {
           "endpoint": "https://recosante.beta.gouv.fr/dashboard/",
            "keys": {
                "p256dh": "BIPUL12DLfytvTajnryr2PRdAgXS3HGKiLqndGcJGabyhHheJYlNGCeXl1dn18gSJ1WAkAPIxr4gK0_dQds4yiI=",
                "auth": "new_value_FPssNDTKnInHVndSTdbKFw=="
            }
        }
    # We first add old value, and check its added
    inscription.webpush_subscriptions_info = json.dumps(old_value)
    assert len(inscription.webpush_subscriptions_info) == 1
    # Then we add old value, and check we have the old one and the new one
    inscription.webpush_subscriptions_info = json.dumps(new_value)
    assert len(inscription.webpush_subscriptions_info) == 2
    assert any([v.data == old_value[0] for v in inscription.webpush_subscriptions_info])
    assert any([v.data == new_value for v in inscription.webpush_subscriptions_info])

    # Let's try to add another time this new_value and check we still have only 2 values
    inscription.add_webpush_subscriptions_info = json.dumps(new_value)
    assert len(inscription.webpush_subscriptions_info) == 2
    assert any([v.data == old_value[0] for v in inscription.webpush_subscriptions_info])
    assert any([v.data == new_value for v in inscription.webpush_subscriptions_info])
