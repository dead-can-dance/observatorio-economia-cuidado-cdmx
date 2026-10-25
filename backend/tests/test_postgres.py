"""La ruta de PostgreSQL, con una conexión simulada.

La conexión falsa devuelve lo mismo que devolvería psycopg al leer `indicadores`
(Decimal para NUMERIC, bool, int, None), construido a partir de la réplica en CSV. Así
se prueba que las dos fuentes terminan en tablas idénticas sin necesitar Docker.
"""

import math
import re
from decimal import Decimal

import pandas as pd
import psycopg
import pytest

from observatorio import esquema, fuente_csv, fuente_postgres
from observatorio.configuracion import cargar_configuracion
from observatorio.repositorio import cargar_repositorio


def _como_psycopg(valor, tipo):
    if valor is None or (isinstance(valor, float) and math.isnan(valor)) or valor is pd.NA:
        return None
    if tipo == esquema.DECIMAL:
        return Decimal(repr(float(valor)))
    if tipo == esquema.ENTERO:
        return int(valor)
    if tipo == esquema.BOOLEANO:
        return bool(valor)
    return valor


class ConexionFalsa:
    def __init__(self, tablas, vacia=None):
        self.tablas, self.vacia, self.read_only = tablas, vacia, False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, consulta):
        tabla = re.search(r'FROM indicadores\."(\w+)"', consulta.as_string(None)).group(1)
        tipos = dict(esquema.TABLAS[tabla]['columnas'])
        df = self.tablas[tabla]
        filas = [] if tabla == self.vacia else [
            tuple(_como_psycopg(v, tipos[c]) for c, v in zip(df.columns, fila))
            for fila in df.itertuples(index=False, name=None)]
        return type('Cursor', (), {'fetchall': lambda _self: filas})()


@pytest.fixture(scope='module')
def crudas(cfg):
    return fuente_csv.construir(cfg.dir_curada)


def test_postgres_y_csv_dan_tablas_identicas(monkeypatch, crudas, repo):
    monkeypatch.setattr(psycopg, 'connect', lambda **kw: ConexionFalsa(crudas))
    cfg = cargar_configuracion(fuente='postgres', pg_clave='secreta')
    desde_pg = cargar_repositorio(cfg)
    assert desde_pg.fuente == 'postgres'
    assert desde_pg.controles_ok
    for tabla in esquema.TABLAS:
        pd.testing.assert_frame_equal(desde_pg.tabla(tabla), repo.tabla(tabla), obj=tabla)


def test_conexion_con_el_rol_tablero(monkeypatch, crudas):
    recibido = {}

    def conectar(**kw):
        recibido.update(kw)
        return ConexionFalsa(crudas)

    monkeypatch.setattr(psycopg, 'connect', conectar)
    cargar_repositorio(cargar_configuracion(fuente='postgres', pg_clave='secreta'))
    assert recibido['user'] == 'tablero'
    assert recibido['password'] == 'secreta'


def test_auto_cae_a_csv_si_la_base_no_responde(monkeypatch):
    def falla(**kw):
        raise psycopg.OperationalError('connection refused')

    monkeypatch.setattr(psycopg, 'connect', falla)
    repo = cargar_repositorio(cargar_configuracion(fuente='auto', pg_clave='secreta'))
    assert repo.fuente == 'csv'
    assert 'PostgreSQL no disponible' in repo.aviso
    assert repo.controles_ok


def test_modo_postgres_falla_si_la_base_no_responde(monkeypatch):
    def falla(**kw):
        raise psycopg.OperationalError('connection refused')

    monkeypatch.setattr(psycopg, 'connect', falla)
    with pytest.raises(fuente_postgres.BaseNoDisponible):
        cargar_repositorio(cargar_configuracion(fuente='postgres', pg_clave='secreta'))


def test_base_sin_etl_se_reporta(monkeypatch, crudas):
    monkeypatch.setattr(psycopg, 'connect', lambda **kw: ConexionFalsa(crudas, vacia='kpi_cdmx'))
    repo = cargar_repositorio(cargar_configuracion(fuente='auto', pg_clave='secreta'))
    assert repo.fuente == 'csv'
    assert 'falta correr el ETL' in repo.aviso


def test_auto_sin_clave_no_intenta_conectar(monkeypatch):
    def no_deberia(**kw):
        raise AssertionError('no debió intentar conectarse')

    monkeypatch.setattr(psycopg, 'connect', no_deberia)
    repo = cargar_repositorio(cargar_configuracion(fuente='auto', pg_clave=None))
    assert repo.fuente == 'csv'
