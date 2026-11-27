import pytest

from app.config import settings

AGEB = "0900700012345"
MISMA_ALCALDIA = "0900700019999"
OTRA_ALCALDIA = "0901500010001"


def _alta(client, email, perfil, ageb):
    r = client.post(
        "/auth/registro",
        json={
            "email": email,
            "password": "contrasena-segura",
            "nombre": email.split("@")[0].capitalize(),
            "perfil": perfil,
            "ageb": ageb,
            "acepto_aviso_privacidad": True,
        },
    )
    assert r.status_code == 201, r.text
    token = client.post("/auth/login", json={"email": email, "password": "contrasena-segura"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _servicio(client, headers, tipo, tarifa_min, tarifa_max):
    r = client.post(
        "/servicios",
        headers=headers,
        json={"tipo_cuidado": tipo, "tarifa_min": tarifa_min, "tarifa_max": tarifa_max, "disponibilidad": "mañanas"},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


@pytest.fixture()
def escenario(client):
    familia = _alta(client, "familia@ejemplo.com", "necesita_cuidado", AGEB)
    ana = _alta(client, "ana@ejemplo.com", "puede_cuidar", AGEB)
    beto = _alta(client, "beto@ejemplo.com", "puede_cuidar", MISMA_ALCALDIA)
    carla = _alta(client, "carla@ejemplo.com", "puede_cuidar", OTRA_ALCALDIA)
    dora = _alta(client, "dora@ejemplo.com", "puede_cuidar", AGEB)
    elena = _alta(client, "elena@ejemplo.com", "puede_cuidar", AGEB)

    ids = {
        "ana": _servicio(client, ana, "acompanamiento", 100, 130),   # compatibilidad 100
        "beto": _servicio(client, beto, "acompanamiento", 90, 120),  # misma alcaldía: 85
        "carla": _servicio(client, carla, "acompanamiento", 90, 120),  # otra alcaldía: fuera
        "dora": _servicio(client, dora, "acompanamiento", 300, 400),  # muy cara: fuera
        "elena": _servicio(client, elena, "comidas", 100, 130),      # otro tipo de cuidado: fuera
    }
    r = client.post(
        "/solicitudes",
        headers=familia,
        json={"tipo_cuidado": "acompanamiento", "horario": "mañanas", "presupuesto_min": 90, "presupuesto_max": 130},
    )
    assert r.status_code == 201, r.text
    return {"familia": familia, "ana": ana, "beto": beto, "ids": ids, "solicitud_id": r.json()["id"]}


def test_cada_perfil_solo_hace_lo_suyo(client, escenario):
    cuerpo_servicio = {"tipo_cuidado": "comidas", "tarifa_min": 80, "tarifa_max": 100}
    cuerpo_solicitud = {"tipo_cuidado": "comidas", "presupuesto_min": 80, "presupuesto_max": 100}
    assert client.post("/servicios", headers=escenario["familia"], json=cuerpo_servicio).status_code == 403
    assert client.post("/solicitudes", headers=escenario["ana"], json=cuerpo_solicitud).status_code == 403
    assert client.post("/servicios", json=cuerpo_servicio).status_code == 401


def test_rango_de_precio_invalido_se_rechaza(client, escenario):
    r = client.post(
        "/servicios", headers=escenario["ana"],
        json={"tipo_cuidado": "comidas", "tarifa_min": 150, "tarifa_max": 100},
    )
    assert r.status_code == 422
    r = client.post(
        "/solicitudes", headers=escenario["familia"],
        json={"tipo_cuidado": "comidas", "presupuesto_min": 150, "presupuesto_max": 100},
    )
    assert r.status_code == 422


def test_la_solicitud_hereda_la_zona_de_la_cuenta(client, escenario):
    mias = client.get("/solicitudes/mias", headers=escenario["familia"]).json()
    assert mias[0]["ageb"] == AGEB


def test_coincidencias_filtran_y_ordenan(client, escenario):
    r = client.get(f"/solicitudes/{escenario['solicitud_id']}/coincidencias", headers=escenario["familia"])
    assert r.status_code == 200
    tarjetas = r.json()
    assert [t["servicio_id"] for t in tarjetas] == [escenario["ids"]["ana"], escenario["ids"]["beto"]]
    assert [t["puntaje"] for t in tarjetas] == [100, 85]
    assert "email" not in tarjetas[0]
    assert {c["nombre"] for c in tarjetas[0]["criterios"]} == {"Tipo de cuidado", "Horario", "Zona", "Precio"}


def test_zona_prioritaria_se_marca_en_las_tarjetas(client, escenario, monkeypatch):
    monkeypatch.setattr(settings, "agebs_prioritarias", AGEB)
    r = client.get(f"/solicitudes/{escenario['solicitud_id']}/coincidencias", headers=escenario["familia"])
    assert all(t["zona_prioritaria"] for t in r.json())


def test_solo_el_dueno_ve_las_coincidencias(client, escenario):
    r = client.get(f"/solicitudes/{escenario['solicitud_id']}/coincidencias", headers=escenario["ana"])
    assert r.status_code == 403


def test_me_interesa_crea_vinculacion_y_saca_el_perfil_de_la_pila(client, escenario):
    sid = escenario["solicitud_id"]
    r = client.post(
        f"/solicitudes/{sid}/decisiones", headers=escenario["familia"],
        json={"servicio_id": escenario["ids"]["ana"], "decision": "me_interesa"},
    )
    assert r.status_code == 201
    assert r.json()["vinculacion_id"] is not None
    pila = client.get(f"/solicitudes/{sid}/coincidencias", headers=escenario["familia"]).json()
    assert [t["servicio_id"] for t in pila] == [escenario["ids"]["beto"]]


def test_pasar_saca_el_perfil_de_la_pila_sin_crear_vinculacion(client, escenario):
    sid = escenario["solicitud_id"]
    r = client.post(
        f"/solicitudes/{sid}/decisiones", headers=escenario["familia"],
        json={"servicio_id": escenario["ids"]["ana"], "decision": "pasar"},
    )
    assert r.status_code == 201
    assert r.json()["vinculacion_id"] is None
    assert client.get("/vinculaciones/recibidas", headers=escenario["ana"]).json() == []
    pila = client.get(f"/solicitudes/{sid}/coincidencias", headers=escenario["familia"]).json()
    assert escenario["ids"]["ana"] not in [t["servicio_id"] for t in pila]


def test_no_se_puede_decidir_dos_veces_sobre_el_mismo_perfil(client, escenario):
    sid = escenario["solicitud_id"]
    cuerpo = {"servicio_id": escenario["ids"]["ana"], "decision": "pasar"}
    assert client.post(f"/solicitudes/{sid}/decisiones", headers=escenario["familia"], json=cuerpo).status_code == 201
    assert client.post(f"/solicitudes/{sid}/decisiones", headers=escenario["familia"], json=cuerpo).status_code == 409


def test_el_contacto_se_abre_solo_cuando_la_cuidadora_acepta(client, escenario):
    sid = escenario["solicitud_id"]
    client.post(
        f"/solicitudes/{sid}/decisiones", headers=escenario["familia"],
        json={"servicio_id": escenario["ids"]["ana"], "decision": "me_interesa"},
    )
    recibidas = client.get("/vinculaciones/recibidas", headers=escenario["ana"]).json()
    assert len(recibidas) == 1
    assert recibidas[0]["estado"] == "pendiente"
    assert recibidas[0]["contacto"] is None
    assert client.get("/vinculaciones/mias", headers=escenario["familia"]).json()[0]["contacto"] is None

    r = client.post(
        f"/vinculaciones/{recibidas[0]['id']}/responder", headers=escenario["ana"], json={"aceptar": True}
    )
    assert r.status_code == 200
    assert r.json()["estado"] == "aceptada"
    assert r.json()["contacto"] == "familia@ejemplo.com"
    assert client.get("/vinculaciones/mias", headers=escenario["familia"]).json()[0]["contacto"] == "ana@ejemplo.com"


def test_rechazar_no_abre_el_contacto(client, escenario):
    sid = escenario["solicitud_id"]
    client.post(
        f"/solicitudes/{sid}/decisiones", headers=escenario["familia"],
        json={"servicio_id": escenario["ids"]["ana"], "decision": "me_interesa"},
    )
    vid = client.get("/vinculaciones/recibidas", headers=escenario["ana"]).json()[0]["id"]
    r = client.post(f"/vinculaciones/{vid}/responder", headers=escenario["ana"], json={"aceptar": False})
    assert r.json()["estado"] == "rechazada"
    assert r.json()["contacto"] is None
    assert client.post(f"/vinculaciones/{vid}/responder", headers=escenario["ana"], json={"aceptar": True}).status_code == 409


def test_otra_cuidadora_no_puede_responder_una_vinculacion_ajena(client, escenario):
    sid = escenario["solicitud_id"]
    client.post(
        f"/solicitudes/{sid}/decisiones", headers=escenario["familia"],
        json={"servicio_id": escenario["ids"]["ana"], "decision": "me_interesa"},
    )
    vid = client.get("/vinculaciones/recibidas", headers=escenario["ana"]).json()[0]["id"]
    r = client.post(f"/vinculaciones/{vid}/responder", headers=escenario["beto"], json={"aceptar": True})
    assert r.status_code == 404
