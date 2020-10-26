from flask import (
    render_template,
    redirect,
    request,
    url_for,
    stream_with_context,
    Response,
)
from datetime import datetime
from .forms import Form
from .models import Avis
from .models import db
from ecosante.utils.decorators import admin_capability_url
from ecosante.utils import Blueprint

bp = Blueprint(
    "avis",
    __name__,
)

@bp.route('/', methods=['GET', 'POST'])
def index():
    form = Form()
    if request.method == "POST":
        if form.validate_on_submit():
            avis = Avis()
            form.populate_obj(avis)
            db.session.add(avis)
            db.session.commit()
            return redirect(url_for('avis.ajoute'))
    return render_template(
        'form.html',
        form=form
    )

@bp.route('/ajoute')
def ajoute():
    return render_template('ajoute.html')

@bp.route('<secret_slug>/csv')
@admin_capability_url
def csv(secret_slug):
    filename = f"export-{datetime.now().strftime('%Y-%m-%d_%H%M')}.csv"
    return Response(
        stream_with_context(
            Avis.generate_csv()
        ),
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )