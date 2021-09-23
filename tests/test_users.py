from ecosante.inscription.models import Inscription
from ecosante.users.schemas import User
from itertools import permutations


def test_no_mail(client):
    data = {
        "ville": {
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
        'deplacement': ['velo', 'tec'],
        'activites': ['jardinage'],
        'population': ['pathologie_respiratoire', 'allergie_pollens'],
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
        'deplacement', 'activites', 'enfants', 'chauffage', 'animaux_domestiques',
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