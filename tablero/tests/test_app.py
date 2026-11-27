"""Pruebas de la app de Streamlit: cada página corre sin errores, muestra sus cifras clave y
respeta las advertencias del diccionario de datos.

    python -m pytest tablero/tests -q      (o: python iniciar.py --pruebas)
"""

import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'backend'))
from observatorio import esquema, repositorio  # noqa: E402

# Cifras de control más un conteo de filas por cada tabla de `indicadores`.
TOTAL_CONTROLES = len(repositorio.CONTROLES) + len(esquema.TABLAS)

APP = str(Path(__file__).resolve().parents[1] / 'app.py')
PAGINAS = ['paginas/inicio.py', 'paginas/mexico.py', 'paginas/cdmx.py', 'paginas/alcaldias.py',
           'paginas/territorio.py', 'paginas/decision.py', 'paginas/metodologia.py']


def abrir(pagina=None, **estado):
    at = AppTest.from_file(APP, default_timeout=120)
    for clave, valor in estado.items():
        at.session_state[clave] = valor
    at.run()
    if pagina:
        at.switch_page(pagina)
        at.run()
    assert not at.exception, [e.message for e in at.exception]
    return at


def texto(at):
    partes = [e.value for grupo in (at.title, at.subheader, at.markdown, at.caption, at.info, at.warning,
                                     at.success, at.error) for e in grupo]
    partes += [e.proto.body for e in at.get('html')]
    return '\n'.join(str(p) for p in partes)


@pytest.mark.parametrize('pagina', PAGINAS)
def test_cada_pagina_corre_sin_errores(pagina):
    at = abrir(pagina)
    assert at.title, 'cada página tiene título'


def test_portada_encabeza_con_el_trabajo_no_pagado():
    t = texto(abrir())
    assert '+12.7' in t, 'la brecha se lee del KPI: 12.7 h, no 12.6'
    assert '77.0' in t
    assert 'Fuente: INEGI, ENUT 2024' in t


def test_portada_resume_decision_y_metodologia():
    at = abrir()
    t = texto(at)
    assert 'Escenario simulado' in t and 'Simulado' in t, 'el adelanto de Decisión se marca como simulado'
    assert '838' in t and '1,337' in t, 'la misma oferta que la página Decisión'
    assert '$1.08 M' in t, 'VAN esperado invirtiendo por etapas, leído de indicadores.escenarios_programa'
    for fuente in ('ENUT 2024', 'ENASIC 2022', 'Censo 2020', 'DENUE 05/2026'):
        assert fuente in t
    assert f'{TOTAL_CONTROLES} de {TOTAL_CONTROLES} cifras de control cuadran' in t
    enlaces = [e.proto.label for e in at.get('page_link')]
    assert 'Ir a Decisión' in enlaces and 'Ir a Metodología' in enlaces


def test_portada_cuenta_la_historia_y_lleva_a_cada_pagina():
    at = abrir()
    t = texto(at)
    for seccion in ('El panorama en datos', 'Lo que los datos permiten observar', '¿Por qué una plataforma digital?',
                    'Explorar el observatorio'):
        assert seccion in t
    for titulo in ('Tener empleo no libera del cuidado', 'La presión sobre las guarderías',
                   'Dónde se concentran las zonas sin respaldo'):
        assert titulo in t, 'los hallazgos se toman tal cual del backend'
    assert '44.4' in t and '61.2' in t and '3.2' in t, 'las señales de la ENASIC se leen de kpi_cdmx'
    assert 'no permite cifras de la CDMX' in t, 'la ENASIC se presenta solo como nacional'
    assert '125,256' in t and 'Exploratorio' in t
    assert 'CuidaRed' in t
    assert any('cuidared' in e.proto.url for e in at.get('link_button'))
    enlaces = [e.proto.label for e in at.get('page_link')]
    for pagina in ('México', 'Ciudad de México', 'Alcaldías', 'Territorio', 'Decisión', 'Metodología'):
        assert f'Ir a {pagina}' in enlaces


def test_enasic_se_presenta_solo_como_nacional():
    at = abrir('paginas/mexico.py')
    assert any('Cifras solo nacionales' in i.value for i in at.info)
    t = texto(at)
    assert '61.2' in t and '3.2' in t


def test_ficha_por_omision_es_la_alcaldia_con_mas_mujeres_sin_respaldo():
    t = texto(abrir('paginas/alcaldias.py'))
    assert 'Iztapalapa' in t
    assert '25 de sus 167 AGEB' in t


def test_elegir_otra_alcaldia_cambia_la_ficha():
    at = abrir('paginas/alcaldias.py')
    at.selectbox(key='w_ficha').set_value('014').run()
    assert not at.exception
    assert at.session_state['ficha'] == '014'
    t = texto(at)
    assert 'Benito Juárez' in t
    assert 'no aplica' in t


def test_territorio_de_una_alcaldia():
    t = texto(abrir('paginas/territorio.py', mapa='007'))
    assert 'AGEB de Iztapalapa' in t
    assert '25 AGEB' in t and '40,199' in t


def test_territorio_de_toda_la_ciudad():
    t = texto(abrir('paginas/territorio.py'))
    assert '88 AGEB' in t and '125,256' in t
    assert 'Exploratorio' in t


def test_cifras_de_control_cuadran():
    at = abrir('paginas/metodologia.py')
    assert any(f'({TOTAL_CONTROLES} de {TOTAL_CONTROLES})' in s.value for s in at.success)


def test_decision_muestra_kpis_con_meta_y_recomendacion():
    t = texto(abrir('paginas/decision.py'))
    assert '838' in t and '1,337' in t, 'la oferta de 2026 contra la de 2016'
    assert 'Escenario simulado' in t
    assert 'Fuera de meta' in t and 'En meta' in t, 'los KPI llevan estado con texto, no solo color'
    assert 'invertir por etapas' in t
    assert '$38.01' in t, 'subsidio de equilibrio leído de indicadores.escenarios_programa'


def test_simulador_responde_al_subsidio():
    at = abrir('paginas/decision.py')
    at.slider(key='sim_sub').set_value(20).run()
    assert not at.exception
    assert 'Se cierra en el mes 12' in texto(at), 'con $20 por hora el programa no llega a la mitad del equilibrio'
