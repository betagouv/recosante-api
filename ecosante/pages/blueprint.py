from flask import (
    Blueprint,
    render_template
)

bp = Blueprint("pages", __name__, template_folder='templates', url_prefix='/')

@bp.route('/')
def index():
    return render_template("index.html")

@bp.route('/donnees-personnelles')
def donnees_personnelles():
    return render_template("donnees-personnelles.html")