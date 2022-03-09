from flask import (
    abort,
    render_template,
    request,
    jsonify,
    stream_with_context,
)
from .models import Inscription, db
from .forms import FormPremiereEtape, FormDeuxiemeEtape
from ecosante.utils.decorators import (
    admin_capability_url,
    webhook_capability_url
)
from ecosante.utils import Blueprint
from ecosante.extensions import celery
from flask.wrappers import Response
from flask_cors import cross_origin
from datetime import datetime
from email_validator import validate_email

bp = Blueprint("inscription", __name__)

@bp.route('<secret_slug>/user_unsubscription', methods=['POST'])
@webhook_capability_url
def user_unsubscription(secret_slug):
    mail = request.json['email']
    user = Inscription.query.filter_by(mail=mail).first()
    if not user:
        celery.send_task("ecosante.inscription.tasks.send_unsubscribe.send_unsubscribe_errorsend_unsubscribe_error", (mail,))
    else:
        user.unsubscribe()
    return jsonify(request.json)