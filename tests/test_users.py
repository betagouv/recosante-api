from ecosante.inscription.models import Inscription
from ecosante.users.schemas import User
import json

def test_no_mail(client):
    data = {
        "commune": {
            "code": "53130"
        },
        'deplacement': ['velo', 'tec'],
        'activites': ['jardinage'],
        'population': ['pathologie_respiratoire', 'allergie_pollens']
    }
    response = client.post('/users/', json=data)
    assert response.status_code == 400

def test_bad_mail(client):
    data = {'mail': 'cestpasunmail'}
    response = client.post('/users/', json=data)
    assert response.status_code == 400

def test_same_mail(client):
    data = {
        'mail': 'lebo@tonvelo.com',
        "commune": {
            "code": "53130"
        },
    }
    response = client.post('/users/', json=data)
    assert response.status_code == 201
    response = client.post('/users/', json=data)
    assert response.status_code == 400
    assert 'mail' in response.json['errors']
    assert 'already used' in response.json['errors']['mail']

def test_default(client, commune):
    data = {
        'mail': 'lebo@tonvelo.com',
        "commune": {
            "code": "53130"
        },
    }
    response = client.post('/users/', json=data)
    assert response.status_code == 201

    inscriptions = Inscription.query.all()
    assert len(inscriptions) == 1
    inscription = inscriptions[0]

    for k, v in data.items():
        if k == 'commune':
            continue
        assert response.json[k] == v
        assert getattr(inscription, k) == v
    assert response.json['commune']['codes_postaux'] == ['53000']
    assert response.json['commune']['code'] == '53130'
    assert response.json['commune']['nom'] == 'Laval'

    assert inscription.commune.id == commune.id

def validate_choice(db_session, client, attribute_name, choice):
    db_session.execute('TRUNCATE inscription CASCADE')
    response = client.post('/users/', json={
        'mail': 'lebo@tonvelo.com',
        'commune': {'code': '53130'},
        attribute_name: choice
    })
    assert response.status_code == 201
    assert response.json[attribute_name] == choice

def test_list_user(db_session, client, commune_commited):
    listes = [
        'deplacement', 'activites', 'chauffage', 'animaux_domestiques',
        'connaissance_produit', 'population',  'indicateurs', 'indicateurs_media', 
        'recommandations', 'recommandations_media']
    for attribute_name in listes:
        attribute = getattr(User, attribute_name)
        one_of_validator = next(filter(lambda v: hasattr(v, 'choices'), attribute.inner.validators))
        choices = one_of_validator.choices

        validate_choice(db_session, client, attribute_name, [])
        validate_choice(db_session, client, attribute_name, [choices[0]])
        if len(choices) > 1 and attribute_name != 'recommandations':
            validate_choice(db_session, client, attribute_name, choices[0:2])
        
        response = client.post('/users/', json={
            'mail': 'lebo@tonvelo.com',
            attribute_name: ["cestnul!"]
        })
        assert response.status_code == 400

def test_enfants(client, commune_commited):
    data = {
        'mail': 'lebo@tonvelo.com',
        "commune": {
            "code": "53130"
        },
        "enfants": ["aucun"]
    }
    response = client.post('/users/', json=data)
    assert response.status_code == 201

    inscription = Inscription.query.filter_by(mail=data['mail']).first()
    assert inscription.enfants == data['enfants'][0]

def test_get_user(commune_commited, client):
    data = {
        'mail': 'lebo@tonvelo.com',
        "commune": {
            "code": "53130"
        },
    }
    response = client.post('/users/', json=data)
    assert response.status_code == 201

    uid = response.json["uid"]
    response = client.get(f'/users/{uid}')
    assert response.status_code == 200
    assert response.json['uid'] == uid
    assert response.json['mail'] == data['mail']

def test_webpush_subscriptions_info(commune_commited, client):
    data = {
        'mail': 'lebo@tonvelo.com',
        "commune": {
            "code": "53130"
        },
        "webpush_subscriptions_info": """{
            "endpoint": "https://updates.push.services.mozilla.com/push/v1/gAA...",
            "keys": { "auth": "k8J...", "p256dh": "BOr..." }
        }"""
    }
    response = client.post('/users/', json=data)
    assert response.status_code == 201
    jdata = json.loads(data['webpush_subscriptions_info'])
    inscription = Inscription.query.filter_by(mail='lebo@tonvelo.com').first()
    assert inscription.webpush_subscriptions_info[0]['endpoint'] == jdata['endpoint']
    assert inscription.webpush_subscriptions_info[0]['keys'] == jdata['keys']


def test_update_user_bad_uid(commune_commited, client):
    data = {
        'mail': 'lebo@tonvelo.com',
        "commune": {
            "code": "53130"
        }
    }
    response = client.post('/users/', json=data)
    assert response.status_code == 201
    uid = response.json['uid'] + 'bad'
    response = client.post(f'/users/{uid}', json=data)
    assert response.status_code == 404


def test_update_user(commune_commited, client):
    data = {
        'mail': 'lebo@tonvelo.com',
        "commune": {
            "code": "53130"
        }
    }
    response = client.post('/users/', json=data)
    assert response.status_code == 201
    inscription = Inscription.query.filter_by(mail=data['mail']).first()
    assert inscription is not None
    assert inscription.animaux_domestiques == None

    uid = response.json['uid']
    data['animaux_domestiques'] = ['chat']
    response = client.post(f'/users/{uid}', json=data)
    assert response.status_code == 200
    inscription = Inscription.query.filter_by(mail=data['mail']).first()
    assert inscription is not None
    assert inscription.animaux_domestiques == data['animaux_domestiques']

    response = client.post(f'/users/{uid}', json={"animaux_domestiques": ["aucun"]})
    assert response.status_code == 200
    inscription = Inscription.query.filter_by(mail=data['mail']).first()
    assert inscription is not None
    assert inscription.animaux_domestiques == ["aucun"]

def test_update_user_with_existing_email(commune_commited, client):
    data = {
        'mail': 'lebo@tonvelo.com',
        "commune": {
            "code": "53130"
        }
    }
    response = client.post('/users/', json=data)
    assert response.status_code == 201

    data['mail'] = 'letrebo@tonvelo.com'
    response = client.post('/users/', json=data)
    assert response.status_code == 201
    uid = response.json['uid']

    data['mail'] = 'lebo@tonvelo.com'
    response = client.post(f'/users/{uid}', json=data)
    assert response.status_code == 409