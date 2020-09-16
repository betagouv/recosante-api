from flask import Blueprint, render_template, request, redirect, session, url_for
from .models import Inscription, db
from .forms import FormInscription, FormHabitudes, FormSante

bp = Blueprint("inscription", __name__, template_folder='templates', url_prefix='/inscription')

@bp.route('/', methods=['GET', 'POST'])
def inscription():
    form = FormInscription()
    if request.method == 'POST' and form.validate_on_submit():
        data = {
            "ville_entree": form.ville_entree.data,
            "frequence": form.frequence.data,
            "diffusion": form.diffusion.data,
            "mail": form.mail.data,
            "telephone": form.telephone.data
        }
        inscription = Inscription.query.filter_by(mail=data['mail']).first() or Inscription()
        for k, v in data.items():
            setattr(inscription, k, v)
            session[k] = v
        db.session.add(inscription)
        db.session.commit()
        session['habitudes'] = dict()
        session['sante'] = dict()
        return redirect(url_for('inscription.reussie'))

    if 'mail' in session:
        del session['mail']

    return render_template('inscription.html', form=form)

@bp.route('/habitudes', methods=['GET', 'POST'])
def habitudes():
    return sante_habitudes(
        FormHabitudes,
        'habitudes',
        ['deplacement', 'sport', 'apa', 'activites', 'enfants']
    )

@bp.route('/sante', methods=['GET', 'POST'])
def sante():
    return sante_habitudes(
        FormSante,
        'sante',
        ['pathologie_respiratoire', 'allergie_pollen', 'fumeur']
    )

def sante_habitudes(form_, nom, fields):
    form = form_(**session[nom])
    if not session['mail']:
        return redirect(url_for('index'))
    if request.method == 'POST' and form.validate_on_submit():
        data = {k: getattr(form, k).data for k in fields}
        inscription = Inscription.query.filter_by(mail=session['mail']).first()
        session[nom] = dict()
        for k, v in data.items():
            setattr(inscription, k, v)
            session[nom][k] = v
        db.session.add(inscription)
        db.session.commit()
        return redirect(url_for('inscription.reussie'))
    return render_template(f'{nom}.html', form=form)

@bp.route('/reussie')
def reussie():
    return render_template('reussi.html')