import json
from ecosante.inscription.models import Inscription
from datetime import date, datetime, timedelta

def premiere_etape(client):
    mail = f'dodo-{int(datetime.timestamp(datetime.now()))}@beta.gouv.fr'
    data = {'mail': mail}
    response = client.post('/inscription/premiere-etape', data=data)
    assert response.status_code == 201
    return mail, response.json['uid']

def data_tester(response, data):
    assert response.status_code == 200
    for k, v in data.items():
        assert response.json[k] == v

def test_add_webpush_subscriptions_info_bad_json(inscription):
    inscription.add_webpush_subscriptions_info("fifi")
    assert len(inscription.webpush_subscriptions_info) == 0


def test_make_new_value_webpush_subscriptions_info(inscription):
    old_value = [
       {
           "endpoint": "https://recosante.beta.gouv.fr/dashboard/",
            "keys": {
                "p256dh": "BIPUL12DLfytvTajnryr2PRdAgXS3HGKiLqndGcJGabyhHheJYlNGCeXl1dn18gSJ1WAkAPIxr4gK0_dQds4yiI=",
                "auth": "FPssNDTKnInHVndSTdbKFw=="
            }
        }
    ]
    new_value = {
           "endpoint": "https://recosante.beta.gouv.fr/dashboard/",
            "keys": {
                "p256dh": "BIPUL12DLfytvTajnryr2PRdAgXS3HGKiLqndGcJGabyhHheJYlNGCeXl1dn18gSJ1WAkAPIxr4gK0_dQds4yiI=",
                "auth": "new_value_FPssNDTKnInHVndSTdbKFw=="
            }
        }
    # We first add old value, and check its added
    inscription.webpush_subscriptions_info = json.dumps(old_value)
    assert len(inscription.webpush_subscriptions_info) == 1
    # Then we add old value, and check we have the old one and the new one
    inscription.webpush_subscriptions_info = json.dumps(new_value)
    assert len(inscription.webpush_subscriptions_info) == 2
    assert any([v.data == old_value[0] for v in inscription.webpush_subscriptions_info])
    assert any([v.data == new_value for v in inscription.webpush_subscriptions_info])

    # Let's try to add another time this new_value and check we still have only 2 values
    inscription.add_webpush_subscriptions_info = json.dumps(new_value)
    assert len(inscription.webpush_subscriptions_info) == 2
    assert any([v.data == old_value[0] for v in inscription.webpush_subscriptions_info])
    assert any([v.data == new_value for v in inscription.webpush_subscriptions_info])

def test_export_query_quotidien(inscription, db_session):
    db_session.add(inscription)
    db_session.commit()
    inscriptions = Inscription.export_query(type_='quotidien').all()
    assert len(inscriptions) == 1

def test_export_query_hebdomadaire(inscription, db_session):
    db_session.add(inscription)
    db_session.commit()
    inscriptions = Inscription.export_query(type_='hebdomadaire').all()
    assert len(inscriptions) == 1

def test_export_query_hebdomadaire_pas_dinscrit(inscription, db_session):
    inscription.recommandations_actives = ['non']
    db_session.add(inscription)
    db_session.commit()

    inscriptions = Inscription.export_query(type_='hebdomadaire').all()
    assert len(inscriptions) == 0