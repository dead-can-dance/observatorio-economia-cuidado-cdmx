"""Datos de la app: las quince tablas del esquema `indicadores`, cargadas una sola vez.

Reutiliza el backend del observatorio web (backend/observatorio): la misma réplica del
ETL, las mismas cifras de control y los mismos hallazgos redactados. Así la app de
Streamlit y la página web no pueden contar cosas distintas.

En Streamlit Community Cloud no hay .env ni PostgreSQL: las tablas se reconstruyen desde
data/curada/ y la página de Metodología dice qué fuente se usó.
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ / 'backend') not in sys.path:
    sys.path.insert(0, str(RAIZ / 'backend'))

from observatorio import analisis, factibilidad, metodologia  # noqa: E402,F401
from observatorio.configuracion import cargar_configuracion  # noqa: E402
from observatorio.esquema import TABLAS, TEMAS_ENASIC  # noqa: E402,F401
from observatorio.fuente_csv import CLAVE_BRECHA_NO_PAGADO  # noqa: E402
from observatorio.repositorio import cargar_repositorio  # noqa: E402

TOTAL_CUIDADO = analisis.TOTAL_CUIDADO
INDICADORES_ALCALDIA = analisis.INDICADORES_ALCALDIA

# Claves de indicadores.kpi_cdmx que usa la app.
KPI_PCT_CUIDAN = 'ENUT · % mujeres CDMX que cuidan'
KPI_HORAS_CUIDAN = 'ENUT · h/semana mujeres que cuidan'
KPI_HORAS_HOMBRES = 'ENUT · ref. h/semana hombres que cuidan'
KPI_JORNADA_MUJERES = 'ENUT · jornada total mujeres ocupadas (h)'
KPI_JORNADA_HOMBRES = 'ENUT · jornada total hombres ocupados (h, ref.)'
KPI_CARGA_CDMX = 'Censo · carga directa x100 mujeres, CDMX'
KPI_BRECHA = CLAVE_BRECHA_NO_PAGADO


@st.cache_resource(show_spinner='Cargando las tablas de indicadores…')
def repositorio():
    return cargar_repositorio(cargar_configuracion())


def tabla(nombre):
    return repositorio().tabla(nombre)


def kpi(clave):
    df = tabla('kpi_cdmx')
    fila = df[df['clave'] == clave]
    if fila.empty or pd.isna(fila['valor_num'].iloc[0]):
        return None
    return float(fila['valor_num'].iloc[0])


@st.cache_data(show_spinner=False)
def hallazgos(nivel):
    funcion = {'nacional': analisis.hallazgos_nacionales, 'cdmx': analisis.hallazgos_cdmx,
               'alcaldias': analisis.hallazgos_alcaldias}[nivel]
    return funcion(repositorio())


@st.cache_data(show_spinner=False)
def contexto_ciudad():
    return analisis.contexto_ciudad(repositorio())


@st.cache_data(show_spinner=False)
def ficha_alcaldia(cve_mun):
    return analisis.ficha_alcaldia(repositorio(), cve_mun)


@st.cache_data(show_spinner=False)
def territorio(cve_mun=None):
    repo = repositorio()
    return {**analisis.resumen_agebs(repo, cve_mun), **analisis.histograma_carga(repo, cve_mun)}


def alcaldias_alfabetico():
    alc = tabla('resumen_alcaldia')
    # Sin acentos para ordenar: Álvaro Obregón va con la A, no al final.
    sin_acentos = lambda s: s.str.normalize('NFD').str.replace('[̀-ͯ]', '', regex=True)
    return alc.sort_values('alcaldia', key=sin_acentos).reset_index(drop=True)


def alcaldia_por_omision():
    """La ficha abre en la alcaldía con más mujeres en zonas sin respaldo, como la web."""
    alc = tabla('resumen_alcaldia')
    return alc.sort_values('mujeres_sin_respaldo', ascending=False)['cve_mun'].iloc[0]


def nombre_alcaldia(cve_mun):
    alc = tabla('resumen_alcaldia')
    fila = alc[alc['cve_mun'] == cve_mun]
    return None if fila.empty else fila['alcaldia'].iloc[0]


def csv_indicadores(nombre):
    # utf-8-sig: con BOM, Excel abre bien los acentos (Álvaro Obregón, Tláhuac).
    return tabla(nombre).to_csv(index=False).encode('utf-8-sig')
