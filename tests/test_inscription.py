from ecosante.inscription.models import Inscription

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