"""La API: respuestas, validaciones y que los hallazgos respeten «Cómo NO leer estos datos»."""

import pytest

from observatorio import esquema

ALCALDIAS = [f'{i:03d}' for i in range(2, 18)]


def test_estado(cliente):
    r = cliente.get('/api/estado')
    assert r.status_code == 200
    datos = r.json()
    assert datos['fuente'] == 'csv'
    assert datos['controles_ok'] is True
    assert datos['tablas'] == {t: d['filas'] for t, d in esquema.TABLAS.items()}


def test_toda_cifra_lleva_fuente_y_nivel(cliente):
    for ruta in ['/api/kpis', '/api/enut/carga-actividad', '/api/enut/brecha', '/api/enut/doble-jornada',
                 '/api/alcaldias', '/api/agebs', '/api/establecimientos', '/api/territorio']:
        datos = cliente.get(ruta).json()
        assert datos['fuente'] and datos['nivel_geografico'], ruta


def test_cuidado_por_grupo_exige_no_mezclar(cliente):
    assert cliente.get('/api/enut/cuidado-por-grupo').status_code == 422
    edad = cliente.get('/api/enut/cuidado-por-grupo', params={'tipo_grupo': 'Grupo de edad'}).json()
    assert [f['grupo'] for f in edad['filas']] == ['12–17', '18–29', '30–44', '45–59', '60+']


def test_enasic_trae_base_por_tema(cliente):
    datos = cliente.get('/api/enasic').json()
    assert datos['nivel_geografico'] == ['Nacional']
    temas = {t['tema']: t for t in datos['temas']}
    assert temas['Razones para no buscar']['respuesta_multiple'] is True
    assert temas['Razones para no buscar']['base'] == 'Mujeres cuidadoras que no buscaron servicio'
    assert temas['Preferencia de cuidado']['filas'][0] == {'categoria': 'En su casa', 'pct': 61.2}


def test_doble_jornada_trae_la_brecha_oficial(cliente):
    assert cliente.get('/api/enut/doble-jornada').json()['brecha_trabajo_no_pagado_h'] == 12.7


def test_ficha_de_iztapalapa(cliente):
    ficha = cliente.get('/api/alcaldias/007').json()
    assert ficha['alcaldia']['alcaldia'] == 'Iztapalapa'
    sin_respaldo = next(h for h in ficha['hallazgos'] if h['clave'] == 'sin_respaldo')
    assert sin_respaldo['exploratorio'] is True
    assert '25 de sus 167 AGEB' in sin_respaldo['texto']
    assert ficha['agebs']['embudo'][-1]['agebs'] == 25


@pytest.mark.parametrize('ruta, codigo', [('/api/alcaldias/999', 404), ('/api/alcaldias/abc', 422),
                                          ('/api/territorio?cve_mun=999', 404)])
def test_alcaldia_invalida(cliente, ruta, codigo):
    assert cliente.get(ruta).status_code == codigo


def _todos_los_hallazgos(cliente):
    for nivel in ['nacional', 'cdmx', 'alcaldias']:
        yield from cliente.get(f'/api/hallazgos/{nivel}').json()['hallazgos']
    for cve in ALCALDIAS:
        yield from cliente.get(f'/api/alcaldias/{cve}').json()['hallazgos']


def test_hallazgos_respetan_las_cinco_advertencias(cliente):
    for h in _todos_los_hallazgos(cliente):
        assert h['fuente'] and h['nivel_geografico'], h
        # 1. El DENUE no mide cobertura: la palabra solo puede aparecer en la advertencia.
        assert 'cobertura' not in h['texto'].lower(), h
        # 2. Lo de la ENASIC es nacional y nunca habla de la ciudad.
        if 'ENASIC' in h['fuente']:
            assert h['nivel_geografico'] == 'Nacional'
            assert 'CDMX' not in h['texto'] and 'Ciudad de México' not in h['texto'], h
        # 3. Lo que depende de las ubicaciones aproximadas se marca como exploratorio.
        if 'sin respaldo' in h['texto'] or 'sin ninguna guardería' in h['texto']:
            assert h['exploratorio'], h
        # 5. Los hombres son referencia: nunca en un titular.
        assert 'hombre' not in h['titulo'].lower(), h
        if 'hombres' in h['texto']:
            assert 'referencia' in h['texto'], h


def test_descarga_csv(cliente):
    r = cliente.get('/api/indicadores/resumen_alcaldia.csv')
    assert r.status_code == 200
    assert r.headers['content-type'].startswith('text/csv')
    assert r.content.startswith(b'\xef\xbb\xbf')               # BOM para Excel
    assert len(r.content.decode('utf-8-sig').strip().splitlines()) == 17
    assert 'Álvaro Obregón' in r.content.decode('utf-8-sig')


def test_solo_se_exponen_tablas_de_indicadores(cliente):
    assert cliente.get('/api/indicadores/denue_cuidado').status_code == 422
    assert cliente.get('/api/indicadores/kpi_cdmx').status_code == 200


def test_frontend_servido(cliente):
    r = cliente.get('/')
    assert r.status_code == 200 and '<div id="app">' in r.text
    js = cliente.get('/js/main.js')
    assert js.status_code == 200
    assert 'javascript' in js.headers['content-type']        # los módulos no cargan con text/plain
