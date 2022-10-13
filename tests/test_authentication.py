from ecosante.utils.authenticator import APIAuthenticator, AdminAuthenticator
from time import time
from jose import jwt
import os
import pytest
from flask import session
from werkzeug.exceptions import HTTPException
from ecosante.extensions import admin_authenticator

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
    os.environ.pop('ADMINS_LIST')
    with pytest.raises(Exception) as exc_info:
        admin_authenticator_test = AdminAuthenticator()
        @admin_authenticator_test.route
        def f():
            pass
    assert str(exc_info.value) == "ADMINS_LIST var env is required"


def test_empty_admins_list_env():
    os.environ['ADMINS_LIST'] = ""
    with pytest.raises(Exception) as exc_info:
        admin_authenticator._set_admin_list()
        @admin_authenticator.route
        def f():
            pass
    assert str(exc_info.value) == "ADMINS_LIST can not be empty"


def test_one_email_in_admins_list_env():
    os.environ['ADMINS_LIST'] = "test@test.com"
    admin_authenticator._set_admin_list()
    assert admin_authenticator.admin_emails == ["test@test.com"]


def test_two_emails_in_admins_list_env():
    os.environ['ADMINS_LIST'] = "test@test.com test2@pouet.com"
    admin_authenticator._set_admin_list()
    assert admin_authenticator.admin_emails == ["test@test.com", "test2@pouet.com"]


def test_no_admin_email_in_session(app):
    os.environ['ADMINS_LIST'] = 'test@test.com'
    admin_authenticator._set_admin_list()
    with app.test_request_context('/'):
        @admin_authenticator.route
        def f():
            pass
        
        response = f()
    assert response.location == '/admin_login/'


def test_unknown_email_in_session(app):
    os.environ['ADMINS_LIST'] = 'test@test.com'
    admin_authenticator._set_admin_list()
    with app.test_request_context('/'):
        session['admin_email'] = 'unknown@email.com'
        @admin_authenticator.route
        def f():
            pass
        with pytest.raises(HTTPException) as exc_info:
            f()
    assert exc_info.value.code == 401


def test_authorized_email_in_session(app):
    os.environ['ADMINS_LIST'] = 'test@test.com second@autredomaine.com'
    admin_authenticator._set_admin_list()
    with app.test_request_context('/'):
        session['admin_email'] = 'test@test.com'
        @admin_authenticator.route
        def f():
            return session.get('admin_email')
        assert f() == 'test@test.com'

        session['admin_email'] = 'second@autredomaine.com'
        assert f() == 'second@autredomaine.com'


def test_authenticate_no_token(client):
    os.environ['ADMINS_LIST'] = 'test@test.com second@autredomaine.com'
    admin_authenticator._set_admin_list()
    response = client.get('/authenticate')
    assert response.status_code == 401


def test_authenticate_bad_token(client):
    os.environ['ADMINS_LIST'] = 'test@test.com second@autredomaine.com'
    admin_authenticator._set_admin_list()
    response = client.get('/authenticate?token=bad_token')
    assert response.status_code == 401


def test_authenticate_bad_email(client):
    os.environ['ADMINS_LIST'] = 'test@test.com second@autredomaine.com'
    admin_authenticator._set_admin_list()
    token = admin_authenticator.make_token('bad@email.com')
    response = client.get(f'/authenticate?token={token}')
    assert response.status_code == 401


def test_expired_admin_link(client):
    os.environ['ADMINS_LIST'] = 'test@test.com second@autredomaine.com'
    admin_authenticator._set_admin_list()
    token = admin_authenticator.make_token('test@test.com', time() - 86400)
    response = client.get(f'/authenticate?token={token}')
    assert response.status_code == 401

def test_good_authentication(app):
    os.environ['ADMINS_LIST'] = 'test@test.com second@autredomaine.com'
    admin_authenticator._set_admin_list()
    token = admin_authenticator.make_token('test@test.com')
    with app.test_client() as c:
        rv = c.get(f'/authenticate?token={token}')
        assert 'admin_email' in session
        assert session['admin_email'] == 'test@test.com'