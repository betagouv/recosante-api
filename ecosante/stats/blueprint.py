from flask import current_app, render_template, Blueprint
from ecosante.inscription.models import Inscription, db
from sqlalchemy import func
from calendar import month_name, different_locale

def get_month_name(month_no, locale):
    with different_locale(locale):
        return month_name[month_no]


bp = Blueprint("stats", __name__, template_folder='templates', url_prefix='/stats')

@bp.route('/')
def stats():
    g = func.date_trunc('month', Inscription.date_inscription)
    graph_inscriptions = db.session.query(g, func.count(Inscription.id)).group_by(g).order_by(g).all()
    mois = [f"{get_month_name(v[0].month, 'fr_FR.utf8')} {v[0].year}" for v in graph_inscriptions]
    valeurs = [v[1] for v in graph_inscriptions]
    return render_template(
        'stats.html', 
        actifs=Inscription.query.count(),
        mois=mois,
        valeurs=valeurs,
        sms=Inscription.query.filter_by(diffusion='sms').count(),
        mails=Inscription.query.filter_by(diffusion='mail').count(),
        quotidien=Inscription.query.filter_by(frequence='quotidien').count(),
        pollution=Inscription.query.filter_by(frequence='pollution').count()
    )

