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

def validate_choice(client, attribute_name, choice):
    response = client.post('/users/', json={
        'mail': 'lebo@tonvelo.com',
        'commune': {'code': '53130'},
        attribute_name: choice
    })
    assert response.status_code == 201
    assert response.json[attribute_name] == choice

def test_list_user(client, commune):
    listes = [
        'deplacement', 'activites', 'chauffage', 'animaux_domestiques',
        'connaissance_produit', 'population',  'indicateurs', 'indicateurs_media', 
        'recommandations', 'recommandations_media']
    for attribute_name in listes:
        attribute = getattr(User, attribute_name)
        one_of_validator = next(filter(lambda v: hasattr(v, 'choices'), attribute.inner.validators))
        choices = one_of_validator.choices

        validate_choice(client, attribute_name, [])
        validate_choice(client, attribute_name, [choices[0]])
        if len(choices) > 1:
            validate_choice(client, attribute_name, choices[0:2])
        
        response = client.post('/users/', json={
            'mail': 'lebo@tonvelo.com',
            attribute_name: ["cestnul!"]
        })
        assert response.status_code == 400

def test_enfants(client, commune):
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

    data = {
        'mail': 'lebo@tonvelo.com',
        "commune": {
            "code": "53130"
        }
    }
    response = client.post('/users/', json=data)
    assert response.status_code == 201

def test_get_user(commune, client):
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

def test_webpush_subscription_info(commune, client):
    data = {
        'mail': 'lebo@tonvelo.com',
        "commune": {
            "code": "53130"
        },
        "webpush_subscription_info": """{
            "endpoint": "https://updates.push.services.mozilla.com/push/v1/gAA...",
            "keys": { "auth": "k8J...", "p256dh": "BOr..." }
        }"""
    }
    response = client.post('/users/', json=data)
    assert response.status_code == 201
    jdata = json.loads(data['webpush_subscription_info'])
    rdata = json.loads(response.json['webpush_subscription_info'])
    assert jdata['endpoint'] == rdata['endpoint']
    assert jdata['keys'] == rdata['keys']