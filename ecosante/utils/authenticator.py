from datetime import datetime, timedelta
from flask import request
from flask_rebar.authenticators.base import Authenticator
from flask_rebar import errors, messages
from jose import jwt
from werkzeug.security import safe_str_cmp
import os

class TempAuthenticator(Authenticator):
    def __init__(self) -> None:
        self.secret = os.getenv('AUTHENTICATOR_SECRET')
        if self.secret is None:
            raise Exception("AUTHENTICATOR_SECRET var env is required")

    def authenticate(self):
        encoded_token = request.args.get('token')
        if not encoded_token:
            raise errors.Unauthorized(messages.required_field_missing)
        view_uid = request.view_args.get('uid')
        if not view_uid:
            raise errors.Unauthorized(messages.required_field_missing)
        try:
            decoded_token = jwt.decode(encoded_token, self.secret)
        except jwt.ExpiredSignatureError:
            raise errors.Unauthorized(messages.invalid_auth_token)
        except jwt.JWTClaimsError:
            raise Exception(messages.invalid_auth_token)
        except jwt.JWTError:
            raise Exception(messages.invalid_auth_token)

        if not safe_str_cmp(view_uid, decoded_token.get('uid')):
            raise errors.Unauthorized(messages.invalid_auth_token)
    
    def make_token(self, uid):
        return jwt.encode(
            {
                'exp': datetime.now() + timedelta(minutes=30),
                'uid': uid
            },
            self.secret,
            'HS256'
        )
