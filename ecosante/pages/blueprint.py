from flask import (
    render_template
)
from ecosante.utils import Blueprint
from ecosante.utils.decorators import admin_capability_url
from datetime import date, timedelta
from ecosante.newsletter.models import NewsletterDB

bp = Blueprint("pages", __name__, url_prefix='/')

@bp.route('/')
def index():
    return render_template("index.html")

@bp.route('/donnees-personnelles')
def donnees_personnelles():
    return render_template("donnees-personnelles.html")

@bp.route('/admin/<secret_slug>')
@admin_capability_url
def admin(secret_slug):
    count_avis = NewsletterDB.query\
        .filter(
            NewsletterDB.avis.isnot(None),
            NewsletterDB.date==date.today() - timedelta(days=1))\
        .count()
    return render_template("admin.html", secret_slug=secret_slug, count_avis=count_avis)
