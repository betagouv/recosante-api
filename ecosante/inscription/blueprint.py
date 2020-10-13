from flask import (Blueprint, render_template, request, redirect, session, url_for,
     current_app, stream_with_context, jsonify)
from flask.wrappers import Response
from .models import Inscription, db
from .forms import FormInscription, FormPersonnalisation, FormExport
from ecosante.utils.decorators import admin_capability_url
from ecosante.recommandations.models import Recommandation
from datetime import datetime

bp = Blueprint("inscription", __name__, template_folder='templates', url_prefix='/inscription')

@bp.route('/', methods=['GET', 'POST'])
def inscription():
    form = FormInscription()
    if request.method == 'POST':
        if form.validate_on_submit():
            inscription = Inscription.query.filter_by(mail=form.mail.data).first() or Inscription()
            form.populate_obj(inscription)
            db.session.add(inscription)
            db.session.commit()
            session['inscription'] = inscription
            return redirect(url_for('inscription.personnalisation'))
    else:
        form.mail.process_data(request.args.get('mail'))

    return render_template('inscription.html', form=form)

@bp.route('/personnalisation', methods=['GET', 'POST'])
def personnalisation():
    if not session['inscription']:
        return redirect(url_for('index'))
    inscription = Inscription.query.get(session['inscription']['id'])
    form = FormPersonnalisation(obj=inscription)
    if request.method == 'POST' and form.validate_on_submit():
        form.populate_obj(inscription)        
        db.session.add(inscription)
        db.session.commit()
        session['inscription'] = inscription
        return redirect(url_for('inscription.reussie'))
    return render_template(f'personnalisation.html', form=form)

@bp.route('/reussie')
def reussie():
    inscription = Inscription.query.get(session['inscription']['id'])
    inscription.send_success_email()

    return render_template('reussi.html')

@bp.route('/geojson')
def geojson():
    return jsonify(Inscription.export_geojson())

@bp.route('<secret_slug>/csv')
@admin_capability_url
def export_csv(secret_slug):
    return Response(
        stream_with_context(
            Inscription.generate_csv(
                request.args.get('preferred_reco')
            )
        ),
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=export-{datetime.now().strftime('%Y-%m-%d_%H%M')}.csv"
        }
    )

@bp.route('<secret_slug>/export', methods=['GET', 'POST'])
@admin_capability_url
def export(secret_slug):
    form = FormExport()
    form.recommandations.choices=[
        (
            r.id,
            r.recommandation
        )
        for r in Recommandation.query.all()
    ]
    form.recommandations.widget.secret_slug = secret_slug
    if request.method == 'POST':
        return redirect(
            url_for(
                "inscription.export_csv",
                secret_slug=secret_slug,
                preferred_reco=form.recommandations.data
            )
        )

    return render_template('export.html', form=form)
