import pytest

AGEB = "0900700012345"


def _alta(client, email, perfil):
    r = client.post(
        "/auth/registro",
        json={
            "email": email, "password": "contrasena-segura", "nombre": email.split("@")[0].capitalize(),
            "perfil": perfil, "ageb": AGEB, "acepto_aviso_privacidad": True,
        },
    )
    assert r.status_code == 201, r.text
    token = client.post("/auth/login", json={"email": email, "password": "contrasena-segura"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def vinculo(client):
    laura = _alta(client, "laura@ejemplo.com", "necesita_cuidado")
    maria = _alta(client, "maria@ejemplo.com", "puede_cuidar")
    otra = _alta(client, "otra@ejemplo.com", "necesita_cuidado")
    servicio = client.post(
        "/servicios", headers=maria,
        json={"tipo_cuidado": "acompanamiento", "tarifa_min": 100, "tarifa_max": 130, "disponibilidad": "mañanas"},
    ).json()["id"]
    solicitud = client.post(
        "/solicitudes", headers=laura,
        json={"tipo_cuidado": "acompanamiento", "horario": "mañanas", "presupuesto_min": 90, "presupuesto_max": 130},
    ).json()["id"]
    vid = client.post(
        f"/solicitudes/{solicitud}/decisiones", headers=laura,
        json={"servicio_id": servicio, "decision": "me_interesa"},
    ).json()["vinculacion_id"]
    return {"laura": laura, "maria": maria, "otra": otra, "id": vid}


def _aceptar(client, v):
    r = client.post(f"/vinculaciones/{v['id']}/responder", headers=v["maria"], json={"aceptar": True})
    assert r.status_code == 200, r.text


def test_no_se_registran_horas_antes_de_aceptar(client, vinculo):
    r = client.post(f"/vinculaciones/{vinculo['id']}/horas", headers=vinculo["maria"],
                    json={"fecha": "2026-11-02", "horas": 2})
    assert r.status_code == 409


def test_personas_ajenas_no_ven_la_vinculacion(client, vinculo):
    _aceptar(client, vinculo)
    assert client.get(f"/vinculaciones/{vinculo['id']}/seguimiento", headers=vinculo["otra"]).status_code == 404


def test_flujo_de_horas_y_pago_simulado(client, vinculo):
    _aceptar(client, vinculo)
    base = f"/vinculaciones/{vinculo['id']}/horas"
    for fecha in ("2026-11-02", "2026-11-04", "2026-11-07"):
        r = client.post(base, headers=vinculo["maria"], json={"fecha": fecha, "horas": 2})
        assert r.status_code == 201, r.text
    horas = r.json()
    assert horas["total_horas"] == 6
    assert horas["tarifa_acordada"] == 115
    assert horas["total_a_pagar"] == 690
    assert horas["quien_paga"] == "Quien contrata"
    assert horas["estado_pago"] == "por_confirmar"

    # La cuidadora no puede confirmar su propio pago
    assert client.post(base + "/confirmar", headers=vinculo["maria"]).status_code == 403
    r = client.post(base + "/confirmar", headers=vinculo["laura"])
    assert r.status_code == 200
    assert r.json()["estado_pago"] == "pagado_simulado"
    assert client.post(base + "/confirmar", headers=vinculo["laura"]).status_code == 409


def test_quien_contrata_no_registra_horas(client, vinculo):
    _aceptar(client, vinculo)
    r = client.post(f"/vinculaciones/{vinculo['id']}/horas", headers=vinculo["laura"],
                    json={"fecha": "2026-11-02", "horas": 2})
    assert r.status_code == 403


def test_horas_invalidas_se_rechazan(client, vinculo):
    _aceptar(client, vinculo)
    r = client.post(f"/vinculaciones/{vinculo['id']}/horas", headers=vinculo["maria"],
                    json={"fecha": "2026-11-02", "horas": 30})
    assert r.status_code == 422


def test_la_linea_de_tiempo_avanza(client, vinculo):
    base = f"/vinculaciones/{vinculo['id']}"
    r = client.get(base + "/seguimiento", headers=vinculo["laura"]).json()
    assert {p["clave"]: p["estado"] for p in r["pasos"]}["respuesta"] == "actual"

    _aceptar(client, vinculo)
    r = client.get(base + "/seguimiento", headers=vinculo["laura"]).json()
    assert {p["clave"]: p["estado"] for p in r["pasos"]}["encuentro"] == "actual"
    assert r["otra_persona"] == "Maria"
    assert "lugar público" in r["aviso_seguridad"]

    client.post(base + "/horas", headers=vinculo["maria"], json={"fecha": "2026-11-02", "horas": 2})
    client.post(base + "/horas/confirmar", headers=vinculo["laura"])
    assert client.post(base + "/checkin", headers=vinculo["laura"], json={"todo_bien": True}).status_code == 201
    pasos = {p["clave"]: p["estado"] for p in client.get(base + "/seguimiento", headers=vinculo["laura"]).json()["pasos"]}
    assert pasos["horas"] == "hecho" and pasos["checkin"] == "hecho" and pasos["evaluacion"] == "actual"


def test_reportar_un_problema_y_evaluar(client, vinculo):
    _aceptar(client, vinculo)
    base = f"/vinculaciones/{vinculo['id']}"
    r = client.post(base + "/checkin", headers=vinculo["laura"], json={"todo_bien": False, "nota": "Llegó tarde"})
    assert r.json()["tipo"] == "problema"
    assert client.post(base + "/evaluacion", headers=vinculo["laura"], json={"puntuacion": 5}).status_code == 201
    assert client.post(base + "/evaluacion", headers=vinculo["laura"], json={"puntuacion": 4}).status_code == 409
    assert client.post(base + "/evaluacion", headers=vinculo["maria"], json={"puntuacion": 9}).status_code == 422


def test_horas_programadas_se_aceptan_pero_no_se_confirman_antes_de_tiempo(client, vinculo):
    _aceptar(client, vinculo)
    base = f"/vinculaciones/{vinculo['id']}/horas"
    assert client.post(base, headers=vinculo["maria"], json={"fecha": "2999-01-15", "horas": 3}).status_code == 201
    # Solo hay horas futuras: no hay nada que confirmar todavía
    assert client.post(base + "/confirmar", headers=vinculo["laura"]).status_code == 409
    # Al registrar horas ya realizadas, solo esas se confirman
    client.post(base, headers=vinculo["maria"], json={"fecha": "2026-11-02", "horas": 2})
    r = client.post(base + "/confirmar", headers=vinculo["laura"])
    assert r.status_code == 200
    asignadas = {x["fecha"]: x["confirmada"] for x in r.json()["registros"]}
    assert asignadas == {"2026-11-02": True, "2999-01-15": False}
    assert r.json()["estado_pago"] == "por_confirmar"
