"""Rutas de la API del observatorio (todas bajo /api).

Cada respuesta con cifras lleva `fuente` y `nivel_geografico`: ninguna cifra se publica
sin ellos (docs/diccionario_datos.md). Donde el diccionario prohíbe una lectura, la API
la impide en vez de confiar en el cliente: por ejemplo, `cuidado-por-grupo` exige
`tipo_grupo` porque mezclar las dos desagregaciones da un total sin sentido.
"""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from fastapi.responses import Response

from . import __version__, analisis, metodologia
from .esquema import TABLAS, TEMAS_ENASIC, a_registros
from .fuente_csv import CLAVE_BRECHA_NO_PAGADO

router = APIRouter(prefix='/api')

CVE_MUN = Path(pattern=r'^\d{3}$', description='Clave de alcaldía, 3 dígitos (002 a 017).')
NombreTabla = Literal[tuple(TABLAS)]
TemaEnasic = Literal[tuple(TEMAS_ENASIC)]


def repositorio(request: Request):
    return request.app.state.repositorio


def paquete(df, sin_columnas=()):
    """Filas más el contexto obligatorio. `sin_columnas` quita columnas constantes de
    cada fila (la fuente y el nivel quedan arriba) para aligerar las capas del mapa."""
    contexto = {
        'fuente': sorted(df['fuente'].dropna().unique().tolist()),
        'nivel_geografico': sorted(df['nivel_geografico'].dropna().unique().tolist()),
    }
    filas = df.drop(columns=list(sin_columnas)) if sin_columnas else df
    return {**contexto, 'filas': a_registros(filas)}


# =============================================================================
# Sistema
# =============================================================================

@router.get('/estado', tags=['sistema'], summary='Fuente de datos activa y cifras de control')
def estado(repo=Depends(repositorio)):
    return {
        'version': __version__,
        'fuente': repo.fuente,
        'detalle': repo.detalle,
        'aviso': repo.aviso,
        'cargado_en': repo.cargado_en.isoformat(timespec='seconds'),
        'controles_ok': repo.controles_ok,
        'controles': repo.controles,
        'tablas': {nombre: len(df) for nombre, df in repo.tablas.items()},
    }


@router.get('/metodologia', tags=['sistema'],
            summary='Fuentes, advertencias de lectura y glosario')
def ver_metodologia():
    return metodologia.contenido()


@router.get('/indicadores/{tabla}.csv', tags=['descargas'],
            summary='Descarga una tabla del esquema indicadores en CSV')
def descargar_csv(tabla: NombreTabla, repo=Depends(repositorio)):
    # utf-8-sig: con BOM, Excel abre bien los acentos (Álvaro Obregón, Tláhuac).
    contenido = repo.tabla(tabla).to_csv(index=False).encode('utf-8-sig')
    return Response(contenido, media_type='text/csv; charset=utf-8', headers={
        'Content-Disposition': f'attachment; filename="indicadores_{tabla}.csv"'})


@router.get('/indicadores/{tabla}', tags=['descargas'],
            summary='Una tabla del esquema indicadores, completa, en JSON')
def ver_tabla(tabla: NombreTabla, repo=Depends(repositorio)):
    return paquete(repo.tabla(tabla))


# =============================================================================
# Portada y nivel nacional
# =============================================================================

@router.get('/kpis', tags=['portada'], summary='Cifras de cabecera (indicadores.kpi_cdmx)')
def kpis(nivel: Literal['CDMX', 'Nacional'] | None = Query(
        None, description='Filtra por nivel geográfico. Las cifras de ENASIC son Nacional.'),
        repo=Depends(repositorio)):
    df = repo.tabla('kpi_cdmx')
    if nivel:
        df = df[df['nivel_geografico'] == nivel]
    return paquete(df)


@router.get('/hallazgos/{nivel}', tags=['hallazgos'],
            summary='Hallazgos redactados para un nivel geográfico')
def hallazgos(nivel: Literal['nacional', 'cdmx', 'alcaldias'], repo=Depends(repositorio)):
    funcion = {'nacional': analisis.hallazgos_nacionales, 'cdmx': analisis.hallazgos_cdmx,
               'alcaldias': analisis.hallazgos_alcaldias}[nivel]
    return {'nivel': nivel, 'hallazgos': funcion(repo)}


# =============================================================================
# ENUT 2024
# =============================================================================

@router.get('/enut/carga-actividad', tags=['ENUT 2024'],
            summary='Cuidado por actividad: CDMX contra nacional, mujeres y referencia')
def enut_carga_actividad(
        ambito: Literal['CDMX', 'Nacional'] | None = None,
        sexo: Literal['Mujeres', 'Hombres'] | None = Query(
            None, description='Los hombres son referencia para medir la brecha.'),
        repo=Depends(repositorio)):
    df = repo.tabla('enut_carga_actividad')
    if ambito:
        df = df[df['ambito'] == ambito]
    if sexo:
        df = df[df['sexo'] == sexo]
    return paquete(df)


@router.get('/enut/brecha', tags=['ENUT 2024'],
            summary='Brecha de cuidado de las mujeres de la CDMX por actividad')
def enut_brecha(repo=Depends(repositorio)):
    return paquete(repo.tabla('enut_brecha_mujeres_cdmx'))


@router.get('/enut/doble-jornada', tags=['ENUT 2024'],
            summary='Hallazgo A: la doble jornada de las mujeres ocupadas')
def enut_doble_jornada(repo=Depends(repositorio)):
    kpi = repo.tabla('kpi_cdmx')
    brecha = kpi.loc[kpi['clave'] == CLAVE_BRECHA_NO_PAGADO, 'valor_num']
    return {
        **paquete(repo.tabla('enut_doble_jornada')),
        # Se lee del KPI: restar las columnas redondeadas daría 12.6 y no 12.7.
        'brecha_trabajo_no_pagado_h': None if brecha.empty else float(brecha.iloc[0]),
    }


@router.get('/enut/cuidado-por-grupo', tags=['ENUT 2024'],
            summary='¿Qué mujeres cuidan más? Por edad o por condición de actividad')
def enut_cuidado_por_grupo(
        tipo_grupo: Literal['Grupo de edad', 'Condición de actividad'] = Query(
            ..., description='Obligatorio: las dos desagregaciones no se mezclan.'),
        repo=Depends(repositorio)):
    df = repo.tabla('enut_cuidado_por_grupo')
    return paquete(df[df['tipo_grupo'] == tipo_grupo])


# =============================================================================
# ENASIC 2022 (nacional)
# =============================================================================

@router.get('/enasic', tags=['ENASIC 2022'],
            summary='Hallazgo C: las cuidadoras y los servicios de cuidado (nacional)')
def enasic(tema: TemaEnasic | None = None, repo=Depends(repositorio)):
    df = repo.tabla('enasic_cuidadoras')
    if tema:
        df = df[df['tema'] == tema]
    temas = []
    for nombre in TEMAS_ENASIC:
        sub = df[df['tema'] == nombre]
        if sub.empty:
            continue
        temas.append({
            'tema': nombre,
            # La base cambia entre temas: sin ella los porcentajes no se comparan.
            'base': sub['base'].iloc[0],
            'respuesta_multiple': bool(sub['respuesta_multiple'].iloc[0]),
            'variable_enasic': sub['variable_enasic'].iloc[0],
            'filas': a_registros(sub[['categoria', 'pct']]),
        })
    return {
        'fuente': sorted(df['fuente'].unique().tolist()),
        'nivel_geografico': sorted(df['nivel_geografico'].unique().tolist()),
        'aviso': analisis.AVISO_ENASIC,
        'temas': temas,
    }


# =============================================================================
# Alcaldías y territorio
# =============================================================================

@router.get('/alcaldias', tags=['alcaldías'],
            summary='Las 16 alcaldías: demanda, oferta y zonas sin respaldo')
def alcaldias(repo=Depends(repositorio)):
    return {
        **paquete(repo.tabla('resumen_alcaldia')),
        'indicadores': analisis.INDICADORES_ALCALDIA,
        'ciudad': analisis.contexto_ciudad(repo),
    }


@router.get('/alcaldias/{cve_mun}', tags=['alcaldías'],
            summary='Ficha de una alcaldía con sus hallazgos')
def alcaldia(cve_mun: str = CVE_MUN, repo=Depends(repositorio)):
    ficha = analisis.ficha_alcaldia(repo, cve_mun)
    if ficha is None:
        raise HTTPException(404, f'No hay una alcaldía con clave {cve_mun}.')
    return ficha


@router.get('/agebs', tags=['territorio'],
            summary='Capa del mapa: carga y acceso por AGEB (ubicación aproximada)')
def agebs(cve_mun: str | None = Query(None, pattern=r'^\d{3}$'),
          solo_sin_respaldo: bool = False, repo=Depends(repositorio)):
    df = repo.tabla('carga_ageb')
    if cve_mun:
        df = df[df['cve_mun'] == cve_mun]
    if solo_sin_respaldo:
        df = df[df['sin_respaldo'].fillna(False).astype(bool)]
    return {
        **paquete(df, sin_columnas=('nivel_geografico', 'fuente')),
        'aviso': analisis.AVISO_EXPLORATORIO,
    }


@router.get('/establecimientos', tags=['territorio'],
            summary='Capa de puntos: establecimientos de cuidado del DENUE')
def establecimientos(cve_mun: str | None = Query(None, pattern=r'^\d{3}$'),
                     solo_respaldo: bool = False, repo=Depends(repositorio)):
    df = repo.tabla('establecimientos_cuidado')
    if cve_mun:
        df = df[df['cve_mun'] == cve_mun]
    if solo_respaldo:
        df = df[df['es_respaldo'].fillna(False).astype(bool)]
    return {
        **paquete(df, sin_columnas=('nivel_geografico', 'fuente')),
        'aviso': analisis.AVISO_PRESION,
    }


@router.get('/territorio', tags=['territorio'],
            summary='Embudo de las zonas sin respaldo y distribución de la carga por AGEB')
def territorio(cve_mun: str | None = Query(None, pattern=r'^\d{3}$'),
               repo=Depends(repositorio)):
    if cve_mun and repo.tabla('resumen_alcaldia').query('cve_mun == @cve_mun').empty:
        raise HTTPException(404, f'No hay una alcaldía con clave {cve_mun}.')
    return {
        'fuente': [analisis.FTE_CRUCE],
        'nivel_geografico': ['AGEB'],
        'aviso': analisis.AVISO_EXPLORATORIO,
        **analisis.resumen_agebs(repo, cve_mun),
        **analisis.histograma_carga(repo, cve_mun),
    }
