from functools import (
    wraps,
    partial
)
from flask import (
    abort,
    current_app,
    redirect,
    request,
    url_for,
    session
)
import os

def capability_url(env_key, redirect_to_slash, f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        capability_token = os.getenv(env_key)
        if capability_token is None:
            current_app.logger.error(f"La variable d'environnement {env_key} n'existe pas")
            abort(500)
        if 'secret_slug' in kwargs and redirect_to_slash:
            session['secret_slug'] = kwargs.pop('secret_slug')
            return redirect(
                url_for(request.endpoint, **kwargs)
            )
        secret_slug = session.get('secret_slug') or kwargs.get('secret_slug')
        if secret_slug != capability_token:
            current_app.logger.error(f"L'url \"{request.url}\" a été accédée avec un mauvais token")
            abort(401)
        return f(*args, **kwargs)
    return decorated_function

admin_capability_url = partial(capability_url, 'CAPABILITY_ADMIN_TOKEN', True)
admin_capability_url_no_redirect = partial(capability_url, 'CAPABILITY_ADMIN_TOKEN', False)
task_status_capability_url = partial(capability_url, 'CAPABILITY_ADMIN_TOKEN', False)
webhook_capability_url = partial(capability_url, 'CAPABILITY_WEBHOOK_TOKEN', False)
