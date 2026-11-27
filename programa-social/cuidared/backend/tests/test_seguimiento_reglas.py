from app.matching import evaluar_horario, normalizar_franjas
from app.seguimiento import armar_pasos, estado_pago, tarifa_acordada


def _pasos(**cambios):
    datos = dict(
        estado_vinculacion="aceptada", nombre_otra_persona="María", fecha_solicitud="Hoy",
        hay_horas=False, horas_confirmadas=False, checkin_hecho=False, evaluacion_hecha=False,
    )
    datos.update(cambios)
    return {p.clave: p.estado for p in armar_pasos(**datos)}


def test_tarifa_acordada_es_el_punto_medio_del_traslape():
    assert tarifa_acordada(90, 130, 100, 130) == 115
    assert tarifa_acordada(90, 110, 100, 130) == 105
    assert tarifa_acordada(10, 20, 100, 130) == 100  # sin traslape: tarifa mínima


def test_estado_de_pago():
    assert estado_pago(0, 0) == "sin_horas"
    assert estado_pago(3, 1) == "por_confirmar"
    assert estado_pago(3, 3) == "pagado_simulado"


def test_recien_aceptada_el_siguiente_paso_es_el_encuentro():
    pasos = _pasos()
    assert pasos["solicitud"] == "hecho" and pasos["respuesta"] == "hecho"
    assert pasos["encuentro"] == "actual"
    assert pasos["horas"] == pasos["checkin"] == pasos["evaluacion"] == "pendiente"


def test_pendiente_de_respuesta_el_actual_es_la_respuesta():
    pasos = _pasos(estado_vinculacion="pendiente")
    assert pasos["respuesta"] == "actual"


def test_rechazada_no_tiene_paso_actual():
    pasos = _pasos(estado_vinculacion="rechazada")
    assert "actual" not in pasos.values()


def test_todo_cumplido():
    pasos = _pasos(hay_horas=True, horas_confirmadas=True, checkin_hecho=True, evaluacion_hecha=True)
    assert set(pasos.values()) == {"hecho"}


def test_franjas_se_normalizan():
    assert normalizar_franjas("Mañanas, tardes") == {"mañana", "tarde"}
    assert normalizar_franjas("Fines de semana") == {"fines de semana"}
    assert normalizar_franjas(None) == set()


def test_horario_es_informativo():
    assert evaluar_horario("mañanas", "Mañana, Tarde").estado == "coincide"
    assert evaluar_horario("noches", "mañanas").estado == "no_coincide"
    assert evaluar_horario("noches", "mañanas").puntos == 0
    assert evaluar_horario(None, "mañanas") is None
