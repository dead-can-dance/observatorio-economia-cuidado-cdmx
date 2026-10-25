"""Cómo leer (y cómo no leer) estos datos: las advertencias del diccionario de datos, las
fuentes, el glosario, las descargas y el estado de la fuente de datos."""

import pandas as pd
import streamlit as st

import componentes as c
import datos as d

DESCRIPCION_TABLAS = {
    'kpi_cdmx': 'Cifras de cabecera',
    'resumen_alcaldia': 'Las 16 alcaldías',
    'carga_ageb': 'Carga y acceso por AGEB (capa del mapa)',
    'establecimientos_cuidado': 'Establecimientos de cuidado del DENUE',
    'enut_carga_actividad': 'ENUT: cuidado por actividad, CDMX y nacional',
    'enut_brecha_mujeres_cdmx': 'ENUT: brecha de las mujeres de la CDMX',
    'enut_doble_jornada': 'ENUT: doble jornada',
    'enut_cuidado_por_grupo': 'ENUT: qué mujeres cuidan más',
    'enasic_cuidadoras': 'ENASIC: cuidadoras y servicios (nacional)',
}

m = d.metodologia
st.html('<p class="obs-escala">Método</p>')
st.title('Cómo leer (y cómo no leer) estos datos', anchor=False)
st.markdown('Cinco advertencias que respeta cada gráfica y cada texto de este observatorio. Vienen del diccionario '
            'de datos del proyecto (`docs/diccionario_datos.md`).')

tarjetas = ''.join(
    f'''<article class="obs-tarjeta"><h4 style="margin:0;font-size:1.02rem">{i}. {c.esc(a["titulo"])}</h4>
      <p style="margin:0;font-size:.92rem">{c.esc(a["texto"])}</p>
      <div class="obs-no-si"><div class="obs-no"><b>No se puede decir</b>{c.esc(a["no"])}</div>
      <div class="obs-si"><b>Sí se puede decir</b>{c.esc(a["si"])}</div></div></article>'''
    for i, a in enumerate(m.ADVERTENCIAS, start=1))
st.html(f'<div class="obs-rejilla" style="grid-template-columns:repeat(auto-fit,minmax(330px,1fr))">{tarjetas}</div>')

st.space('medium')
c.subtitulo('Fuentes', 'Todas del INEGI. Ninguna cifra se publica sin fuente, año y nivel geográfico.')
fuentes = ''.join(
    f'''<article class="obs-tarjeta"><p class="obs-tile-etiqueta">{c.esc(f["clave"])}</p>
      <h4 style="margin:0;font-size:1.02rem">{c.esc(f["nombre"])}</h4><p style="margin:0;font-size:.92rem">{c.esc(f["que_mide"])}</p>
      <div class="obs-tile-pie" style="margin-top:0">Niveles: {c.insignias(f["niveles"])}</div>
      <ul style="margin:4px 0 0;padding-left:1.1em;font-size:.88rem">{"".join(f"<li>{c.esc(n)}</li>" for n in f["notas"])}</ul>
    </article>'''
    for f in m.FUENTES)
st.html(f'<div class="obs-rejilla" style="grid-template-columns:repeat(auto-fit,minmax(380px,1fr))">{fuentes}</div>')

st.space('medium')
c.subtitulo('Glosario')
for g in m.GLOSARIO:
    st.markdown(f'**{g["termino"]}.** {g["definicion"]}')

st.space('medium')
c.subtitulo('Descarga los datos', 'Las nueve tablas del esquema `indicadores`, que son las únicas que lee este '
            'observatorio. Los CSV abren bien en Excel (con acentos).')
repo = d.repositorio()
with st.container(horizontal=True, gap='small'):
    for nombre in d.TABLAS:
        st.download_button(f'{nombre} ({c.f_ent(len(repo.tabla(nombre)))} filas)', d.csv_indicadores(nombre),
                           f'indicadores_{nombre}.csv', 'text/csv', icon=':material/download:',
                           help=DESCRIPCION_TABLAS.get(nombre), on_click='ignore', key=f'csv_{nombre}')

st.space('medium')
c.subtitulo('Estado de los datos')
cuadran = sum(x['ok'] for x in repo.controles)
if repo.controles_ok:
    st.success(f'Todas las cifras de control cuadran ({cuadran} de {len(repo.controles)}).', icon=':material/check_circle:')
else:
    st.error(f'Hay cifras de control que no cuadran ({cuadran} de {len(repo.controles)}).', icon=':material/error:')
fuente = 'PostgreSQL' if repo.fuente == 'postgres' else 'Respaldo local'
st.markdown(f'**Fuente activa:** {fuente}: {repo.detalle}.')
if repo.aviso:
    st.caption(repo.aviso)
st.caption(f'Datos cargados el {repo.cargado_en:%d/%m/%Y a las %H:%M}.')


def mostrar(v):
    return '—' if v is None else f'{v:,}' if isinstance(v, int) else f'{v:,.1f}' if isinstance(v, float) else str(v)


st.dataframe(pd.DataFrame([{'Cifra de control': x['etiqueta'], 'Esperado': mostrar(x['esperado']),
                            'Obtenido': mostrar(x['obtenido']), 'Estado': '✓ Cuadra' if x['ok'] else '✗ No cuadra'}
                           for x in repo.controles]), hide_index=True, width='stretch')
