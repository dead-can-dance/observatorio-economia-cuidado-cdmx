"""Reconstruye el esquema `indicadores` a partir de los CSV de data/curada/.

Es una réplica, sin Spark, de la sección 5 de etl/cargar_capas.py: mismas columnas,
mismos tipos y el mismo redondeo. Existe para que el observatorio se pueda levantar sin
Docker; cuando la base está arriba, el backend lee PostgreSQL y este módulo no se usa.

Si cambia un cálculo en el ETL hay que cambiarlo aquí también. Las pruebas de
backend/tests/ verifican las mismas cifras de control que el ETL, así que una
divergencia se nota.

Detalles de paridad con Spark que importan:

  * Todo se lee como texto: '09', '002' y las AGEB alfanuméricas ('003A') no se tocan.
  * limpiar(): espacios recortados y cadena vacía -> nulo, igual que en el ETL.
  * tasa(): Spark convierte double -> decimal partiendo de la representación más corta
    del double y redondeando HALF_UP. round() de Python redondea al par y sobre el
    binario, así que 16.25 y 16.35 saldrían distinto. Se replica con Decimal.
  * Un valor que no cabe en NUMERIC(p, s) es nulo (try_cast), no un error.
"""

import csv
import math
import re
import unicodedata
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import pandas as pd

from . import esquema

FTE_ENUT = 'INEGI, ENUT 2024'
FTE_ENASIC = 'INEGI, ENASIC 2022'
FTE_CRUCE = 'INEGI, Censo 2020 + DENUE 05/2026'
FTE_DENUE = 'INEGI, DENUE 05/2026'

# Mismas constantes que etl/cargar_capas.py.
CODIGOS_RESPALDO = {'624411', '624412',    # guarderías
                    '623311', '623312',    # residencias y asilos de personas mayores
                    '624121', '624122'}    # centros de día
CLAVE_BRECHA_NO_PAGADO = ('ENUT · brecha de trabajo no pagado, '
                          'mujeres − hombres ocupados (h)')


# =============================================================================
# Lectura
# =============================================================================

def normalizar_columna(nombre):
    """Encabezado de CSV -> nombre de columna, con la misma regla que el ETL."""
    s = unicodedata.normalize('NFKD', nombre)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace('%', 'pct')
    s = re.sub(r'[^a-z0-9]+', '_', s)
    s = re.sub(r'_+', '_', s).strip('_')
    return f'c_{s}' if s and s[0].isdigit() else s


def leer(directorio, nombre):
    """Lee un CSV como lista de dicts de texto, ya limpio (trim y '' -> None)."""
    ruta = Path(directorio) / f'{nombre}.csv'
    with open(ruta, encoding='utf-8-sig', newline='') as f:
        lector = csv.reader(f)
        encabezado = [normalizar_columna(c) for c in next(lector)]
        filas = []
        for fila in lector:
            if not fila:
                continue
            valores = [v.strip() for v in fila]
            filas.append({c: (v if v != '' else None) for c, v in zip(encabezado, valores)})
    return filas


# =============================================================================
# Conversiones (equivalentes a entero / tasa / booleano / doble del ETL)
# =============================================================================

def doble(v):
    if v is None:
        return None
    try:
        return float(v)
    except ValueError:
        return None


def entero(v):
    """Texto -> int. Tolera '1026.0'. Trunca hacia cero, como el cast de Spark."""
    d = doble(v)
    if d is None or not math.isfinite(d):
        return None
    return int(d)


def tasa(v, enteros=5, decimales=1):
    """Texto -> NUMERIC(enteros, decimales), redondeo HALF_UP. Devuelve float."""
    d = doble(v)
    if d is None or not math.isfinite(d):
        return None
    q = Decimal(repr(d)).quantize(Decimal(1).scaleb(-decimales), rounding=ROUND_HALF_UP)
    if abs(q) >= Decimal(10) ** (enteros - decimales):
        return None
    return float(q)


_VERDADERO = {'t', 'true', 'y', 'yes', '1'}
_FALSO = {'f', 'false', 'n', 'no', '0'}


def booleano(v):
    if v is None:
        return None
    s = v.strip().lower()
    if s in _VERDADERO:
        return True
    if s in _FALSO:
        return False
    return None


# =============================================================================
# Construcción de las nueve tablas
# =============================================================================

def _unidad_kpi(clave, valor_num):
    """Misma cascada de reglas que el ETL. El orden importa: 'mujeres 15–59 en esas
    AGEB' contiene 'mujeres 15' y 'AGEB', y la unidad correcta es mujeres."""
    if valor_num is None:
        return 'texto'
    if '%' in clave:
        return '%'
    if 'h/semana' in clave or 'jornada' in clave:
        return 'horas por semana'
    if 'mujeres 15' in clave:
        return 'mujeres'
    if 'AGEB' in clave:
        return 'AGEB'
    if 'carga directa' in clave:
        return 'personas por cada 100 mujeres'
    return 'valor'


def _etiqueta(clave):
    partes = clave.split('·')
    return partes[1].strip() if len(partes) > 1 else None


def _kpi_cdmx(d):
    filas = []
    for f in d['resumen_cifras_clave']:
        valor = doble(f['valor'])
        filas.append({
            'clave': f['clave'],
            'etiqueta': _etiqueta(f['clave']),
            'valor_num': tasa(f['valor'], enteros=12),
            'valor_texto': f['valor'] if valor is None else None,
            'unidad': _unidad_kpi(f['clave'], valor),
            'nivel_geografico': f['nivel_geografico'],
            'fuente': f['fuente'],
        })

    # La brecha de trabajo no pagado se calcula con la columna SIN redondear: restar
    # las columnas de un decimal da 12.6 en vez de 12.7 (ver diccionario de datos).
    no_pagado = {f['grupo']: doble(f['trabajo_no_pagado_sin_redondear'])
                 for f in d['mujeres_doble_jornada_cdmx']}
    mujeres, hombres = no_pagado.get('Mujeres ocupadas'), no_pagado.get('Hombres ocupados (ref.)')
    brecha = None if mujeres is None or hombres is None else mujeres - hombres
    filas.append({
        'clave': CLAVE_BRECHA_NO_PAGADO,
        'etiqueta': _etiqueta(CLAVE_BRECHA_NO_PAGADO),
        'valor_num': None if brecha is None else tasa(repr(brecha), enteros=12),
        'valor_texto': None,
        'unidad': 'horas por semana',
        'nivel_geografico': 'CDMX',
        'fuente': FTE_ENUT,
    })
    return filas


def _resumen_alcaldia(d):
    # Las tablas por alcaldía solo traen el nombre: se unen por nombre (inner join,
    # como en el ETL) y la clave sale del Censo.
    carga = {f['nom_mun']: f for f in d['mujeres_carga_alcaldia']}
    zonas = {f['nom_mun']: f for f in d['mujeres_zonas_sin_respaldo_alcaldia']}
    cruce = {f['alcaldia']: f for f in d['cruce_oferta_demanda_alcaldia']}
    filas = []
    for c in d['censo2020_alcaldia_cuidado_cdmx']:
        nombre = c['alcaldia']
        if nombre not in carga or nombre not in zonas or nombre not in cruce:
            continue
        ca, zo, cr = carga[nombre], zonas[nombre], cruce[nombre]
        filas.append({
            'cve_mun': c['cve_mun'],
            'alcaldia': nombre,
            'pob_total': entero(c['pob_total']),
            'mujeres_15a59': entero(ca['mujeres_15a59']),
            'pct_60mas': tasa(cr['pct_60mas']),
            'carga_directa_x100_mujeres': tasa(ca['carga_directa_x100_mujeres']),
            'rango_carga': entero(ca['rango_carga_1_mas_alta']),
            'pct_hog_jefa': tasa(ca['pct_hog_jefa']),
            'pct_mujeres_inactivas': tasa(ca['pct_mujeres_inactivas']),
            'agebs': entero(zo['agebs']),
            'agebs_alta_carga': entero(zo['alta_carga']),
            'agebs_sin_respaldo': entero(zo['sin_respaldo']),
            'mujeres_sin_respaldo': entero(zo['mujeres_sin_respaldo']),
            # Benito Juárez no tiene AGEB de alta carga: nulo (no aplica), nunca 0.
            'pct_agebs_alta_carga_sin_respaldo': tasa(zo['pct_ageb_de_alta_carga_sin_respaldo']),
            'guarderias': entero(cr['guarderias']),
            'cuidado_mayores': entero(cr['cuidado_mayores']),
            'ninos_0a5_por_guarderia': tasa(cr['ninos_0a5_por_guarderia'], enteros=10),
            'mayores_60_por_establecimiento': tasa(cr['mayores_60_por_establecimiento'], enteros=10),
            'pct_guarderias_publicas': tasa(cr['pct_guarderias_publicas']),
            'nivel_geografico': 'Alcaldía',
            'fuente': FTE_CRUCE,
        })
    return filas


def _carga_ageb(d):
    return [{
        'cvegeo_ageb': f['cvegeo_ageb'],
        'cve_mun': f['mun'],
        'alcaldia': f['nom_mun'],
        'mujeres_15a59': entero(f['mujeres_15a59']),
        'pob_0a5': entero(f['pob_0a5']),
        'pob_disc_autocuidado': entero(f['pcdisc_mot2']),
        'carga_directa_x100_mujeres': tasa(f['carga_directa_x100_mujeres']),
        'pct_hog_jefa': tasa(f['pct_hog_jefa']),
        'pct_mujeres_inactivas': tasa(f['pct_mujeres_inactivas']),
        'guarderias_1km': entero(f['guarderias_1km']),
        'respaldo_total_1km': entero(f['respaldo_total_1km']),
        'alta_carga': booleano(f['alta_carga']),
        'sin_guarderia': booleano(f['sin_guarderia']),
        'sin_respaldo': booleano(f['sin_respaldo']),
        'lat': doble(f['lat']),
        'lon': doble(f['lon']),
        # TRUE mientras el punto sea la mediana del DENUE y no el centroide oficial.
        'centroide_es_aproximado': True,
        'nivel_geografico': 'AGEB',
        'fuente': FTE_CRUCE,
    } for f in d['mujeres_carga_acceso_ageb']]


def _establecimientos(d):
    # Un CVEGEO del DENUE es válido si existe entre las 2,433 AGEB urbanas del Censo.
    agebs_censo = {f['cvegeo_ageb'] for f in d['censo2020_ageb_cuidado_cdmx']}
    return [{
        'id': f['id'],
        'nom_estab': f['nom_estab'],
        'grupo': f['grupo'],
        'tipo': f['tipo'],
        'sector': f['sector'],
        'per_ocu': f['per_ocu'],
        'codigo_act': f['codigo_act'],
        'cve_mun': f['cve_mun'],
        'alcaldia': f['municipio'],
        'cvegeo_ageb': f['cvegeo_ageb'] if f['cvegeo_ageb'] in agebs_censo else None,
        'es_respaldo': f['codigo_act'] in CODIGOS_RESPALDO,
        'lat': doble(f['lat']),
        'lon': doble(f['lon']),
        'nivel_geografico': 'AGEB',
        'fuente': FTE_DENUE,
    } for f in d['denue_cuidado_cdmx']]


def _enut_carga_actividad(d):
    filas = []
    for f in d['enut2024_cuidados_cdmx_vs_nacional']:
        n = entero(f['n_muestral'])
        filas.append({
            'ambito': f['ambito'],
            'sexo': f['sexo'],
            'actividad': f['actividad'],
            'pct_realiza': tasa(f['pct_que_lo_realiza']),
            'horas_semana': tasa(f['h_semana_quienes_lo_realizan']),
            'n_muestral': n,
            'precision_baja': None if n is None else n < 100,
            'nivel_geografico': f['ambito'],
            'fuente': FTE_ENUT,
        })
    return filas


def _enut_brecha(d):
    return [{
        'actividad': f['actividad'],
        'pct_realiza_mujeres': tasa(f['pct_de_mujeres_que_lo_realiza']),
        'horas_mujeres': tasa(f['h_semana_mujeres_que_lo_realizan']),
        'n_mujeres': entero(f['n_mujeres']),
        'horas_hombres_ref': tasa(f['ref_h_semana_hombres']),
        # Dos decimales a propósito: la razón vale entre 0.98 y 2.12.
        'razon_mujeres_hombres': tasa(f['mujeres_hombres_h'], enteros=4, decimales=2),
        'nivel_geografico': 'CDMX',
        'fuente': FTE_ENUT,
    } for f in d['mujeres_enut_carga_cdmx']]


def _enut_doble_jornada(d):
    return [{
        'grupo': f['grupo'],
        'horas_trabajo_mercado': tasa(f['trabajo_para_el_mercado']),
        'horas_trabajo_domestico': tasa(f['trabajo_domestico_no_remunerado']),
        'horas_cuidado': tasa(f['cuidado_no_remunerado']),
        'horas_jornada_total': tasa(f['total']),
        'n_muestral': entero(f['n']),
        'nivel_geografico': 'CDMX',
        'fuente': FTE_ENUT,
    } for f in d['mujeres_doble_jornada_cdmx']]


def _enut_por_grupo(d):
    def bloque(archivo, tipo_grupo, col_grupo):
        return [{
            'tipo_grupo': tipo_grupo,
            'grupo': f[col_grupo],
            'horas_cuidado': tasa(f['h_semana_de_cuidado_promedio_por_mujer']),
            'pct_que_cuida': tasa(f['pct_que_cuida']),
            'n_muestral': entero(f['n']),
            # El CSV guarda 'sí' / 'no — muestra chica'.
            'confiable': None if f['confiable'] is None else f['confiable'] == 'sí',
            'nivel_geografico': 'CDMX',
            'fuente': FTE_ENUT,
        } for f in d[archivo]]

    return (bloque('mujeres_cuidado_por_condicion', 'Condición de actividad', 'condicion')
            + bloque('mujeres_cuidado_por_edad', 'Grupo de edad', 'grupo_edad'))


# Mismos bloques que BLOQUES_ENASIC en el ETL.
BLOQUES_ENASIC = [
    ('enasic_busqueda_servicios', 'Búsqueda de servicios', 'respuesta',
     'pct_de_mujeres_cuidadoras', 'Mujeres cuidadoras de 15+', False, 'P6_42'),
    ('enasic_razones_no_buscar', 'Razones para no buscar', 'razon',
     'pct_de_mujeres_cuidadoras_que_no_buscaron',
     'Mujeres cuidadoras que no buscaron servicio', True, 'P6_45_01 a P6_45_10'),
    ('enasic_preferencia_cuidado', 'Preferencia de cuidado', 'preferencia',
     'pct_de_mujeres_cuidadoras', 'Mujeres cuidadoras de 15+', False, 'P6_46'),
    ('enasic_disposicion_cuidar', 'Disposición a cuidar', 'indicador',
     'pct_de_mujeres_cuidadoras', 'Mujeres cuidadoras de 15+', False, 'P6_47 / P6_48'),
]


def _enasic(d):
    filas = []
    for archivo, tema, col_cat, col_pct, base, multiple, variable in BLOQUES_ENASIC:
        for f in d[archivo]:
            filas.append({
                'tema': tema,
                'categoria': f[col_cat],
                'pct': tasa(f[col_pct]),
                'base': base,
                'respuesta_multiple': multiple,
                'variable_enasic': variable,
                # Del propio CSV, que ya trae 'Nacional': si algún día la ENASIC se
                # pudiera desagregar, el dato manda.
                'nivel_geografico': f['nivel_geografico'],
                'fuente': FTE_ENASIC,
            })
    return filas


ARCHIVOS = [
    'censo2020_ageb_cuidado_cdmx', 'censo2020_alcaldia_cuidado_cdmx',
    'cruce_oferta_demanda_alcaldia', 'denue_cuidado_cdmx',
    'enasic_busqueda_servicios', 'enasic_disposicion_cuidar',
    'enasic_preferencia_cuidado', 'enasic_razones_no_buscar',
    'enut2024_cuidados_cdmx_vs_nacional', 'mujeres_carga_acceso_ageb',
    'mujeres_carga_alcaldia', 'mujeres_cuidado_por_condicion',
    'mujeres_cuidado_por_edad', 'mujeres_doble_jornada_cdmx',
    'mujeres_enut_carga_cdmx', 'mujeres_zonas_sin_respaldo_alcaldia',
    'resumen_cifras_clave',
]

_CONSTRUCTORES = {
    'kpi_cdmx': _kpi_cdmx,
    'resumen_alcaldia': _resumen_alcaldia,
    'carga_ageb': _carga_ageb,
    'establecimientos_cuidado': _establecimientos,
    'enut_carga_actividad': _enut_carga_actividad,
    'enut_brecha_mujeres_cdmx': _enut_brecha,
    'enut_doble_jornada': _enut_doble_jornada,
    'enut_cuidado_por_grupo': _enut_por_grupo,
    'enasic_cuidadoras': _enasic,
}


def construir(directorio):
    """Devuelve las nueve tablas de `indicadores` como DataFrames (sin normalizar)."""
    d = {nombre: leer(directorio, nombre) for nombre in ARCHIVOS}
    return {tabla: pd.DataFrame(fn(d), columns=esquema.columnas(tabla))
            for tabla, fn in _CONSTRUCTORES.items()}
