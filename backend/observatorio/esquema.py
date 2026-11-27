"""Las quince tablas del esquema `indicadores`, tal como las define sql/01_esquemas.sql.

Nueve son el diagnóstico descriptivo (notebook 02) y seis la capa analítica del trabajo
integrador (notebook 03): serie histórica de la oferta, pronóstico, validación de modelos,
coeficientes del modelo de horas de cuidado, horas por AGEB y escenarios del programa.

Es el contrato entre el backend y sus dos fuentes posibles (PostgreSQL o los CSV de
data/curada/): cualquiera de las dos debe entregar exactamente estas columnas, con
estos tipos. El tablero no lee nada fuera de este esquema (ver docs/diccionario_datos.md).

Después de cargar, cada tabla se normaliza aquí mismo: tipos de pandas fijos y un orden
de filas determinista. Así la API responde lo mismo venga de donde venga el dato.
"""

import math
from decimal import Decimal

import pandas as pd

# Tipos lógicos. Se mapean a dtypes de pandas en normalizar().
TEXTO = 'texto'          # TEXT
ENTERO = 'entero'        # INTEGER
DECIMAL = 'decimal'      # NUMERIC(p, s); llega ya redondeado y se guarda como float
BOOLEANO = 'booleano'    # BOOLEAN
FLOTANTE = 'flotante'    # DOUBLE PRECISION (coordenadas)

_CONTEXTO = [('nivel_geografico', TEXTO), ('fuente', TEXTO)]

# Orden de presentación de las categorías que tienen uno natural. Lo que no aparece
# aquí se ordena por la llave primaria. El orden de las actividades es el de los
# notebooks; el de edad es ordinal.
ACTIVIDADES_ENUT = [
    'Cuidado a integrantes del hogar (total)',
    'Cuidado a niñas/os de 0 a 5',
    'Cuidado a personas de 60+',
    'Cuidados especiales (enfermedad o discapacidad)',
]
ACTIVIDADES_BRECHA = [
    'Cuidado a integrantes del hogar (total)',
    'Cuidado a niñas y niños de 0 a 5',
    'Cuidado a niñas y niños de 6 a 14',
    'Cuidado a personas de 60+',
    'Cuidados especiales (enfermedad o discapacidad)',
    'Trabajo doméstico no remunerado',
]
GRUPOS_EDAD = ['12–17', '18–29', '30–44', '45–59', '60+']
CONDICIONES = [
    'Ocupada', 'Dedicada al hogar o al cuidado', 'Estudiante',
    'Jubilada o pensionada', 'Desocupada', 'Otra situación',
]
TEMAS_ENASIC = [
    'Búsqueda de servicios', 'Razones para no buscar',
    'Preferencia de cuidado', 'Disposición a cuidar',
]
TIPOS_RESPALDO = ['Guardería', 'Residencia / asilo', 'Centro de día']
SERIES_OFERTA = ['Total de respaldo'] + TIPOS_RESPALDO
METODOS_PRONOSTICO = ['Ingenuo', 'Suavizamiento simple', 'Holt amortiguado', 'Deriva', 'ARIMA(0,1,1)']
METRICAS = ['MAPE', 'RMSE', 'MAE', 'R2']
VARIABLES_MODELO = ['constante', 'n_0a5', 'n_6a14', 'n_60mas', 'n_disc', 'tam', 'edad_15a24',
                    'edad_50a59', 'ocupada', 'anios_esc', 'jefa_hog', 'urbana']
ESCENARIOS_PROGRAMA = ['Pesimista', 'Realista', 'Optimista', 'Valor esperado', 'Zona del programa']

TABLAS = {
    'kpi_cdmx': {
        'columnas': [
            ('clave', TEXTO), ('etiqueta', TEXTO), ('valor_num', DECIMAL),
            ('valor_texto', TEXTO), ('unidad', TEXTO), *_CONTEXTO,
        ],
        'llave': ['clave'],
        'filas': 13,
    },
    'resumen_alcaldia': {
        'columnas': [
            ('cve_mun', TEXTO), ('alcaldia', TEXTO), ('pob_total', ENTERO),
            ('mujeres_15a59', ENTERO), ('pct_60mas', DECIMAL),
            ('carga_directa_x100_mujeres', DECIMAL), ('rango_carga', ENTERO),
            ('pct_hog_jefa', DECIMAL), ('pct_mujeres_inactivas', DECIMAL),
            ('agebs', ENTERO), ('agebs_alta_carga', ENTERO),
            ('agebs_sin_respaldo', ENTERO), ('mujeres_sin_respaldo', ENTERO),
            ('pct_agebs_alta_carga_sin_respaldo', DECIMAL), ('guarderias', ENTERO),
            ('cuidado_mayores', ENTERO), ('ninos_0a5_por_guarderia', DECIMAL),
            ('mayores_60_por_establecimiento', DECIMAL),
            ('pct_guarderias_publicas', DECIMAL), *_CONTEXTO,
        ],
        'llave': ['cve_mun'],
        'filas': 16,
    },
    'carga_ageb': {
        'columnas': [
            ('cvegeo_ageb', TEXTO), ('cve_mun', TEXTO), ('alcaldia', TEXTO),
            ('mujeres_15a59', ENTERO), ('pob_0a5', ENTERO),
            ('pob_disc_autocuidado', ENTERO), ('carga_directa_x100_mujeres', DECIMAL),
            ('pct_hog_jefa', DECIMAL), ('pct_mujeres_inactivas', DECIMAL),
            ('guarderias_1km', ENTERO), ('respaldo_total_1km', ENTERO),
            ('alta_carga', BOOLEANO), ('sin_guarderia', BOOLEANO),
            ('sin_respaldo', BOOLEANO), ('lat', FLOTANTE), ('lon', FLOTANTE),
            ('centroide_es_aproximado', BOOLEANO), *_CONTEXTO,
        ],
        'llave': ['cvegeo_ageb'],
        'filas': 2320,
    },
    'establecimientos_cuidado': {
        'columnas': [
            ('id', TEXTO), ('nom_estab', TEXTO), ('grupo', TEXTO), ('tipo', TEXTO),
            ('sector', TEXTO), ('per_ocu', TEXTO), ('codigo_act', TEXTO),
            ('cve_mun', TEXTO), ('alcaldia', TEXTO), ('cvegeo_ageb', TEXTO),
            ('es_respaldo', BOOLEANO), ('lat', FLOTANTE), ('lon', FLOTANTE),
            *_CONTEXTO,
        ],
        'llave': ['id'],
        'filas': 1463,
    },
    'enut_carga_actividad': {
        'columnas': [
            ('ambito', TEXTO), ('sexo', TEXTO), ('actividad', TEXTO),
            ('pct_realiza', DECIMAL), ('horas_semana', DECIMAL),
            ('n_muestral', ENTERO), ('precision_baja', BOOLEANO), *_CONTEXTO,
        ],
        'llave': ['ambito', 'sexo', 'actividad'],
        'orden': {'ambito': ['CDMX', 'Nacional'], 'sexo': ['Mujeres', 'Hombres'],
                  'actividad': ACTIVIDADES_ENUT},
        'filas': 16,
    },
    'enut_brecha_mujeres_cdmx': {
        'columnas': [
            ('actividad', TEXTO), ('pct_realiza_mujeres', DECIMAL),
            ('horas_mujeres', DECIMAL), ('n_mujeres', ENTERO),
            ('horas_hombres_ref', DECIMAL), ('razon_mujeres_hombres', DECIMAL),
            *_CONTEXTO,
        ],
        'llave': ['actividad'],
        'orden': {'actividad': ACTIVIDADES_BRECHA},
        'filas': 6,
    },
    'enut_doble_jornada': {
        'columnas': [
            ('grupo', TEXTO), ('horas_trabajo_mercado', DECIMAL),
            ('horas_trabajo_domestico', DECIMAL), ('horas_cuidado', DECIMAL),
            ('horas_jornada_total', DECIMAL), ('n_muestral', ENTERO), *_CONTEXTO,
        ],
        'llave': ['grupo'],
        'orden': {'grupo': ['Mujeres ocupadas', 'Hombres ocupados (ref.)']},
        'filas': 2,
    },
    'enut_cuidado_por_grupo': {
        'columnas': [
            ('tipo_grupo', TEXTO), ('grupo', TEXTO), ('horas_cuidado', DECIMAL),
            ('pct_que_cuida', DECIMAL), ('n_muestral', ENTERO),
            ('confiable', BOOLEANO), *_CONTEXTO,
        ],
        'llave': ['tipo_grupo', 'grupo'],
        'orden': {'tipo_grupo': ['Grupo de edad', 'Condición de actividad'],
                  'grupo': GRUPOS_EDAD + CONDICIONES},
        'filas': 11,
    },
    'enasic_cuidadoras': {
        'columnas': [
            ('tema', TEXTO), ('categoria', TEXTO), ('pct', DECIMAL), ('base', TEXTO),
            ('respuesta_multiple', BOOLEANO), ('variable_enasic', TEXTO), *_CONTEXTO,
        ],
        'llave': ['tema', 'categoria'],
        # Dentro de cada tema, de la respuesta más frecuente a la menos frecuente.
        'orden': {'tema': TEMAS_ENASIC},
        'orden_desc': 'pct',
        'filas': 19,
    },
    # --- Capa analítica (notebook 03): serie histórica, pronóstico, modelo y escenarios ---
    'oferta_historica': {
        'columnas': [
            ('edicion', TEXTO), ('periodo', TEXTO), ('tipo', TEXTO), ('sector', TEXTO),
            ('establecimientos', ENTERO), *_CONTEXTO,
        ],
        'llave': ['edicion', 'tipo', 'sector'],
        'orden': {'tipo': TIPOS_RESPALDO, 'sector': ['Privado', 'Público']},
        'orden_primero': ['edicion'],
        'filas': 114,
    },
    'pronostico_oferta': {
        'columnas': [
            ('serie', TEXTO), ('metodo', TEXTO), ('periodo', TEXTO), ('horizonte', ENTERO),
            ('pronostico', DECIMAL), ('li_80', DECIMAL), ('ls_80', DECIMAL),
            ('li_95', DECIMAL), ('ls_95', DECIMAL), ('elegido', BOOLEANO), *_CONTEXTO,
        ],
        'llave': ['serie', 'metodo', 'periodo'],
        'orden': {'serie': SERIES_OFERTA, 'metodo': METODOS_PRONOSTICO},
        'filas': 60,
    },
    'validacion_modelos': {
        'columnas': [
            ('modelo', TEXTO), ('tarea', TEXTO), ('conjunto', TEXTO), ('metrica', TEXTO),
            ('valor', DECIMAL), ('n_evaluaciones', ENTERO), ('elegido', BOOLEANO), *_CONTEXTO,
        ],
        'llave': ['tarea', 'conjunto', 'modelo', 'metrica'],
        'orden': {'metrica': METRICAS},
        'orden_primero': ['tarea', 'conjunto', 'modelo'],
        'filas': 56,
    },
    'modelo_horas_coeficientes': {
        'columnas': [
            ('variable', TEXTO), ('descripcion', TEXTO), ('coeficiente', DECIMAL),
            ('variable_censo', TEXTO), *_CONTEXTO,
        ],
        'llave': ['variable'],
        'orden': {'variable': VARIABLES_MODELO},
        'filas': 12,
    },
    'horas_cuidado_ageb': {
        'columnas': [
            ('cvegeo_ageb', TEXTO), ('cve_mun', TEXTO), ('alcaldia', TEXTO),
            ('mujeres_15a59', ENTERO), ('horas_mujer_semana', DECIMAL),
            ('horas_semana_total', ENTERO), ('alta_carga', BOOLEANO), ('sin_respaldo', BOOLEANO),
            ('variables_imputadas', BOOLEANO), *_CONTEXTO,
        ],
        'llave': ['cvegeo_ageb'],
        'filas': 2320,
    },
    'escenarios_programa': {
        'columnas': [
            ('escenario', TEXTO), ('indicador', TEXTO), ('valor', DECIMAL), ('unidad', TEXTO),
            *_CONTEXTO,
        ],
        'llave': ['escenario', 'indicador'],
        'orden': {'escenario': ESCENARIOS_PROGRAMA},
        'filas': 74,
    },
}


def columnas(tabla):
    """Nombres de columna de una tabla, en el orden del DDL."""
    return [c for c, _ in TABLAS[tabla]['columnas']]


def _a_python(v):
    """Lleva cualquier valor de pandas/numpy/psycopg a un escalar de Python o None."""
    if v is None or v is pd.NA:
        return None
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, float) and math.isnan(v):
        return None
    if hasattr(v, 'item'):            # escalares de numpy
        v = v.item()
        if isinstance(v, float) and math.isnan(v):
            return None
    return v


def _serie(valores, tipo):
    valores = [_a_python(v) for v in valores]
    if tipo == TEXTO:
        return pd.Series([None if v is None else str(v) for v in valores], dtype=object)
    if tipo == ENTERO:
        return pd.Series([None if v is None else int(v) for v in valores], dtype='Int64')
    if tipo == BOOLEANO:
        return pd.Series([None if v is None else bool(v) for v in valores], dtype='boolean')
    # DECIMAL y FLOTANTE
    return pd.Series([math.nan if v is None else float(v) for v in valores], dtype='float64')


def normalizar(tabla, df):
    """Fija columnas, tipos y orden de filas de una tabla de `indicadores`.

    Falla si falta una columna del DDL: preferimos un error al arrancar que una
    gráfica vacía sin explicación.
    """
    definicion = TABLAS[tabla]
    faltantes = [c for c in columnas(tabla) if c not in df.columns]
    if faltantes:
        raise ValueError(f'indicadores.{tabla}: faltan columnas {faltantes}')

    datos = {c: _serie(df[c].tolist(), tipo) for c, tipo in definicion['columnas']}
    salida = pd.DataFrame(datos)

    # Orden determinista: primero las columnas de `orden_primero` (p. ej. la edición del
    # DENUE), luego las categorías con orden natural y al final la llave.
    claves_orden = list(definicion.get('orden_primero', []))
    for col, categorias in definicion.get('orden', {}).items():
        posicion = {c: i for i, c in enumerate(categorias)}
        aux = f'_orden_{col}'
        salida[aux] = salida[col].map(lambda v: posicion.get(v, len(posicion)))
        claves_orden.append(aux)
    ascendente = [True] * len(claves_orden)
    if 'orden_desc' in definicion:
        claves_orden.append(definicion['orden_desc'])
        ascendente.append(False)
    claves_orden += definicion['llave']
    ascendente += [True] * len(definicion['llave'])

    salida = salida.sort_values(claves_orden, ascending=ascendente, kind='stable')
    salida = salida.drop(columns=[c for c in salida.columns if c.startswith('_orden_')])
    return salida.reset_index(drop=True)


def a_registros(df):
    """DataFrame -> lista de dicts listos para JSON (NaN y NA se vuelven None)."""
    nombres = list(df.columns)
    return [{c: _a_python(v) for c, v in zip(nombres, fila)}
            for fila in df.itertuples(index=False, name=None)]
