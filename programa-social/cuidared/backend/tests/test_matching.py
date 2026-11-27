from app.matching import calcular_compatibilidad, evaluar_precio, evaluar_zona, rangos_se_traslapan

AGEB = "0900700012345"
MISMA_ALCALDIA = "0900700019999"
OTRA_ALCALDIA = "0901500010001"


def test_rangos_que_se_tocan_se_traslapan():
    assert rangos_se_traslapan(90, 130, 130, 160)
    assert not rangos_se_traslapan(90, 130, 131, 160)


def test_zona_misma_ageb_misma_alcaldia_y_otra_alcaldia():
    assert evaluar_zona(AGEB, AGEB).estado == "coincide"
    assert evaluar_zona(AGEB, MISMA_ALCALDIA).estado == "parcial"
    assert evaluar_zona(AGEB, OTRA_ALCALDIA) is None


def test_zona_sin_dato_no_excluye():
    assert evaluar_zona(None, AGEB).estado == "sin_dato"
    assert evaluar_zona(AGEB, None).estado == "sin_dato"


def test_precio_dentro_parcial_y_fuera_del_presupuesto():
    assert evaluar_precio(90, 130, 100, 120).estado == "coincide"
    assert evaluar_precio(90, 130, 100, 150).estado == "parcial"
    assert evaluar_precio(90, 130, 200, 250) is None


def test_compatibilidad_maxima_es_100():
    r = calcular_compatibilidad(
        ageb_solicitud=AGEB, presupuesto_min=90, presupuesto_max=130,
        ageb_servicio=AGEB, tarifa_min=100, tarifa_max=120,
    )
    assert r.puntaje == 100
    assert [c.nombre for c in r.criterios] == ["Tipo de cuidado", "Zona", "Precio"]


def test_compatibilidad_se_descarta_si_falla_zona_o_precio():
    base = dict(presupuesto_min=90, presupuesto_max=130, tarifa_min=100, tarifa_max=120)
    assert calcular_compatibilidad(ageb_solicitud=AGEB, ageb_servicio=OTRA_ALCALDIA, **base) is None
    caro = dict(presupuesto_min=90, presupuesto_max=130, tarifa_min=300, tarifa_max=400)
    assert calcular_compatibilidad(ageb_solicitud=AGEB, ageb_servicio=AGEB, **caro) is None
