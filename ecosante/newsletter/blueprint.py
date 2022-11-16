from flask import (
    abort,
    current_app,
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
from indice_pollution.history.models.vigilance_meteo import VigilanceMeteo
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from ecosante.inscription.models import Inscription
from ecosante.recommandations.models import Recommandation

from ecosante.utils import Blueprint
from ecosante.extensions import db, sib, admin_authenticator
from .forms import FormTemplateAdd, FormTemplateEdit
from .models import Newsletter, NewsletterDB, NewsletterHebdoTemplate
from .tasks.import_in_sb import import_
from .tasks.send_webpush_notifications import send_webpush_notification, vapid_claims
from indice_pollution.history.models import IndiceATMO
import sib_api_v3_sdk
from psycopg2.extras import DateTimeTZRange

bp = Blueprint("newsletter", __name__)

@bp.route('<short_id>/avis', methods=['POST'])
def avis(short_id):
    nl = db.session.query(NewsletterDB).filter_by(short_id=short_id).first()
    if not nl:
        abort(404)
    nl.appliquee = request.args.get('avis') == 'oui' or request.args.get('appliquee') == 'oui'
    db.session.add(nl)
    db.session.commit()
    return {
        "short_id": nl.short_id,
        "avis": nl.avis,
        "recommandation": nl.recommandation,
        "appliquee": nl.appliquee
    }

@bp.route('/avis/liste')
@admin_authenticator.route
def liste_avis():
    newsletters = NewsletterDB.query\
        .filter(NewsletterDB.avis.isnot(None))\
        .order_by(NewsletterDB.date.desc())\
        .all()
    return render_template('liste_avis.html', newsletters=newsletters)


@bp.route('/avis/csv')
@admin_authenticator.route
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

@bp.route('/test', methods=['GET', 'POST'])
@admin_authenticator.route
def test():
    if request.method == "GET":
        return render_template("test.html")
    indice_atmo = int(request.form.get("indice_atmo"))
    uid = request.form.get("uid")
    inscription = Inscription.query.filter_by(uid=uid).first()
    nb_mails = 0
    nb_notifications = 0
    nb_notifications_sent = 0
    phenomene_to_phenomene_id = {v: k for k, v in VigilanceMeteo.phenomenes.items()}
    couleur_to_couleur_id = {v: k for k, v in VigilanceMeteo.couleurs.items()}
    recommandations = Recommandation.published_query().all()
    for media in inscription.indicateurs_media:
        nl = Newsletter(
            inscription=inscription,
            forecast={"data":[{"date": str(today()), "label": IndiceATMO.label_from_valeur(indice_atmo), "couleur": IndiceATMO.couleur_from_valeur(indice_atmo)}]},
            raep=int(request.form.get("raep")),
            allergenes={k: v for k, v in zip(request.form.getlist('allergene_nom[]'), request.form.getlist('allergene_value[]'))},
            validite_raep={
                "debut": today().strftime("%d/%m/%Y"),
                "fin": (today()+timedelta(days=7)).strftime("%d/%m/%Y")
            },
            vigilances=Newsletter.get_vigilances_recommandations(
                [
                    VigilanceMeteo(
                        zone_id=inscription.commune.departement.zone_id,
                        couleur_id=couleur_to_couleur_id[c],
                        phenomene_id=phenomene_to_phenomene_id[ph],
                        date_export=datetime.now() - timedelta(minutes=30),
                        validity=DateTimeTZRange(datetime.now() - timedelta(hours=6), datetime.now() + timedelta(hours=6)),
                    )
                    for c, ph in zip(
                        request.form.getlist('vigilance_couleur[]'),
                        request.form.getlist('vigilance_phenomene[]')
                    )
                ],
                recommandations
            ),
            recommandations=recommandations,
            indice_uv=request.form.get("indice_uv", type=int)
        )
        if media == "mail":
            import_(None, newsletters=[nl], force_send=True, test=True)
            nb_mails += 1
        elif media == "notifications_web":
            for wp in inscription.webpush_subscriptions_info:
                nl.webpush_subscription_info = wp
                nl.webpush_subscription_info_id = wp.id
                if send_webpush_notification(NewsletterDB(nl), vapid_claims):
                    nb_notifications_sent += 1
                nb_notifications += 1

    return render_template("test_ok.html", nb_mails=nb_mails, nb_notifications=nb_notifications, nb_notifications_sent=nb_notifications_sent)

@bp.route('/newsletter_hebdo_templates', methods=['GET', 'POST'])
@admin_authenticator.route
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
            current_app.logger.info(f"Template SIB {t.sib_id} inexistant")
            pass
        templates.append(template)
    return render_template("newsletter_hebdo_templates.html", templates=templates)


@bp.route('/newsletter_hebdo/_add', methods=['GET', 'POST'])
@bp.route('/newsletter_hebdo/<int:id_>/_edit', methods=['GET', 'POST'])
@admin_authenticator.route
def newsletter_hebdo_form(id_=None):
    form_cls = FormTemplateEdit if id_ else FormTemplateAdd
    form = form_cls(obj=NewsletterHebdoTemplate.query.get(id_))
    (dernier_ordre,) = db.session.query(func.max(NewsletterHebdoTemplate.ordre)).first()
    form.ordre.description = f"Dernier ordre ajouté : {dernier_ordre}"
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

