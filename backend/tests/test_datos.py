"""La réplica del ETL debe reproducir el esquema `indicadores` y respetar el diccionario."""

import math

import pytest

from observatorio import esquema, fuente_csv


def test_filas_por_tabla(repo):
    for tabla, definicion in esquema.TABLAS.items():
        assert len(repo.tabla(tabla)) == definicion['filas'], tabla


def test_todas_las_cifras_de_control_cuadran(repo):
    malas = [c for c in repo.controles if not c['ok']]
    assert not malas, malas


def test_columnas_iguales_al_ddl(repo):
    for tabla in esquema.TABLAS:
        assert list(repo.tabla(tabla).columns) == esquema.columnas(tabla), tabla


@pytest.mark.parametrize('texto, decimales, esperado', [
    ('16.25', 1, 16.3),        # round() de Python daría 16.2 (redondeo al par)
    ('2.675', 2, 2.68),        # y aquí 2.67 (el binario queda en 2.67499...)
    ('16.276803118908383', 1, 16.3),
    ('-0.05', 1, -0.1),
    ('', 1, None),
    ('*', 1, None),            # dato reservado: faltante, nunca cero
])
def test_redondeo_como_spark(texto, decimales, esperado):
    assert fuente_csv.tasa(texto or None, decimales=decimales) == esperado


def test_valor_que_no_cabe_en_numeric_es_nulo():
    assert fuente_csv.tasa('13401.0') is None                 # NUMERIC(5,1)
    assert fuente_csv.tasa('13401.0', enteros=10) == 13401.0  # NUMERIC(10,1)


def test_claves_geograficas_son_texto(repo):
    alc = repo.tabla('resumen_alcaldia')
    assert sorted(alc['cve_mun']) == [f'{i:03d}' for i in range(2, 18)]
    ageb = repo.tabla('carga_ageb')['cvegeo_ageb']
    assert ageb.str.len().eq(13).all()
    assert ageb.str.startswith('09').all()
    assert ageb.str[-1].str.isalpha().sum() > 0      # AGEB alfanuméricas como 003A


def test_benito_juarez_no_aplica_en_lugar_de_cero(repo):
    alc = repo.tabla('resumen_alcaldia').set_index('alcaldia')
    assert math.isnan(alc.loc['Benito Juárez', 'pct_agebs_alta_carga_sin_respaldo'])
    assert alc.loc['Cuauhtémoc', 'pct_agebs_alta_carga_sin_respaldo'] == 0.0


def test_la_brecha_sale_del_kpi_y_no_de_restar(repo):
    kpi = repo.tabla('kpi_cdmx').set_index('clave')
    assert kpi.loc[fuente_csv.CLAVE_BRECHA_NO_PAGADO, 'valor_num'] == 12.7
    j = repo.tabla('enut_doble_jornada').set_index('grupo')
    resta = (j.loc['Mujeres ocupadas', 'horas_trabajo_domestico'] + j.loc['Mujeres ocupadas', 'horas_cuidado']
             - j.loc['Hombres ocupados (ref.)', 'horas_trabajo_domestico'] - j.loc['Hombres ocupados (ref.)', 'horas_cuidado'])
    assert round(resta, 1) == 12.6   # la razón por la que el tablero no la recalcula


def test_unidades_de_los_kpi(repo):
    kpi = repo.tabla('kpi_cdmx').set_index('clave')['unidad']
    assert kpi['ENUT · % mujeres CDMX que cuidan'] == '%'
    assert kpi['ENUT · jornada total mujeres ocupadas (h)'] == 'horas por semana'
    assert kpi['Cruce · mujeres 15–59 en esas AGEB'] == 'mujeres'
    assert kpi['Cruce · AGEB alta carga sin respaldo'] == 'AGEB'
    assert kpi['Censo · carga directa x100 mujeres, CDMX'] == 'personas por cada 100 mujeres'
    assert kpi['Censo · alcaldía con mayor carga'] == 'texto'


def test_enasic_es_solo_nacional(repo):
    enasic = repo.tabla('enasic_cuidadoras')
    assert set(enasic['nivel_geografico']) == {'Nacional'}
    kpi = repo.tabla('kpi_cdmx')
    assert set(kpi.loc[kpi['fuente'].str.contains('ENASIC'), 'nivel_geografico']) == {'Nacional'}


def test_respaldo_y_claves_que_no_empatan(repo):
    est = repo.tabla('establecimientos_cuidado')
    assert int(est['es_respaldo'].sum()) == 838
    assert int(est['cvegeo_ageb'].isna().sum()) == 6


def test_banderas_de_muestra(repo):
    enut = repo.tabla('enut_carga_actividad')
    assert int(enut['precision_baja'].sum()) == 3
    grupos = repo.tabla('enut_cuidado_por_grupo').set_index('grupo')['confiable']
    assert not grupos['Desocupada'] and not grupos['Otra situación']
    assert grupos['Ocupada']


def test_ubicaciones_de_ageb_son_aproximadas(repo):
    assert repo.tabla('carga_ageb')['centroide_es_aproximado'].all()
