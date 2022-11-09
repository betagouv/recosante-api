import functools
from lib2to3.pytree import Base
from time import time
from flask import current_app, request, session, redirect, url_for, abort
from flask_rebar.authenticators.base import Authenticator
from flask_rebar import errors, messages
from jose import jwt
from hmac import compare_digest
import os

class BaseAuthenticator:
    def __init__(self) -> None:
        self.secret = os.getenv('AUTHENTICATOR_SECRET')
        if self.secret is None:
            raise Exception("AUTHENTICATOR_SECRET var env is required")

    def decode_token(self, encoded_token):
        return jwt.decode(encoded_token, self.secret, options={"require_exp": True, "leeway": 0})
    
    def make_token(self, payload, time_= None):
        time_ = time_ or time() + current_app.config['TEMP_AUTHENTICATOR_EXP_TIME']
        return jwt.encode(
            {
                **{'exp': time_},
                **payload
            },
            self.secret,
            'HS256'
        )

class APIAuthenticator(Authenticator, BaseAuthenticator):
    def make_token(self, uid, time_=None):
        return super().make_token({"uid": uid}, time_)

    def authenticate(self):
        encoded_token = request.args.get('token')
        if not encoded_token:
            raise errors.Unauthorized(messages.required_field_missing('token'))
        view_uid = request.view_args.get('uid')
        if not view_uid:
            raise errors.Unauthorized(messages.required_field_missing('uid'))
        try:
            decoded_token = self.decode_token(encoded_token)
        except (jwt.ExpiredSignatureError, jwt.JWTClaimsError, jwt.JWTError):
            raise errors.Unauthorized(messages.invalid_auth_token)

        if not compare_digest(view_uid, decoded_token.get('uid')):
            raise errors.Unauthorized(messages.invalid_auth_token)

class AdminAuthenticator(BaseAuthenticator):
    def __init__(self) -> None:
        super().__init__()
        self._set_admin_list()
        
    def _set_admin_list(self):
        if (admin_str := os.getenv('ADMINS_LIST')) != None:
            self.admin_emails = [v for v in admin_str.split(' ') if v]
            if len(self.admin_emails) < 1:
                raise Exception("ADMINS_LIST can not be empty")
        else:
            raise Exception("ADMINS_LIST var env is required")

    def make_token(self, email, time_=None):
        return super().make_token({"email": email}, time_)
    
    def authenticate(self):
        admin_email = session.get('admin_email')
        if admin_email is None:
            raise errors.Unauthorized(messages.missing_auth_token)
        elif admin_email not in self.admin_emails:
            raise errors.Unauthorized(messages.invalid_auth_token)

    def route(self, f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            admin_email = session.get('admin_email')
            if admin_email is None:
                return redirect(url_for('pages.admin_login'))
            elif admin_email not in self.admin_emails:
                abort(401)
            else:
                return f(*args, **kwargs)
        return wrapper