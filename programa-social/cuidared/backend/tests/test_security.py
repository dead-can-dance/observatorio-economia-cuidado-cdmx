from app.security import create_access_token, decode_access_token, hash_password, verify_password


def test_hash_y_verificacion_de_contrasena():
    guardada = hash_password("mi-clave-segura")
    assert guardada != "mi-clave-segura"
    assert verify_password("mi-clave-segura", guardada)
    assert not verify_password("otra-clave", guardada)


def test_dos_hashes_de_la_misma_clave_son_distintos():
    assert hash_password("misma-clave") != hash_password("misma-clave")


def test_token_se_decodifica_al_mismo_usuario():
    assert decode_access_token(create_access_token(42)) == 42


def test_token_invalido_devuelve_none():
    assert decode_access_token("no-es-un-token") is None
