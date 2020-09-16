from functools import wraps
from flask import abort, current_app, request
import os

def admin_capability_url(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        capability_admin_token = os.getenv('CAPABILITY_ADMIN_TOKEN')
        if capability_admin_token is None:
            current_app.logger.error("La variable d'environnement CAPABILITY_ADMIN_TOKEN n'existe pas")
            abort(500)
        if not 'secret_slug' in kwargs:
            current_app.logger.error("L'url ne contient pas de secret_slug")
            abort(500)
        if kwargs['secret_slug'] != capability_admin_token:
            current_app.logger.error(f"L'url \"{request.url}\" a été accédée avec un mauvais token")
            abort(401)
        return f(*args, **kwargs)
    return decorated_function

