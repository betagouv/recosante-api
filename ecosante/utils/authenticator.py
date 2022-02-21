from time import time
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
            raise errors.Unauthorized(messages.required_field_missing('token'))
        view_uid = request.view_args.get('uid')
        if not view_uid:
            raise errors.Unauthorized(messages.required_field_missing('uid'))
        try:
            decoded_token = jwt.decode(encoded_token, self.secret, options={"require_exp": True, "leeway": 0})
        except (jwt.ExpiredSignatureError, jwt.JWTClaimsError, jwt.JWTError):
            raise errors.Unauthorized(messages.invalid_auth_token)

        if not safe_str_cmp(view_uid, decoded_token.get('uid')):
            raise errors.Unauthorized(messages.invalid_auth_token)
    
    def make_token(self, uid, time_= None):
        time_ = time_ or time() + 60 * 30
        return jwt.encode(
            {
                'exp': time_,
                'uid': uid
            },
            self.secret,
            'HS256'
        )
