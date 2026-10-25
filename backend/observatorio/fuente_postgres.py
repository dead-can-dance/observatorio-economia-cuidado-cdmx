"""Lee el esquema `indicadores` de PostgreSQL, como pide el README.

Se conecta con el rol `tablero` (solo SELECT sobre `indicadores`, lo crea
sql/02_usuario_tablero.sql) y nunca toca `cruda` ni `curada`. La sesión además se
marca de solo lectura: el tablero no escribe en la base.
"""

import pandas as pd

from . import esquema


class BaseNoDisponible(RuntimeError):
    """La base no responde, rechaza las credenciales o todavía no tiene datos."""


def leer(cfg):
    """Devuelve las nueve tablas de `indicadores` como DataFrames (sin normalizar)."""
    try:
        import psycopg
        from psycopg import sql
    except ImportError as e:  # pragma: no cover - depende del entorno
        raise BaseNoDisponible('falta el paquete psycopg (pip install "psycopg[binary]")') from e

    if not cfg.pg_clave:
        raise BaseNoDisponible('no hay TABLERO_PASSWORD en .env')

    try:
        conexion = psycopg.connect(
            host=cfg.pg_host, port=cfg.pg_puerto, dbname=cfg.pg_base,
            user=cfg.pg_usuario, password=cfg.pg_clave,
            connect_timeout=3, application_name='observatorio-tablero',
        )
    except psycopg.Error as e:
        raise BaseNoDisponible(_primera_linea(e)) from e

    tablas = {}
    try:
        with conexion:
            conexion.read_only = True
            for tabla in esquema.TABLAS:
                cols = esquema.columnas(tabla)
                consulta = sql.SQL('SELECT {} FROM indicadores.{}').format(
                    sql.SQL(', ').join(sql.Identifier(c) for c in cols),
                    sql.Identifier(tabla),
                )
                filas = conexion.execute(consulta).fetchall()
                if not filas:
                    raise BaseNoDisponible(
                        f'indicadores.{tabla} está vacía: falta correr el ETL '
                        '(docker compose up --build)')
                tablas[tabla] = pd.DataFrame(filas, columns=cols)
    except psycopg.Error as e:
        raise BaseNoDisponible(_primera_linea(e)) from e
    return tablas


def _primera_linea(error):
    texto = str(error).strip()
    return texto.splitlines()[0] if texto else type(error).__name__
