DATOS = {
    "email": "Ana@Ejemplo.com",
    "password": "contrasena-segura",
    "nombre": "Ana",
    "perfil": "puede_cuidar",
    "ageb": "0900700012345",
    "acepto_aviso_privacidad": True,
}


def _registrar(client, **cambios):
    return client.post("/auth/registro", json={**DATOS, **cambios})


def test_registro_exitoso_no_devuelve_contrasena(client):
    r = _registrar(client)
    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["email"] == "ana@ejemplo.com"
    assert cuerpo["perfil"] == "puede_cuidar"
    assert "password" not in cuerpo and "password_hash" not in cuerpo


def test_registro_exige_aviso_de_privacidad(client):
    r = _registrar(client, acepto_aviso_privacidad=False)
    assert r.status_code == 400


def test_registro_rechaza_correo_repetido(client):
    assert _registrar(client).status_code == 201
    assert _registrar(client).status_code == 409


def test_registro_rechaza_contrasena_corta(client):
    assert _registrar(client, password="corta").status_code == 422


def test_login_correcto_y_acceso_a_mi_perfil(client):
    _registrar(client)
    r = client.post("/auth/login", json={"email": "ana@ejemplo.com", "password": DATOS["password"]})
    assert r.status_code == 200
    token = r.json()["access_token"]
    yo = client.get("/auth/yo", headers={"Authorization": f"Bearer {token}"})
    assert yo.status_code == 200
    assert yo.json()["nombre"] == "Ana"


def test_login_con_contrasena_incorrecta(client):
    _registrar(client)
    r = client.post("/auth/login", json={"email": "ana@ejemplo.com", "password": "otra-contrasena"})
    assert r.status_code == 401


def test_yo_sin_token_o_con_token_falso(client):
    assert client.get("/auth/yo").status_code == 401
    assert client.get("/auth/yo", headers={"Authorization": "Bearer falso"}).status_code == 401
