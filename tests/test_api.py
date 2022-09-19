from indice_pollution.history.models import IndiceUv, PotentielRadon, VigilanceMeteo
from datetime import date, datetime, timedelta
from psycopg2.extras import DateTimeTZRange

def helper_test(response, indice_key, label, area, charniere, code):
    assert indice_key in response.json
    indice_json = response.json[indice_key]
    assert indice_json['indice']['label'] == label
    assert indice_json['validity']['area'] == area
    assert indice_json['validity']['area_details']['charniere'] == charniere
    assert indice_json['validity']['area_details']['code'] == code

def test_commune(client, commune_commited):
    response = client.get(f"/v1/?insee={commune_commited.code}")
    assert response.status_code == 200
    assert response.json['commune'] != None
    assert response.json['commune']['code'] == commune_commited.code
    assert response.json['commune']['nom'] == commune_commited.nom

def test_indice_atmo(client, commune_commited, bonne_qualite_air):
    response = client.get(f"/v1/?insee={commune_commited.code}")
    assert response.status_code == 200
    helper_test(response, 'indice_atmo', bonne_qualite_air.label, "la commune de Laval", "de ", "53130")

def test_raep_no_show(client, commune_commited, raep_faible):
    response = client.get(f"/v1/?insee={commune_commited.code}")
    assert response.status_code == 200
    assert not 'raep' in response.json

def test_raep_show(client, commune_commited, raep_faible):
    response = client.get(f"/v1/?insee={commune_commited.code}&show_raep=true")
    assert response.status_code == 200
    departement = commune_commited.departement
    helper_test(response, 'raep', 'Très faible', "le département de la Mayenne", "de la ", "53")

def test_potentiel_radon(client, commune_commited, db_session):
    radon = PotentielRadon(zone_id=commune_commited.zone_id, classe_potentiel=1)
    db_session.add(radon)
    db_session.commit()
    response = client.get(f"/v1/?insee={commune_commited.code}")
    assert response.status_code == 200
    helper_test(response, 'potentiel_radon', 'Catégorie 1', "la commune de Laval", "de ", "53130")

def test_episodes_pollution(client, commune_commited, episode_soufre, db_session):
    db_session.add(episode_soufre)
    db_session.commit()
    response = client.get(f"/v1/?insee={commune_commited.code}")
    assert response.status_code == 200
    helper_test(response, 'episodes_pollution', 'Épisode de pollution au Dioxyde de soufre', "le département de la Mayenne", "de la ", "53")

def test_vigilance_meteo(client, commune_commited, db_session):
    v = VigilanceMeteo(
        zone_id=commune_commited.departement.zone_id,
        phenomene_id=1,
        couleur_id=1,
        date_export=datetime.now() - timedelta(hours=1),
        validity=DateTimeTZRange(date.today() - timedelta(days=1), date.today() + timedelta(days=1)),
    )
    db_session.add(v)
    db_session.commit()

    response = client.get(f"/v1/?insee={commune_commited.code}")
    assert response.status_code == 200
    helper_test(response, 'vigilance_meteo', 'Vigilance verte', "le département de la Mayenne", "de la ", "53")

def test_indice_uv_no_show(client, commune_commited, db_session):
    indice_uv = IndiceUv(
        zone_id=commune_commited.zone_id,
        date=date.today(),
        uv_j0=0,
    )
    db_session.add(indice_uv)
    db_session.commit()

    response = client.get(f"/v1/?insee={commune_commited.code}")
    assert response.status_code == 200
    assert 'indice_uv' not in response.json

def test_indice_uv_show(client, commune_commited, db_session):
    indice_uv = IndiceUv(
        zone_id=commune_commited.zone_id,
        date=date.today(),
        uv_j0=0,
    )
    db_session.add(indice_uv)
    db_session.commit()

    response = client.get(f"/v1/?insee={commune_commited.code}&show_indice_uv=true")
    assert response.status_code == 200
    helper_test(response, 'indice_uv', 'Nul (UV\u00a00)', "la commune de Laval", "de ", "53130")

def test_indice_uv_j1(client, commune_commited, db_session):
    indice_uv = IndiceUv(
        zone_id=commune_commited.zone_id,
        date=date.today(),
        uv_j1=11,
    )
    db_session.add(indice_uv)
    db_session.commit()
    tomorrow = date.today() + timedelta(days=1)
    tomorrow_string = tomorrow.strftime('%Y-%m-%d')
    response = client.get(f"/v1/?insee={commune_commited.code}&date={tomorrow_string}&time=12:00&show_indice_uv=true")
    assert response.status_code == 200
    helper_test(response, 'indice_uv', 'Extrême (UV\u00a011)', "la commune de Laval", "de ", "53130")

def test_indice_uv_j2(client, commune_commited, db_session):
    indice_uv = IndiceUv(
        zone_id=commune_commited.zone_id,
        date=date.today(),
        uv_j2=11,
    )
    db_session.add(indice_uv)
    db_session.commit()
    in2days = date.today() + timedelta(days=2)
    in2days_string = in2days.strftime('%Y-%m-%d')
    response = client.get(f"/v1/?insee={commune_commited.code}&date={in2days_string}&time=12:00&show_indice_uv=true")
    assert response.status_code == 200
    helper_test(response, 'indice_uv', 'Extrême (UV\u00a011)', "la commune de Laval", "de ", "53130")

def test_indice_uv_j3(client, commune_commited, db_session):
    indice_uv = IndiceUv(
        zone_id=commune_commited.zone_id,
        date=date.today(),
        uv_j3=11,
    )
    db_session.add(indice_uv)
    db_session.commit()
    in3days = date.today() + timedelta(days=3)
    in3days_string = in3days.strftime('%Y-%m-%d')
    response = client.get(f"/v1/?insee={commune_commited.code}&date={in3days_string}&time=12:00&show_indice_uv=true")
    assert response.status_code == 200
    helper_test(response, 'indice_uv', 'Extrême (UV\u00a011)', "la commune de Laval", "de ", "53130")