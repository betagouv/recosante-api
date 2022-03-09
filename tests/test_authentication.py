from ecosante.utils.authenticator import TempAuthenticator
from time import time
from jose import jwt


def test_no_token(client):
    response = client.get('/users/uid1')
    assert response.status_code == 401
    assert response.json['message'] == 'Required field missing: token'

def test_bad_token(client):
    response = client.get('/users/uid1?token=pouet')
    assert response.status_code == 401
    assert response.json['message'] == 'Invalid authentication.'

def test_expired_token(client):
    authenticator = TempAuthenticator()
    token = authenticator.make_token('monuid', time() - 60)
    response = client.get(f'/users/uid1?token={token}')
    assert response.status_code == 401
    assert response.json['message'] == 'Invalid authentication.'

def test_no_expired_token(client):
    authenticator = TempAuthenticator()
    token = jwt.encode({'uid': 'monuid'}, authenticator.secret, 'HS256')
    response = client.get(f'/users/uid1?token={token}')
    assert response.status_code == 401
    assert response.json['message'] == 'Invalid authentication.'

def test_mauvais_uid(client):
    authenticator = TempAuthenticator()
    token = authenticator.make_token('monuid')
    response = client.get(f'/users/uid1?token={token}')
    assert response.status_code == 401
    assert response.json['message'] == 'Invalid authentication.'

def test_bon_uid(client, inscription, db_session):
    db_session.add(inscription)
    db_session.commit()
    authenticator = TempAuthenticator()
    token = authenticator.make_token(inscription.uid)
    response = client.get(f'/users/{inscription.uid}?token={token}')
    assert response.status_code == 200
