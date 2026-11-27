"""Piezas que se repiten en todas las páginas: formato de cifras, insignias de nivel,
notas de fuente, tarjetas de indicador y de hallazgo, medidores y el embudo.

Toda cifra sale con su fuente y su nivel geográfico (docs/diccionario_datos.md). Los
textos que vienen de los datos se escapan antes de entrar a HTML.
"""

import html
import math
from contextlib import contextmanager

import streamlit as st

from datos import analisis
from estilo import ACENTO, REFERENCIA

NBSP = ' '


# --- Formato de México: 1,234.5 · 62.2 % · 12.7 h ------------------------------------

def vacio(v):
    return v is None or (isinstance(v, float) and math.isnan(v))


def f_num(v, decimales=1):
    return '—' if vacio(v) else analisis.num(v, decimales)


def f_ent(v):
    return '—' if vacio(v) else analisis.ent(v)


def f_pct(v, decimales=1):
    return '—' if vacio(v) else analisis.pct(v, decimales)


def f_horas(v):
    return '—' if vacio(v) else analisis.horas(v)


def segun_indicador(v, indicador):
    if vacio(v):
        return 'No aplica'
    texto = analisis.num(v, indicador['decimales'])
    return f'{texto}{NBSP}%' if indicador['unidad'].startswith('%') else texto


def esc(texto):
    return html.escape('' if texto is None else str(texto))


# Etiquetas cortas para los ejes; la tabla de cada gráfica conserva el nombre completo.
CORTAS = {
    'Cuidado a niñas/os de 0 a 5': 'Niñas y niños de 0 a 5',
    'Cuidado a niñas y niños de 0 a 5': 'Niñas y niños de 0 a 5',
    'Cuidado a niñas y niños de 6 a 14': 'Niñas y niños de 6 a 14',
    'Cuidado a personas de 60+': 'Personas de 60 años o más',
}


def corta(actividad):
    return CORTAS.get(actividad, actividad)


# --- Insignias y notas de fuente -----------------------------------------------------

def insignias(niveles, exploratorio=False):
    niveles = [niveles] if isinstance(niveles, str) else list(niveles)
    partes = [f'<span class="obs-insignia{" obs-insignia--nacional" if n == "Nacional" else ""}">{esc(n)}</span>'
              for n in niveles]
    if exploratorio:
        partes.append('<span class="obs-insignia obs-insignia--exploratorio">Exploratorio</span>')
    return ''.join(partes)


def nota_fuente(fuente, nivel, exploratorio=False):
    fuentes = [fuente] if isinstance(fuente, str) else list(fuente)
    st.html(f'<div class="obs-nota"><span>Fuente: {esc(" · ".join(fuentes))}</span>'
            f'<span>Nivel: {insignias(nivel, exploratorio)}</span></div>')


def encabezado(escala, titulo, entrada, fuentes, niveles, exploratorio=False):
    st.html(f'<p class="obs-escala">{esc(escala)} {insignias(niveles, exploratorio)}</p>')
    st.title(titulo, anchor=False)
    st.markdown(entrada)
    st.caption(f'Fuentes: {fuentes}')


def subtitulo(titulo, texto=None):
    st.subheader(titulo, anchor=False)
    if texto:
        st.markdown(texto)


@contextmanager
def tarjeta(titulo, subtitulo_=None):
    with st.container(border=True):
        st.markdown(f'**{titulo}**')
        if subtitulo_:
            st.caption(subtitulo_)
        yield


def ver_tabla(df, column_config=None, titulo='Ver los datos en tabla'):
    with st.expander(titulo):
        st.dataframe(df, hide_index=True, column_config=column_config, width='stretch')


# --- Tarjetas --------------------------------------------------------------------------

def _tile(etiqueta, valor, contexto=None, nivel=None, fuente=None, exploratorio=False):
    pie = ''
    if nivel or fuente:
        pie = (f'<div class="obs-tile-pie">{insignias(nivel, exploratorio) if nivel else ""}'
               f'<span>{esc(fuente)}</span></div>')
    return (f'<div class="obs-tarjeta"><p class="obs-tile-etiqueta">{esc(etiqueta)}</p>'
            f'<p class="obs-tile-valor">{esc(valor)}</p>'
            f'{f"<p class=obs-tile-contexto>{esc(contexto)}</p>" if contexto else ""}{pie}</div>')


def indicadores(items):
    """Fila de tarjetas de indicador. items: dicts con etiqueta, valor, contexto, nivel, fuente."""
    st.html(f'<div class="obs-rejilla" style="grid-template-columns:repeat(auto-fit,minmax(220px,1fr))">'
            f'{"".join(_tile(**i) for i in items)}</div>')


ESTADOS = {'ok': ('obs-estado--ok', '●', 'En meta'), 'aviso': ('obs-estado--aviso', '▲', 'Vigilar'),
           'critico': ('obs-estado--critico', '■', 'Fuera de meta')}


def kpis_con_meta(items):
    """Tarjetas de KPI con su meta o referencia y un estado (forma + texto, no solo color).

    items: dicts con etiqueta, valor, meta, estado ('ok' | 'aviso' | 'critico'), nivel, fuente
    y, opcional, exploratorio y simulado.
    """
    tarjetas = []
    for i in items:
        clase, forma, texto = ESTADOS[i['estado']]
        niveles = insignias(i['nivel'], i.get('exploratorio', False))
        if i.get('simulado'):
            niveles += '<span class="obs-insignia obs-insignia--exploratorio">Simulado</span>'
        tarjetas.append(
            f'<div class="obs-tarjeta"><p class="obs-tile-etiqueta">{esc(i["etiqueta"])}</p>'
            f'<p class="obs-tile-valor">{esc(i["valor"])}</p>'
            f'<p class="obs-tile-contexto">{esc(i["meta"])}</p>'
            f'<p class="obs-estado {clase}"><span aria-hidden="true">{forma}</span> {esc(texto)}'
            f'{(" · " + esc(i["detalle_estado"])) if i.get("detalle_estado") else ""}</p>'
            f'<div class="obs-tile-pie">{niveles}<span>{esc(i["fuente"])}</span></div></div>')
    st.html(f'<div class="obs-rejilla" style="grid-template-columns:repeat(auto-fit,minmax(200px,1fr))">'
            f'{"".join(tarjetas)}</div>')


def f_cambio(v, decimales=0):
    """Cambio porcentual con signo tipográfico: +37 % o −37 %."""
    if vacio(v):
        return '—'
    return f'{"−" if v < 0 else "+"}{analisis.num(abs(v), decimales)}{NBSP}%'


def hallazgos(lista):
    if not lista:
        return
    tarjetas = []
    for h in lista:
        clase = 'obs-tarjeta obs-hallazgo' + (' obs-tarjeta--destacada' if h['destacado'] else '')
        advertencia = (f'<p class="obs-advertencia">{esc(h["advertencia"])}</p>'
                       if h.get('advertencia') else '')
        tarjetas.append(
            f'<article class="{clase}"><h4>{esc(h["titulo"])}</h4><p>{esc(h["texto"])}</p>{advertencia}'
            f'<div class="obs-tile-pie">{insignias(h["nivel_geografico"], h["exploratorio"])}'
            f'<span>{esc(h["fuente"])}</span></div></article>')
    st.html(f'<div class="obs-rejilla">{"".join(tarjetas)}</div>')


def leyenda(items):
    """items: (texto, color, forma) con forma en cuadro | punto | anillo | hueco | gradiente."""
    partes = []
    for texto, color, forma in items:
        if forma == 'gradiente':
            muestra = f'<i class="obs-gradiente" style="background:linear-gradient(90deg,{", ".join(color)})"></i>'
        else:
            clase = {'cuadro': '', 'punto': ' obs-muestra--punto', 'anillo': ' obs-muestra--anillo',
                     'hueco': ' obs-muestra--hueco'}[forma]
            fondo = f' style="background:{color}"' if forma in ('cuadro', 'punto') else ''
            muestra = f'<i class="obs-muestra{clase}"{fondo}></i>'
        partes.append(f'<span>{muestra}{esc(texto)}</span>')
    st.html(f'<div class="obs-leyenda">{"".join(partes)}</div>')


def leyenda_mujeres_hombres(principal='Mujeres', referencia='Hombres (referencia)'):
    leyenda([(principal, ACENTO, 'cuadro'), (referencia, REFERENCIA, 'cuadro')])


def medidores(items):
    """Barras de porcentaje (0 a 100) con su etiqueta: items (etiqueta, valor)."""
    filas = ''.join(
        f'<div class="obs-medidor"><div><span>{esc(etiqueta)}</span><strong>{esc(f_pct(valor))}</strong></div>'
        f'<span class="obs-pista"><i style="width:{0 if vacio(valor) else min(100, max(0, valor)):.1f}%"></i></span></div>'
        for etiqueta, valor in items)
    st.html(filas)


def embudo(etapas, colores):
    maximo = max(e['agebs'] for e in etapas) or 1
    filas = ''.join(
        f'<div><span class="obs-fila"><span>{esc(e["etapa"])}</span><strong>{esc(f_ent(e["agebs"]))} AGEB</strong></span>'
        f'<span class="obs-barra" style="width:{max(1.5, e["agebs"] / maximo * 100):.1f}%;background:{color}"></span>'
        f'<small>{esc(f_ent(e["mujeres_15a59"]))} mujeres de 15 a 59 viven ahí</small></div>'
        for e, color in zip(etapas, colores))
    st.html(f'<div class="obs-embudo">{filas}</div>')


def pie():
    st.html('<div class="obs-pie">Observatorio de la Economía del Cuidado · Proyecto PP7, UNRC. '
            'Datos: INEGI (ENUT 2024, ENASIC 2022, Censo 2020, DENUE 05/2026). '
            'Código y datos en <a href="https://github.com/dead-can-dance/observatorio-economia-cuidado-cdmx" '
            'target="_blank" rel="noopener">GitHub</a>.</div>')
