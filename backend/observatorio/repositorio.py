"""Carga las quince tablas de `indicadores` en memoria y verifica las cifras de control.

Son ~6,700 filas: caben de sobra en memoria, así que se leen una vez al arrancar y la
API responde sin volver a la fuente.

Fuente de datos (OBSERVATORIO_FUENTE):

  postgres  Lee `indicadores` con el rol `tablero`. Si la base no responde, falla.
  csv       Reconstruye `indicadores` desde data/curada/ (réplica del ETL).
  auto      Intenta PostgreSQL; si no está disponible, usa los CSV y lo avisa.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime

from . import esquema, factibilidad, fuente_csv, fuente_postgres

log = logging.getLogger('observatorio')


# Cifras que deben reproducirse en cada arranque: las del reporte de control del ETL
# más las del README. El tablero las muestra; si alguna no cuadra, lo avisa en pantalla.
def _kpi(tablas, clave):
    df = tablas['kpi_cdmx']
    fila = df[df['clave'] == clave]
    return None if fila.empty else round(float(fila['valor_num'].iloc[0]), 1)


def _escenario(tablas, escenario, indicador):
    df = _primero(tablas['escenarios_programa'], escenario=escenario, indicador=indicador)
    return None if df.empty or df['valor'].isna().iloc[0] else round(float(df['valor'].iloc[0]))


def _primero(df, **filtros):
    for col, valor in filtros.items():
        df = df[df[col] == valor]
    return df


CONTROLES = [
    ('Establecimientos de cuidado del DENUE',
     lambda t: len(t['establecimientos_cuidado']), 1463),
    ('Establecimientos que cuentan como respaldo',
     lambda t: int(t['establecimientos_cuidado']['es_respaldo'].sum()), 838),
    ('AGEB con carga alta y sin respaldo a 1 km',
     lambda t: int(t['carga_ageb']['sin_respaldo'].sum()), 88),
    ('Mujeres de 15 a 59 en esas AGEB',
     lambda t: int(t['carga_ageb'].loc[t['carga_ageb']['sin_respaldo'].fillna(False),
                                       'mujeres_15a59'].sum()), 125256),
    ('Alcaldías en indicadores.resumen_alcaldia',
     lambda t: len(t['resumen_alcaldia']), 16),
    ('Brecha ENUT de trabajo no pagado (h)',
     lambda t: _kpi(t, fuente_csv.CLAVE_BRECHA_NO_PAGADO), 12.7),
    ('% de mujeres de la CDMX que cuidan (ENUT)',
     lambda t: round(float(_primero(t['enut_brecha_mujeres_cdmx'],
                                    actividad='Cuidado a integrantes del hogar (total)')
                           ['pct_realiza_mujeres'].iloc[0]), 1), 62.2),
    ('Jornada total de mujeres ocupadas (ENUT)',
     lambda t: round(float(_primero(t['enut_doble_jornada'], grupo='Mujeres ocupadas')
                           ['horas_jornada_total'].iloc[0]), 1), 77.0),
    ('% de cuidadoras que prefiere cuidado en casa (ENASIC)',
     lambda t: round(float(_primero(t['enasic_cuidadoras'], tema='Preferencia de cuidado',
                                    categoria='En su casa')['pct'].iloc[0]), 1), 61.2),
    # Capa analítica. La serie histórica del DENUE debe cerrar en el conteo de la edición
    # actual, y la tabla de escenarios debe ser la que produce hoy el modelo financiero:
    # si alguien cambia un supuesto en factibilidad.py sin volver a correr el notebook 03,
    # este control lo avisa.
    ('Respaldo DENUE 05/2026 en la serie histórica',
     lambda t: int(t['oferta_historica'].loc[t['oferta_historica']['edicion'] == '2026-05',
                                             'establecimientos'].sum()), 838),
    ('VAN realista del programa (coincide con factibilidad.py)',
     lambda t: _escenario(t, 'Realista', 'VAN'),
     round(factibilidad.evaluar(factibilidad.ESCENARIOS['Realista']).van)),
]


@dataclass
class Repositorio:
    tablas: dict
    fuente: str                 # 'postgres' o 'csv'
    detalle: str                # descripción legible de la fuente
    aviso: str | None = None    # por qué no se usó PostgreSQL, si aplica
    cargado_en: datetime = field(default_factory=datetime.now)
    controles: list = field(default_factory=list)

    def tabla(self, nombre):
        return self.tablas[nombre]

    @property
    def controles_ok(self):
        return all(c['ok'] for c in self.controles)


def evaluar_controles(tablas):
    resultados = []
    for etiqueta, calcular, esperado in CONTROLES:
        try:
            obtenido = calcular(tablas)
        except Exception as e:  # una tabla incompleta no debe tumbar el arranque
            log.warning('Control %r no se pudo calcular: %s', etiqueta, e)
            obtenido = None
        resultados.append({'etiqueta': etiqueta, 'esperado': esperado,
                           'obtenido': obtenido, 'ok': obtenido == esperado})
    for tabla, definicion in esquema.TABLAS.items():
        filas = len(tablas[tabla])
        resultados.append({'etiqueta': f'Filas en indicadores.{tabla}',
                           'esperado': definicion['filas'], 'obtenido': filas,
                           'ok': filas == definicion['filas']})
    return resultados


def cargar_repositorio(cfg):
    aviso = None
    tablas = None
    fuente = detalle = None

    if cfg.fuente in ('postgres', 'auto'):
        destino = (f'PostgreSQL {cfg.pg_host}:{cfg.pg_puerto}/{cfg.pg_base}, '
                   f'esquema indicadores, usuario {cfg.pg_usuario}')
        if cfg.fuente == 'auto' and not cfg.pg_clave:
            aviso = ('No hay .env con TABLERO_PASSWORD, así que no se intentó PostgreSQL.'
                     if not cfg.hay_env else
                     'El .env no trae TABLERO_PASSWORD, así que no se intentó PostgreSQL.')
        else:
            try:
                tablas = fuente_postgres.leer(cfg)
                fuente, detalle = 'postgres', destino
            except fuente_postgres.BaseNoDisponible as e:
                if cfg.fuente == 'postgres':
                    raise
                aviso = f'PostgreSQL no disponible ({e}).'

    if tablas is None:
        tablas = fuente_csv.construir(cfg.dir_curada)
        fuente = 'csv'
        detalle = ('CSV de data/curada/, transformados con las mismas reglas que '
                   'etl/cargar_capas.py')

    tablas = {nombre: esquema.normalizar(nombre, df) for nombre, df in tablas.items()}
    repo = Repositorio(tablas=tablas, fuente=fuente, detalle=detalle, aviso=aviso)
    repo.controles = evaluar_controles(tablas)
    return repo
