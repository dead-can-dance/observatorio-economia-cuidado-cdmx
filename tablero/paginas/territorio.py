"""Territorio (AGEB). Hallazgo B, exploratorio: AGEB de alta carga de cuidado sin
guardería, residencia ni centro de día a menos de 1 km."""

import pandas as pd
import streamlit as st

import componentes as c
import datos as d
import graficas as g
import mapa
from estilo import ACENTO, CRITICO, REFERENCIA, VIOLETA

c.encabezado(
    'Escala de AGEB', 'Territorio: mujeres que cuidan sin respaldo cerca',
    'Hallazgo B. Zonas en el cuartil más alto de carga de cuidado de la ciudad que no tienen ninguna guardería, '
    'residencia para personas mayores ni centro de día a menos de 1 km (unos 12 a 15 minutos a pie).',
    'INEGI, Censo 2020 (AGEB urbanas) + INEGI, DENUE 05/2026', 'AGEB', exploratorio=True)
st.warning('**Hallazgo exploratorio.** Mientras no se integre el Marco Geoestadístico del INEGI, el punto de cada '
           'AGEB es la mediana de los establecimientos del DENUE que caen dentro, no el centroide de su polígono: '
           'está sesgado hacia las zonas comerciales. Al recalcular con los polígonos oficiales las cifras pueden '
           'cambiar. Las AGEB urbanas no cubren la zona rural (en Milpa Alta queda fuera el 16 % de la población).',
           icon=':material/warning:')

alfabetico = d.alcaldias_alfabetico()
nombres = dict(zip(alfabetico['cve_mun'], alfabetico['alcaldia']))
CIUDAD = 'ciudad'


def al_cambiar():
    st.session_state.mapa = None if st.session_state.w_mapa == CIUDAD else st.session_state.w_mapa


CAPAS = {'carga': 'Carga por AGEB', 'sin_respaldo': 'Zonas sin respaldo',
         'respaldo': 'Establecimientos de respaldo', 'otros': 'Otros establecimientos'}
st.session_state.setdefault('w_mapa', st.session_state.mapa or CIUDAD)
with st.container(border=True, horizontal=True, gap='medium', vertical_alignment='bottom'):
    st.selectbox('Alcaldía', [CIUDAD] + alfabetico['cve_mun'].tolist(),
                 format_func=lambda k: 'Toda la ciudad' if k == CIUDAD else nombres[k],
                 key='w_mapa', on_change=al_cambiar, width=280)
    capas = st.pills('Capas del mapa', list(CAPAS), format_func=CAPAS.get, selection_mode='multi',
                     default=['carga', 'sin_respaldo'], key='capas')
cve = st.session_state.mapa
nombre = nombres.get(cve)
resumen = d.territorio(cve)

izq, der = st.columns([1.75, 1], gap='medium')
with izq, c.tarjeta(f'AGEB de {nombre}' if nombre else 'Las 2,320 AGEB analizadas de la ciudad',
                    'Cada punto es una AGEB, coloreada por personas que necesitan cuidado directo por cada 100 '
                    'mujeres de 15 a 59. Pasa el cursor sobre un punto para ver su detalle.'):
    leyenda = []
    if 'carga' in capas:
        leyenda.append(('Carga de cuidado (menos a más)', mapa.ESCALA, 'gradiente'))
    if 'sin_respaldo' in capas:
        leyenda.append(('⚠ Alta carga sin respaldo a 1 km', CRITICO, 'anillo'))
    if 'respaldo' in capas:
        leyenda.append(('Guardería, residencia o centro de día', '#3e3d3a', 'punto'))
    if 'otros' in capas:
        leyenda.append(('Otro establecimiento de cuidado', REFERENCIA, 'hueco'))
    c.leyenda(leyenda)
    st.pydeck_chart(mapa.construir(d.tabla('carga_ageb'), d.tabla('establecimientos_cuidado'),
                                   seleccion=cve, capas=capas or ()), height=560)
    c.nota_fuente(['INEGI, Censo 2020 + DENUE 05/2026', 'mapa base © CARTO y colaboradores de OpenStreetMap'], 'AGEB',
                  exploratorio=True)

with der:
    with c.tarjeta('De la carga a la falta de respaldo',
                   f'{nombre or "Toda la ciudad"}. Cada etapa es un subconjunto de la anterior.'):
        c.embudo(resumen['embudo'], [VIOLETA[300], VIOLETA[450], VIOLETA[600], CRITICO])
        c.nota_fuente('INEGI, Censo 2020 + DENUE 05/2026', 'AGEB', exploratorio=True)
    with c.tarjeta('Cómo se reparte la carga entre las AGEB',
                   f'{nombre or "Toda la ciudad"}. En el color de acento, las de alta carga (cuartil superior de la ciudad).'):
        c.leyenda([('Alta carga', ACENTO, 'cuadro'), ('Resto de las AGEB', REFERENCIA, 'cuadro')])
        filas = []
        for i in resumen['intervalos']:
            rango = f'{i["desde"]} a {i["hasta"]}'
            filas += [{'desde': i['desde'], 'hasta': i['hasta'], 'grupo': 'Alta carga', 'n': i['alta_carga'],
                       'rango': rango, 'orden': 0},
                      {'desde': i['desde'], 'hasta': i['hasta'], 'grupo': 'Resto de las AGEB', 'n': i['resto'],
                       'rango': rango, 'orden': 1}]
        st.altair_chart(g.histograma(pd.DataFrame(filas), umbral=resumen['umbral_alta_carga']), width='stretch')
        st.caption(f'Mediana: {c.f_num(resumen["mediana"])}; percentiles 10 y 90: {c.f_num(resumen["percentil_10"])} '
                   f'y {c.f_num(resumen["percentil_90"])}.')
        c.nota_fuente('INEGI, Censo 2020', 'AGEB')
        c.ver_tabla(pd.DataFrame([{'Carga (personas por cada 100 mujeres)': f'{i["desde"]} a {i["hasta"]}',
                                   'AGEB de alta carga': i['alta_carga'], 'Resto de las AGEB': i['resto']}
                                  for i in resumen['intervalos'] if i['alta_carga'] + i['resto'] > 0]))

st.space('medium')
agebs = d.tabla('carga_ageb')
sin = agebs[agebs['sin_respaldo'].fillna(False).astype(bool)]
if cve:
    sin = sin[sin['cve_mun'] == cve]
sin = sin.sort_values('mujeres_15a59', ascending=False)
c.subtitulo(f'Las AGEB sin respaldo{" en " + nombre if nombre else ""}',
            f'{c.f_ent(len(sin))} AGEB de alta carga sin ningún servicio de respaldo a menos de 1 km, ordenadas por '
            'número de mujeres de 15 a 59 que viven en ellas.')
if len(sin):
    st.dataframe(sin[['cvegeo_ageb', 'alcaldia', 'mujeres_15a59', 'carga_directa_x100_mujeres', 'pob_0a5',
                      'pct_hog_jefa', 'guarderias_1km']], hide_index=True, width='stretch', column_config={
        'cvegeo_ageb': st.column_config.TextColumn('AGEB (clave)'),
        'alcaldia': st.column_config.TextColumn('Alcaldía'),
        'mujeres_15a59': st.column_config.NumberColumn('Mujeres 15–59', format='localized'),
        'carga_directa_x100_mujeres': st.column_config.NumberColumn('Carga x100 mujeres', format='%.1f'),
        'pob_0a5': st.column_config.NumberColumn('Niñas y niños 0–5', format='localized'),
        'pct_hog_jefa': st.column_config.NumberColumn('% hogares con jefa', format='%.1f %%'),
        'guarderias_1km': st.column_config.NumberColumn('Guarderías a 1 km'),
    })
else:
    st.markdown(f'No hay AGEB de alta carga sin respaldo en {nombre}.')
c.nota_fuente('INEGI, Censo 2020 + DENUE 05/2026', 'AGEB', exploratorio=True)
