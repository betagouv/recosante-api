from ecosante.inscription.models import Inscription
from datetime import datetime

def test_inscription(client):
    data = {
        'ville_entree': 'Marcillé-la-ville',
        'mail': 'lala@example.com',
        'diffusion': 'mail',
        'frequence': 'quotidien',
        'rgpd': 'true'
    }
    response = client.post('/inscription/', data=data)
    assert response.status_code == 302
    assert response.location == 'http://localhost:5000/inscription/personnalisation'

    data = {
        "deplacement": "velo",
        "activites": ["jardinage"],
        "enfants": "true",
        "pathologie_respiratoire": "true",
        "allergie_pollen": "true",
    }
    response = client.post('/inscription/personnalisation', data=data)
    assert response.status_code == 302
    assert response.location == 'http://localhost:5000/inscription/reussie'

def premiere_etape(client):
    mail = f'dodo-{datetime.timestamp(datetime.now())}@example.com'
    data = {'mail': mail}
    response = client.post('/inscription/premiere-etape', data=data)
    assert response.status_code == 201
    return mail, response.json['uid']

def test_inscription_multi_etapes(client):
    mail, uid = premiere_etape(client)

    data = {
        'ville_insee': '53130',
        'deplacement': ['velo', 'tec'],
        'activites': ['jardinage'],
        'pathologie_respiratoire': False,
        'allergie_pollen': True
    }
    response = client.post(f'/inscription/{uid}/', data=data)
    assert response.status_code == 200
    for k, v in data.items():
        assert response.json[k] == v

    inscription = Inscription.query.filter_by(uid=uid).first()

    assert inscription
    assert inscription.mail == mail
    assert inscription.diffusion == 'mail'
    assert inscription.frequence == 'quotidien'
    assert inscription.ville_insee == '53130'
    assert inscription.deplacement == ['velo', 'tec']
    assert inscription.activites == ['jardinage']
    assert inscription.pathologie_respiratoire == False
    assert inscription.allergie_pollen == True

def test_partial_updates(client):
    _mail, uid = premiere_etape(client)

    data = {
        'ville_insee': '53130',
        'deplacement': ['velo', 'tec'],
        'activites': ['jardinage'],
        'pathologie_respiratoire': False,
        'allergie_pollen': True
    }

    for k, v in data.items():
        response = client.post(f'/inscription/{uid}/', data={k: v})
        assert response.status_code == 200
        assert response.json[k] == v

def test_errors(client):
    _mail, uid = premiere_etape(client)

    response = client.post(f'/inscription/{uid}/', data={"ville_insee": "13"}, headers={"Accept": "application/json"})
    assert response.status_code == 400
    assert 'ville_insee' in response.json

def test_json(client):
    data = {'mail': f'dodo-{datetime.timestamp(datetime.now())}@example.com'}
    response = client.post('/inscription/premiere-etape', json=data)
    assert response.status_code == 201

    uid = response.json['uid']
    data = {
        'ville_insee': '53130',
        'deplacement': ['velo', 'tec'],
        'activites': ['jardinage'],
        'pathologie_respiratoire': False,
        'allergie_pollen': True
    }

    for k, v in data.items():
        response = client.post(f'/inscription/{uid}/', json={k: v})
        assert response.status_code == 200
        assert response.json[k] == v