from functools import (
    wraps,
    partial
)
from flask import (
    abort,
    current_app,
    request
)
import os

def capability_url(env_key, f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        capability_token = os.getenv(env_key)
        if capability_token is None:
            current_app.logger.error(f"La variable d'environnement {env_key} n'existe pas")
            abort(500)
        if not 'secret_slug' in kwargs:
            current_app.logger.error("L'url ne contient pas de secret_slug")
            abort(500)
        if kwargs['secret_slug'] != capability_token:
            current_app.logger.error(f"L'url \"{request.url}\" a été accédée avec un mauvais token")
            abort(401)
        return f(*args, **kwargs)
    return decorated_function

admin_capability_url = partial(capability_url, 'CAPABILITY_ADMIN_TOKEN')
webhook_capability_url = partial(capability_url, 'CAPABILITY_WEBHOOK_TOKEN')
