from ecosante.utils.authenticator import APIAuthenticator, AdminAuthenticatorDecorator
from time import time
from jose import jwt
import os
import pytest
from flask import session
from werkzeug.exceptions import HTTPException

def test_no_token(client):
    response = client.get('/users/uid1')
    assert response.status_code == 401
    assert response.json['message'] == 'Required field missing: token'

def test_bad_token(client):
    response = client.get('/users/uid1?token=pouet')
    assert response.status_code == 401
    assert response.json['message'] == 'Invalid authentication.'

def test_expired_token(client):
    authenticator = APIAuthenticator()
    token = authenticator.make_token('monuid', time() - 60)
    response = client.get(f'/users/uid1?token={token}')
    assert response.status_code == 401
    assert response.json['message'] == 'Invalid authentication.'

def test_no_expired_token(client):
    authenticator = APIAuthenticator()
    token = jwt.encode({'uid': 'monuid'}, authenticator.secret, 'HS256')
    response = client.get(f'/users/uid1?token={token}')
    assert response.status_code == 401
    assert response.json['message'] == 'Invalid authentication.'

def test_mauvais_uid(client):
    authenticator = APIAuthenticator()
    token = authenticator.make_token('monuid')
    response = client.get(f'/users/uid1?token={token}')
    assert response.status_code == 401
    assert response.json['message'] == 'Invalid authentication.'

def test_bon_uid(client, inscription, db_session):
    db_session.add(inscription)
    db_session.commit()
    authenticator = APIAuthenticator()
    token = authenticator.make_token(inscription.uid)
    response = client.get(f'/users/{inscription.uid}?token={token}')
    assert response.status_code == 200

def test_no_admins_list_env():
    os.unsetenv('ADMINS_LIST')
    with pytest.raises(Exception) as exc_info:
        @AdminAuthenticatorDecorator
        def f():
            pass
    assert str(exc_info.value) == "ADMINS_LIST var env is required"

def test_empty_admins_list_env():
    os.environ['ADMINS_LIST'] = ""
    with pytest.raises(Exception) as exc_info:
        @AdminAuthenticatorDecorator
        def f():
            pass
    assert str(exc_info.value) == "ADMINS_LIST can not be empty"


def test_one_email_in_admins_list_env():
    os.environ['ADMINS_LIST'] = "test@test.com"
    admin_decorator = AdminAuthenticatorDecorator(None)
    assert admin_decorator.admin_emails == ["test@test.com"]


def test_two_emails_in_admins_list_env():
    os.environ['ADMINS_LIST'] = "test@test.com test2@pouet.com"
    admin_decorator = AdminAuthenticatorDecorator(None)
    assert admin_decorator.admin_emails == ["test@test.com", "test2@pouet.com"]

def test_no_admin_email_in_session(app):
    os.environ['ADMINS_LIST'] = 'test@test.com'
    with app.test_request_context('/'):
        @AdminAuthenticatorDecorator
        def f():
            pass
        
        response = f()
    assert response.location == '/login'

def test_unknown_email_in_session(app):
    os.environ['ADMINS_LIST'] = 'test@test.com'
    with app.test_request_context('/'):
        session['admin_email'] = 'unknown@email.com'
        @AdminAuthenticatorDecorator
        def f():
            pass
        with pytest.raises(HTTPException) as exc_info:
            f()
    assert exc_info.value.code == 401

def test_authorized_email_in_session(app):
    os.environ['ADMINS_LIST'] = 'test@test.com second@autredomaine.com'
    with app.test_request_context('/'):
        session['admin_email'] = 'test@test.com'
        @AdminAuthenticatorDecorator
        def f():
            return session.get('admin_email')
        assert f() == 'test@test.com'

        session['admin_email'] = 'second@autredomaine.com'
        assert f() == 'second@autredomaine.com'
