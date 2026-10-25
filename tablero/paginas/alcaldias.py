"""Alcaldías. La comparación entre las 16 (mosaico y ranking por indicador), la ficha de
una alcaldía con sus hallazgos y el cruce entre la carga de cuidado y la presión sobre
las guarderías."""

import pandas as pd
import streamlit as st

import componentes as c
import datos as d
import graficas as g
from estilo import SECUENCIAL, SIN_DATO, color_secuencial, texto_sobre

# Posición aproximada de cada alcaldía en la ciudad (norte arriba): columna, fila, abreviatura.
CUADRICULA = {
    '002': (1, 0, 'AZC'), '005': (2, 0, 'GAM'), '016': (1, 1, 'MH'), '015': (2, 1, 'CUH'),
    '017': (3, 1, 'VC'), '004': (0, 2, 'CUJ'), '010': (1, 2, 'AO'), '014': (2, 2, 'BJ'),
    '006': (3, 2, 'IZC'), '008': (1, 3, 'MC'), '003': (2, 3, 'COY'), '007': (3, 3, 'IZP'),
    '012': (1, 4, 'TLP'), '013': (2, 4, 'XOC'), '011': (3, 4, 'TLH'), '009': (3, 5, 'MA'),
}

c.encabezado(
    'Escala de alcaldía', 'Alcaldías: dónde pesa más el cuidado',
    'Cuántas personas necesitan cuidado directo por cada mujer en edad de cuidar, cuánta oferta formal de '
    'cuidado hay cerca y dónde hay zonas de alta carga sin ningún respaldo.',
    'INEGI, Censo de Población y Vivienda 2020 · INEGI, DENUE 05/2026', 'Alcaldía')
c.hallazgos(d.hallazgos('alcaldias'))

alc = d.tabla('resumen_alcaldia')
alfabetico = d.alcaldias_alfabetico()
nombres = dict(zip(alc['cve_mun'], alc['alcaldia']))
ciudad = d.contexto_ciudad()
indicadores = {i['columna']: i for i in d.INDICADORES_ALCALDIA}


def elegir(cve):
    if cve in nombres:
        st.session_state.ficha = cve
        st.session_state.w_ficha = cve


def al_cambiar_selector():
    st.session_state.ficha = st.session_state.w_ficha


def al_hacer_clic(clave):
    """Un clic en el mosaico, el ranking o la dispersión elige la alcaldía de la ficha."""
    estado = st.session_state.get(clave)
    seleccion = getattr(estado, 'selection', None) or (estado or {}).get('selection', {})
    puntos = seleccion.get('elegida') if hasattr(seleccion, 'get') else None
    if puntos:
        elegir(puntos[0].get('cve_mun'))


st.space('medium')
c.subtitulo('Compara las 16 alcaldías',
            'Elige un indicador y una alcaldía. También puedes hacer clic en una casilla del mosaico, en una barra '
            'o en un punto.')
st.session_state.setdefault('w_ficha', st.session_state.ficha)
with st.container(border=True, horizontal=True, gap='medium'):
    columna = st.selectbox('Indicador', list(indicadores), format_func=lambda k: indicadores[k]['etiqueta'],
                           key='indicador', width=380)
    st.selectbox('Alcaldía de la ficha', alfabetico['cve_mun'].tolist(), format_func=nombres.get,
                 key='w_ficha', on_change=al_cambiar_selector, width=300)
indicador = indicadores[columna]
ficha_cve = st.session_state.ficha

# --- Mosaico y ranking ---------------------------------------------------------------------
valores = alc[columna]
minimo, maximo = valores.min(), valores.max()
orden_desc = valores.rank(ascending=False, method='min')
mosaico = []
for f in alc.itertuples():
    col, fila, abrev = CUADRICULA[f.cve_mun]
    v = getattr(f, columna)
    relleno = color_secuencial(None if pd.isna(v) else v, minimo, maximo) or SIN_DATO
    lugar = orden_desc[f.Index]
    mosaico.append({'cve_mun': f.cve_mun, 'col': col, 'fila': fila, 'abrev': abrev, 'nombre': f.alcaldia,
                    'texto': c.segun_indicador(None if pd.isna(v) else v, indicador), 'relleno': relleno,
                    'color_texto': texto_sobre(relleno), 'elegida': f.cve_mun == ficha_cve,
                    'lugar': '—' if pd.isna(lugar) else f'{int(lugar)} de {int(valores.notna().sum())}'})

if columna == 'carga_directa_x100_mujeres' and ciudad['carga_cdmx'] is not None:
    referencia = (ciudad['carga_cdmx'], f'Ciudad: {c.f_num(ciudad["carga_cdmx"])}')
elif ciudad['medianas'].get(columna) is not None:
    referencia = (ciudad['medianas'][columna], f'Mediana: {c.segun_indicador(ciudad["medianas"][columna], indicador)}')
else:
    referencia = None
ordenadas = alc.assign(_nulo=valores.isna()).sort_values(['_nulo', columna], ascending=[True, False])
ranking = pd.DataFrame({'cve_mun': ordenadas['cve_mun'], 'categoria': ordenadas['alcaldia'],
                        'valor': ordenadas[columna],
                        'texto': [c.segun_indicador(None if pd.isna(v) else v, indicador) for v in ordenadas[columna]],
                        'unidad': indicador['unidad']})
sufijo = ' %' if indicador['unidad'].startswith('%') else ''

izq, der = st.columns([1, 1.45], gap='medium')
with izq, c.tarjeta(indicador['etiqueta'],
                    f'{indicador["unidad"].capitalize()}. Cada casilla es una alcaldía, en su posición aproximada '
                    '(norte arriba).'):
    st.altair_chart(g.mosaico(pd.DataFrame(mosaico)), key='clic_mosaico', on_select=lambda: al_hacer_clic('clic_mosaico'),
                    selection_mode='elegida')
    leyenda = [(f'{c.segun_indicador(minimo, indicador)} a {c.segun_indicador(maximo, indicador)}', SECUENCIAL, 'gradiente')]
    if valores.isna().any():
        leyenda.append(('No aplica', SIN_DATO, 'cuadro'))
    c.leyenda(leyenda)
    c.nota_fuente(indicador['fuente'], 'Alcaldía', indicador.get('exploratorio', False))
with der, c.tarjeta('Las 16 alcaldías en orden', indicador['descripcion']):
    st.altair_chart(g.ranking(ranking, seleccion=ficha_cve, referencia=referencia, sufijo=sufijo), width='stretch',
                    key='clic_ranking', on_select=lambda: al_hacer_clic('clic_ranking'), selection_mode='elegida')
    if indicador.get('advertencia'):
        st.caption(indicador['advertencia'])
    if indicador.get('exploratorio'):
        st.caption('Exploratorio: las ubicaciones de las AGEB son aproximadas.')
    c.nota_fuente(indicador['fuente'], 'Alcaldía', indicador.get('exploratorio', False))

# --- Ficha de la alcaldía --------------------------------------------------------------------
ficha = d.ficha_alcaldia(ficha_cve)
st.space('medium')
with st.container(border=True):
    a, ctx, pos = ficha['alcaldia'], ficha['ciudad'], ficha['posiciones']
    cabeza, boton = st.columns([3, 1], vertical_alignment='bottom')
    cabeza.caption('Ficha de alcaldía')
    cabeza.subheader(a['alcaldia'], anchor=False)
    if boton.button('Ver sus AGEB en el mapa', icon=':material/map:', width='stretch'):
        st.session_state.mapa = ficha_cve
        st.session_state.pop('w_mapa', None)
        st.switch_page('paginas/territorio.py')
    lugar_guarderias = pos['ninos_0a5_por_guarderia']['lugar']
    st.html(f'''<div class="obs-ficha-cifras">
      <div><span>Mujeres de 15 a 59 años</span><strong>{c.esc(c.f_ent(a["mujeres_15a59"]))}</strong>
        <small>{c.esc(c.f_pct(a["mujeres_15a59"] / ctx["mujeres_15a59"] * 100))} de la ciudad</small></div>
      <div><span>Carga de cuidado directo</span><strong>{c.esc(c.f_num(a["carga_directa_x100_mujeres"]))}</strong>
        <small>Lugar {a["rango_carga"]} de 16; ciudad: {c.esc(c.f_num(ctx["carga_cdmx"]))}</small></div>
      <div><span>Mujeres en zonas sin respaldo</span><strong>{c.esc(c.f_ent(a["mujeres_sin_respaldo"]))}</strong>
        <small>{a["agebs_sin_respaldo"]} de {a["agebs_alta_carga"]} AGEB de alta carga; exploratorio</small></div>
      <div><span>Niñas y niños por guardería</span><strong>{c.esc(c.f_ent(a["ninos_0a5_por_guarderia"]))}</strong>
        <small>{f"Lugar {lugar_guarderias} de 16 en presión" if lugar_guarderias else "No aplica"}</small></div>
    </div>''')
    st.space('small')
    c.hallazgos(ficha['hallazgos'])
    est = ficha['establecimientos']
    st.markdown(f'**Establecimientos de cuidado registrados.** {c.f_ent(est["total"])} establecimientos en el DENUE, '
                f'de los cuales {c.f_ent(est["respaldo"])} cuentan como respaldo (sustituyen horas de cuidado en el hogar).')
    st.dataframe(pd.DataFrame([{'Tipo de establecimiento': t['tipo'], 'Públicos': t['publico'], 'Privados': t['privado'],
                                'Total': t['total'], 'Cuenta como respaldo': 'Sí' if t['es_respaldo'] else 'No'}
                               for t in est['por_tipo']]), hide_index=True, width='stretch')
    c.nota_fuente([est['fuente'], 'INEGI, Censo 2020'], 'Alcaldía')

# --- Dispersión ------------------------------------------------------------------------------------
st.space('medium')
c.subtitulo('Mucha carga y poca oferta',
            'Cada punto es una alcaldía. A la derecha, más personas que necesitan cuidado por cada mujer; arriba, más '
            'niñas y niños por cada guardería registrada. Las líneas marcan la mediana de las alcaldías.')
puntos = pd.DataFrame({
    'cve_mun': alc['cve_mun'], 'abrev': [CUADRICULA[k][2] for k in alc['cve_mun']], 'nombre': alc['alcaldia'],
    'x': alc['carga_directa_x100_mujeres'], 'y': alc['ninos_0a5_por_guarderia'],
    'texto_x': [c.f_num(v) for v in alc['carga_directa_x100_mujeres']],
    'texto_y': [c.f_ent(v) for v in alc['ninos_0a5_por_guarderia']],
    'elegida': alc['cve_mun'] == ficha_cve,
}).dropna(subset=['x', 'y'])
with c.tarjeta('Carga de cuidado y presión sobre las guarderías',
               'La presión sobre la oferta no es cobertura: el DENUE registra establecimientos, no lugares disponibles.'):
    st.altair_chart(g.dispersion(puntos, medianas={'x': ciudad['medianas']['carga_directa_x100_mujeres'],
                                                   'y': ciudad['medianas']['ninos_0a5_por_guarderia']},
                                 nombre_x='Carga de cuidado (personas por cada 100 mujeres de 15 a 59)',
                                 nombre_y='Niñas y niños de 0 a 5 por guardería', rotulo='Más carga y más presión'),
                    width='stretch', key='clic_dispersion', on_select=lambda: al_hacer_clic('clic_dispersion'),
                    selection_mode='elegida')
    c.nota_fuente('INEGI, Censo 2020 + DENUE 05/2026', 'Alcaldía')

# --- Tabla completa ------------------------------------------------------------------------------
st.space('medium')
c.subtitulo('Todas las cifras por alcaldía', 'Haz clic en un encabezado para ordenar.')
completa = alfabetico[['alcaldia','mujeres_15a59', 'carga_directa_x100_mujeres', 'pct_hog_jefa', 'pct_mujeres_inactivas',
                'agebs_alta_carga', 'agebs_sin_respaldo', 'mujeres_sin_respaldo', 'guarderias',
                'ninos_0a5_por_guarderia', 'cuidado_mayores', 'mayores_60_por_establecimiento',
                'pct_guarderias_publicas']]
st.dataframe(completa, hide_index=True, width='stretch', column_config={
    'alcaldia': st.column_config.TextColumn('Alcaldía', pinned=True),
    'mujeres_15a59': st.column_config.NumberColumn('Mujeres 15–59', format='localized'),
    'carga_directa_x100_mujeres': st.column_config.NumberColumn('Carga x100 mujeres', format='%.1f'),
    'pct_hog_jefa': st.column_config.NumberColumn('% hogares con jefa', format='%.1f %%'),
    'pct_mujeres_inactivas': st.column_config.NumberColumn('% mujeres fuera del mercado laboral', format='%.1f %%'),
    'agebs_alta_carga': st.column_config.NumberColumn('AGEB de alta carga'),
    'agebs_sin_respaldo': st.column_config.NumberColumn('AGEB sin respaldo'),
    'mujeres_sin_respaldo': st.column_config.NumberColumn('Mujeres sin respaldo', format='localized'),
    'guarderias': st.column_config.NumberColumn('Guarderías'),
    'ninos_0a5_por_guarderia': st.column_config.NumberColumn('Niñas/os por guardería', format='%.0f'),
    'cuidado_mayores': st.column_config.NumberColumn('Estab. personas mayores'),
    'mayores_60_por_establecimiento': st.column_config.NumberColumn('60+ por estab.', format='%.0f'),
    'pct_guarderias_publicas': st.column_config.NumberColumn('% guarderías públicas', format='%.1f %%'),
})
st.download_button('Descargar en CSV', d.csv_indicadores('resumen_alcaldia'), 'indicadores_resumen_alcaldia.csv',
                   'text/csv', icon=':material/download:', on_click='ignore')
c.nota_fuente('INEGI, Censo 2020 + DENUE 05/2026', 'Alcaldía')
