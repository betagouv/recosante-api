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
    assert inscription.population == ['pathologie_respiratoire', 'allergie_pollens']

def test_partial_updates(client):
    mail, uid = premiere_etape(client)

    data = {
        'ville_insee': '53130',
        'deplacement': ['velo', 'tec'],
        'activites': ['jardinage'],
        'population': ['pathologie_respiratoire', 'allergie_pollens']
    }

    for k, v in data.items():
        response = client.post(f'/inscription/{uid}/', data={k: v})
        assert response.status_code == 200
        assert response.json[k] == v

    data = {"mail": mail}
    response = client.post(f'/inscription/{uid}/', data={k: v})
    assert response.status_code == 200
    assert response.json[k] == v

def test_errors(client):
    _mail, uid = premiere_etape(client)

    response = client.post(f'/inscription/{uid}/', data={"ville_insee": "13"}, headers={"Accept": "application/json"})
    assert response.status_code == 400
    assert 'ville_insee' in response.json

def test_json(client):
    data = {'mail': f'dodo-{int(datetime.timestamp(datetime.now()))}@beta.gouv.fr'}
    response = client.post('/inscription/premiere-etape', json=data)
    assert response.status_code == 201

    uid = response.json['uid']
    data = {
        'ville_insee': '53130',
        'deplacement': ['velo', 'tec'],
        'activites': ['jardinage'],
        'population': ['pathologie_respiratoire', 'allergie_pollens']
    }

    for k, v in data.items():
        response = client.post(f'/inscription/{uid}/', json={k: v})
        assert response.status_code == 200
        assert response.json[k] == v
    assert response.json['ville_nom'] == 'Laval'
    assert response.json['ville_codes_postaux'] == ['53000']

def test_animaux(client):
    _mail, uid = premiere_etape(client)

    response = client.post(f'/inscription/{uid}/', json={"animaux_domestiques": ["chat"]})
    assert response.json['animaux_domestiques'] == ["chat"]
    response = client.post(f'/inscription/{uid}/', json={"animaux_domestiques": ["chien"]})
    assert response.json['animaux_domestiques'] == ["chien"]
    response = client.post(f'/inscription/{uid}/', json={"animaux_domestiques": ["chat", "chien"]})
    assert response.json['animaux_domestiques'] == ["chat", "chien"]
    response = client.post(f'/inscription/{uid}/', json={"animaux_domestiques": []})
    assert response.json['animaux_domestiques'] == []

def test_chauffage(client):
    _mail, uid = premiere_etape(client)

    response = client.post(f'/inscription/{uid}/', json={"chauffage": ["bois"]})
    assert response.json['chauffage'] == ["bois"]
    response = client.post(f'/inscription/{uid}/', json={"chauffage": ["chaudiere"]})
    assert response.json['chauffage'] == ["chaudiere"]
    response = client.post(f'/inscription/{uid}/', json={"chauffage": ["appoint"]})
    assert response.json['chauffage'] == ["appoint"]
    response = client.post(f'/inscription/{uid}/', json={"chauffage": ["bois", "chaudiere", "appoint"]})
    assert response.json['chauffage'] == ["bois", "chaudiere", "appoint"]
    response = client.post(f'/inscription/{uid}/', json={"chauffage": []})
    assert response.json['chauffage'] == []

def test_connaissace_produit(client):
    _mail, uid = premiere_etape(client)

    choices = ['medecin', 'association', 'reseaux_sociaux', 'publicite', 'ami', 'autrement']

    for choice in choices:
        response = client.post(f'/inscription/{uid}/', json={"connaissance_produit": [choice]})
        assert response.json['connaissance_produit'] == [choice]

    response = client.post(f'/inscription/{uid}/', json={"connaissance_produit": ["medecin", "association"]})
    assert response.json['connaissance_produit'] == ["medecin", "association"]
    response = client.post(f'/inscription/{uid}/', json={"connaissance_produit": []})
    assert response.json['connaissance_produit'] == []

def test_population(client):
    _mail, uid = premiere_etape(client)

    choices = ['pathologie_respiratoire', 'allergie_pollens', 'aucun']

    for choice in choices:
        response = client.post(f'/inscription/{uid}/', json={"population": [choice]})
        assert response.json['population'] == [choice]

    response = client.post(f'/inscription/{uid}/', json={"population": ["pathologie_respiratoire", "allergie_pollens"]})
    assert response.json['population'] == ["pathologie_respiratoire", "allergie_pollens"]
    response = client.post(f'/inscription/{uid}/', json={"population": []})
    assert response.json['population'] == []

def test_enfants(client):
    _mail, uid = premiere_etape(client)

    for choice in ["oui", "non", "aucun", None]:
        response = client.post(f'/inscription/{uid}/', json={"enfants": choice})
        assert response.status_code == 200
        assert response.json['enfants'] == choice

def test_deplacement(client):
    _mail, uid = premiere_etape(client)

    for choice in ["velo", "tec", "voiture", "aucun"]:
        response = client.post(f'/inscription/{uid}/', json={"deplacement": [choice]})
        assert response.status_code == 200
        assert response.json['deplacement'] == [choice]

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

def test_recommandations_field(db_session, client):
    mail, uid = premiere_etape(client)

    data = {
        "recommandations": ["hebdomadaire"]
    }
    response = client.post(f'/inscription/{uid}/', data=data)
    data_tester(response, data)
    response = client.get(f'/inscription/{uid}/', data=data)
    data_tester(response, data)

    data = {
        "recommandations": ["quotidien"]
    }
    response = client.post(f'/inscription/{uid}/', data=data)
    data_tester(response, data)
    response = client.get(f'/inscription/{uid}/', data=data)
    data_tester(response, data)

    data = {
        "recommandations": ["faux"]
    }
    response = client.post(f'/inscription/{uid}/', data=data)
    assert response.status_code == 400

def test_notifications_field(db_session, client):
    mail, uid = premiere_etape(client)

    data = {
        "notifications": ["aucun"]
    }
    response = client.get(f'/inscription/{uid}/', data=data)
    response = client.post(f'/inscription/{uid}/', data=data)
    data_tester(response, data)
    response = client.get(f'/inscription/{uid}/', data=data)
    data_tester(response, data)

    data = {
        "notifications": ["quotidien"]
    }
    response = client.post(f'/inscription/{uid}/', data=data)
    data_tester(response, data)
    response = client.get(f'/inscription/{uid}/', data=data)
    data_tester(response, data)

    data = {
        "notifications": ["faux"]
    }
    response = client.post(f'/inscription/{uid}/', data=data)
    assert response.status_code == 400

def test_make_new_value_webpush_subscriptions_info():
    assert Inscription.make_new_value_webpush_subscriptions_info([], "fifi") == None
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

    updated_value = Inscription.make_new_value_webpush_subscriptions_info(old_value, json.dumps(new_value))
    assert len(updated_value) == 2
    assert any([v == old_value[0] for v in updated_value])
    assert any([v == new_value for v in updated_value])

    updated_value = Inscription.make_new_value_webpush_subscriptions_info(old_value, json.dumps([new_value]))
    assert len(updated_value) == 2
    assert any([v == old_value[0] for v in updated_value])
    assert any([v == new_value for v in updated_value])

    old_value.append(new_value)
    updated_value = Inscription.make_new_value_webpush_subscriptions_info(old_value, json.dumps(new_value))
    assert len(updated_value) == 2
    assert any([v == old_value[0] for v in updated_value])
    assert any([v == new_value for v in updated_value])

    updated_value = Inscription.make_new_value_webpush_subscriptions_info(old_value, json.dumps([new_value]))
    assert len(updated_value) == 2
    assert any([v == old_value[0] for v in updated_value])
    assert any([v == new_value for v in updated_value])
