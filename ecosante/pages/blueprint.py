from flask import (
    render_template
)
from ecosante.utils import Blueprint

bp = Blueprint("pages", __name__, url_prefix='/')

@bp.route('/')
def index():
    return render_template("index.html")

@bp.route('/donnees-personnelles')
def donnees_personnelles():
    return render_template("donnees-personnelles.html")