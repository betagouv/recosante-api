from flask import (
    abort,
    render_template,
    request,
    redirect,
    url_for,
    stream_with_context,
)
from flask.helpers import flash
from flask.wrappers import Response
from datetime import datetime, timedelta
import csv

from indice_pollution.helpers import today
from indice_pollution.history.models.commune import Commune
from indice_pollution.history.models.departement import Departement
from sqlalchemy.orm import joinedload, subqueryload
from ecosante.inscription.models import Inscription

from ecosante.utils.decorators import admin_capability_url, admin_capability_url_no_redirect
from ecosante.utils import Blueprint
from ecosante.extensions import sib
from .forms import FormAvis, FormTemplateAdd, FormTemplateEdit
from .models import Newsletter, NewsletterDB, NewsletterHebdoTemplate, db
from .tasks.import_in_sb import create_campaign, import_, send
from .tasks.send_webpush_notifications import send_webpush_notification, vapid_claims
from indice_pollution.history.models import IndiceATMO
import sib_api_v3_sdk

bp = Blueprint("newsletter", __name__)

@bp.route('<short_id>/avis', methods=['GET', 'POST'])
def avis(short_id):
    nl = db.session.query(NewsletterDB).filter_by(short_id=short_id).first()
    if not nl:
        abort(404)
    nl.appliquee = request.args.get('avis') == 'oui' or request.args.get('appliquee') == 'oui'
    form = FormAvis(request.form or request.json, obj=nl)
    if request.method=='POST' and form.validate_on_submit():
        form.populate_obj(nl)
        db.session.add(nl)
        db.session.commit()
        if not request.accept_mimetypes.accept_html:
            return {
                "short_id": nl.short_id,
                "avis": nl.avis,
                "recommandation": nl.recommandation,
                "appliquee": nl.appliquee
            }
        return redirect(
            url_for('newsletter.avis_enregistre', short_id=short_id)
        )
    db.session.add(nl)
    db.session.commit()

    if not request.accept_mimetypes.accept_html:
        return {
            "short_id": nl.short_id,
            "avis": nl.avis,
            "recommandation": nl.recommandation,
            "appliquee": nl.appliquee
        }
    return render_template(
        'avis.html',
        nl=nl,
        form=form,
    )

@bp.route('<short_id>/avis/enregistre')
def avis_enregistre(short_id):
    return render_template('avis_enregistre.html')

@bp.route('<secret_slug>/avis/liste')
@bp.route('/avis/liste')
@admin_capability_url
def liste_avis():
    newsletters = NewsletterDB.query\
        .filter(NewsletterDB.avis.isnot(None))\
        .order_by(NewsletterDB.date.desc())\
        .all()
    return render_template('liste_avis.html', newsletters=newsletters)


@bp.route('<secret_slug>/avis/csv')
@bp.route('/avis/csv')
@admin_capability_url
def export_avis():
    return Response(
        stream_with_context(
            NewsletterDB.generate_csv_avis()
        ),
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=export-avis-{datetime.now()}"
        }
    )

@bp.route('<secret_slug>/send_campaign/', methods=['GET', 'POST'])
@admin_capability_url_no_redirect
def send_campaign(secret_slug):
    now = request.args.get('now')
    mail_list_id = request.args.get('mail_list_id', type=int)
    template_id = request.args.get('template_id', type=int)
    type_ = request.args.get('type_')
    campaign_id = create_campaign(now, mail_list_id=mail_list_id, template_id=template_id, type_=type_)
    send(campaign_id)
    return "ok"

@bp.route('<secret_slug>/<int:mail_list_id>/export.csv', methods=['GET', 'POST'])
@admin_capability_url_no_redirect
def export(mail_list_id, secret_slug):
    class Line(object):
        def __init__(self):
            self._line = None
        def write(self, line):
            self._line = line
        def read(self):
            return self._line
    def iter_csv(newsletters):
        line = Line()
        writer = csv.DictWriter(line, fieldnames=NewsletterDB.header)
        writer.writeheader()
        yield line.read()
        for nl in newsletters:
            if nl.inscription.mail is None:
                continue
            writer.writerow(nl.attributes())
            yield line.read()
    newsletters = db.session.query(NewsletterDB).filter_by(
        mail_list_id=mail_list_id
        ).options(
            joinedload(
                NewsletterDB.inscription
            ).joinedload(
                Inscription.commune
            ).joinedload(
                Commune.departement
            ).joinedload(
                Departement.region
            )
        ).options(joinedload(NewsletterDB.recommandation)
        ).options(joinedload(NewsletterDB.recommandation_qa)
        ).options(joinedload(NewsletterDB.recommandation_raep)
        ).populate_existing(
        ).yield_per(1000)
    response = Response(iter_csv(newsletters), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=export.csv'
    return response


@bp.route('<secret_slug>/test', methods=['GET', 'POST'])
@bp.route('/test', methods=['GET', 'POST'])
@admin_capability_url
def test():
    if request.method == "GET":
        return render_template("test.html")
    indice_atmo = int(request.form.get("indice_atmo"))
    uid = request.form.get("uid")
    inscription = Inscription.query.filter_by(uid=uid).first()
    nb_mails = 0
    nb_notifications = 0
    nb_notifications_sent = 0
    for media in inscription.indicateurs_media:
        nl = Newsletter(
            inscription=inscription,
            forecast={"data":[{"date": str(today()), "label": IndiceATMO.label_from_valeur(indice_atmo), "couleur": IndiceATMO.couleur_from_valeur(indice_atmo)}]},
            raep=int(request.form.get("raep")),
            allergenes={k: v for k, v in zip(request.form.getlist('allergene_nom'), request.form.getlist('allergene_value'))},
            validite_raep={
                "debut": today().strftime("%d/%m/%Y"),
                "fin": (today()+timedelta(days=7)).strftime("%d/%m/%Y")
            }
        )
        if media == "mail":
            import_(None, newsletters=[NewsletterDB(nl)], force_send=True, test=True)
            nb_mails += 1
        elif media == "notifications_web":
            for wp in inscription.webpush_subscriptions_info:
                nl.webpush_subscription_info = wp
                nl.webpush_subscription_info_id = wp.id
                if send_webpush_notification(NewsletterDB(nl), vapid_claims):
                    nb_notifications_sent += 1
                nb_notifications += 1

    return render_template("test_ok.html", nb_mails=nb_mails, nb_notifications=nb_notifications, nb_notifications_sent=nb_notifications_sent)

@bp.route('<secret_slug>/newsletter_hebdo_templates', methods=['GET', 'POST'])
@bp.route('/newsletter_hebdo_templates', methods=['GET', 'POST'])
@admin_capability_url
def newsletter_hebdo():
    templates_db = NewsletterHebdoTemplate.query.order_by(NewsletterHebdoTemplate.ordre).all()
    templates = []
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib)
    for t in templates_db:
        template = {"db": t, "is_active": False}
        try:
            api_response = api_instance.get_smtp_template(t.sib_id)
            template["is_active"] = api_response.is_active
        except sib_api_v3_sdk.rest.ApiException as e:
            continue
        templates.append(template)
    return render_template("newsletter_hebdo_templates.html", templates=templates)


@bp.route('<secret_slug>/newsletter_hebdo/_add', methods=['GET', 'POST'])
@bp.route('/newsletter_hebdo/_add', methods=['GET', 'POST'])
@bp.route('<secret_slug>/newsletter_hebdo/<int:id_>/_edit', methods=['GET', 'POST'])
@bp.route('/newsletter_hebdo/<int:id_>/_edit', methods=['GET', 'POST'])
@admin_capability_url
def newsletter_hebdo_form(id_=None):
    form_cls = FormTemplateEdit if id_ else FormTemplateAdd
    form = form_cls(
        request.form,
        obj=NewsletterHebdoTemplate.query.get(id_)
    )
    if request.method == "GET":
        return render_template("newsletter_hebdo_form.html", form=form)
    else:
        if form.validate_on_submit():
            template = NewsletterHebdoTemplate.query.get(id_) or NewsletterHebdoTemplate()
            form.populate_obj(template)
            db.session.add(template)
            db.session.commit()
            flash(
                "Template édité !" if id_ else "Template ajouté"
            )
            return redirect(url_for("newsletter.newsletter_hebdo"))
        else:
	        return render_template("newsletter_hebdo_form.html", form=form)

