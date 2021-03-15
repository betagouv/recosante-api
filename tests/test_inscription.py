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
        "allergie_pollens": "true",
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
        'population': ['pathologie_respiratoire', 'allergie_pollens']
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
    assert inscription.population == ['pathologie_respiratoire', 'allergie_pollens']

def test_partial_updates(client):
    _mail, uid = premiere_etape(client)

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

def test_changement_ville(client):
    _mail, uid = premiere_etape(client)
    response = client.post(f'/inscription/{uid}/', json={"ville_insee": "53130"})
    assert response.status_code == 200
    assert response.json['ville_nom'] == 'Laval'

    response = client.post(f'/inscription/{uid}/', json={"ville_insee": "53144"})
    assert response.status_code == 200
    assert response.json['ville_nom'] == 'Marcillé-la-Ville'
