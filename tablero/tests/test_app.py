"""Pruebas de la app de Streamlit: cada página corre sin errores, muestra sus cifras clave y
respeta las advertencias del diccionario de datos.

    python -m pytest tablero/tests -q      (o: python iniciar.py --pruebas)
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / 'app.py')
PAGINAS = ['paginas/inicio.py', 'paginas/mexico.py', 'paginas/cdmx.py', 'paginas/alcaldias.py',
           'paginas/territorio.py', 'paginas/metodologia.py']


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
    assert any('(18 de 18)' in s.value for s in at.success)
