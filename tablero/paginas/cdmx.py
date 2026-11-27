"""Ciudad de México. La doble jornada (hallazgo A), la ciudad frente al país, la brecha
por actividad y qué mujeres cuidan más (ENUT 2024, nivel CDMX)."""

import pandas as pd
import streamlit as st

import componentes as c
import datos as d
import graficas as g
from estilo import ACENTO, CUIDADO, DOMESTICO, MERCADO, REFERENCIA

c.encabezado(
    'Escala de ciudad', 'Ciudad de México: la doble jornada',
    'En la capital, la mayoría de las mujeres cuida y, cuando además tiene un empleo, su semana se alarga: '
    'al trabajo pagado se suman el trabajo doméstico y el cuidado de su propio hogar.',
    'INEGI, ENUT 2024 (representativa para la CDMX) · INEGI, Censo de Población y Vivienda 2020', 'CDMX')

c.indicadores([
    dict(etiqueta='Mujeres de 12 años y más que cuidan a integrantes de su hogar', valor=c.f_pct(d.kpi(d.KPI_PCT_CUIDAN)),
         nivel='CDMX', fuente='INEGI, ENUT 2024'),
    dict(etiqueta='Horas a la semana que dedican las que cuidan', valor=c.f_horas(d.kpi(d.KPI_HORAS_CUIDAN)),
         contexto=f'Hombres que cuidan (referencia): {c.f_horas(d.kpi(d.KPI_HORAS_HOMBRES))}',
         nivel='CDMX', fuente='INEGI, ENUT 2024'),
    dict(etiqueta='Jornada total de las mujeres ocupadas', valor=c.f_horas(d.kpi(d.KPI_JORNADA_MUJERES)),
         contexto=f'Hombres ocupados (referencia): {c.f_horas(d.kpi(d.KPI_JORNADA_HOMBRES))}',
         nivel='CDMX', fuente='INEGI, ENUT 2024'),
    dict(etiqueta='Personas que necesitan cuidado directo por cada 100 mujeres de 15 a 59',
         valor=c.f_num(d.kpi(d.KPI_CARGA_CDMX)),
         contexto='Niñas y niños de 0 a 5 y personas con discapacidad para su autocuidado.',
         nivel='CDMX', fuente='INEGI, Censo 2020'),
])

# --- Hallazgo A: la doble jornada ------------------------------------------------------
st.space('medium')
c.subtitulo('Hallazgo A: la doble jornada',
            'Horas a la semana de las personas ocupadas, por tipo de trabajo. Es el promedio sobre todo el grupo, '
            'incluso quien no realiza la actividad: por eso los componentes suman la jornada total.')
jornada = d.tabla('enut_doble_jornada').set_index('grupo')
muj, hom = jornada.loc['Mujeres ocupadas'], jornada.iloc[1]
brecha = d.kpi(d.KPI_BRECHA)
componentes = [('Trabajo para el mercado (pagado)', 'horas_trabajo_mercado', MERCADO),
               ('Trabajo doméstico no remunerado', 'horas_trabajo_domestico', DOMESTICO),
               ('Cuidado no remunerado', 'horas_cuidado', CUIDADO)]
cortas = {'Mujeres ocupadas': 'Mujeres', 'Hombres ocupados (ref.)': 'Hombres (ref.)'}

izq, der = st.columns([1, 2], gap='medium')
with izq, st.container(border=True):
    st.html(f'''<p class="obs-tile-etiqueta">Brecha de trabajo no pagado</p>
      <p class="obs-tile-valor">+{c.esc(c.f_num(brecha))} h <span style="font-size:1rem;font-weight:400;opacity:.75">a la
      semana</span></p>
      <p style="margin:6px 0 0">Es lo que trabajan sin pago, de más, las mujeres ocupadas frente a los hombres ocupados
      (referencia): trabajo doméstico y cuidado de su propio hogar.</p>
      <p style="margin:10px 0 0;opacity:.8">Con el trabajo pagado, su semana suma <strong>{c.esc(c.f_horas(muj.horas_jornada_total))}</strong>.
      La diferencia en la jornada total es menor y más frágil que la del trabajo no pagado, que es la cifra sólida.</p>''')
    c.nota_fuente('INEGI, ENUT 2024', 'CDMX')
with der, c.tarjeta('Jornada semanal de las personas ocupadas',
                    f'Muestra: {c.f_ent(muj.n_muestral)} mujeres y {c.f_ent(hom.n_muestral)} hombres ocupados de la CDMX.'):
    c.leyenda([(n, color, 'cuadro') for n, _, color in componentes])
    filas = [{'categoria': cortas.get(grupo, grupo), 'componente': n, 'valor': fila[col], 'texto': c.f_horas(fila[col])}
             for grupo, fila in jornada.iterrows() for n, col, _ in componentes]
    totales = {cortas.get(grupo, grupo): c.f_horas(fila.horas_jornada_total) for grupo, fila in jornada.iterrows()}
    st.altair_chart(g.barra_apilada(pd.DataFrame(filas), orden=list(totales), totales=totales,
                                    componentes=[(n, color) for n, _, color in componentes]), width='stretch')
    st.dataframe(pd.DataFrame({
        'Componente': [n for n, _, _ in componentes] + ['Jornada total'],
        'Mujeres ocupadas': [c.f_horas(muj[col]) for _, col, _ in componentes] + [c.f_horas(muj.horas_jornada_total)],
        'Hombres ocupados (ref.)': [c.f_horas(hom[col]) for _, col, _ in componentes] + [c.f_horas(hom.horas_jornada_total)],
    }), hide_index=True, width='stretch')
    st.caption(f'La brecha de {c.f_num(brecha)} h se calcula con los valores sin redondear; restar las cifras de un '
               'decimal de esta tabla da una décima menos.')
    c.nota_fuente('INEGI, ENUT 2024', 'CDMX')

# --- La ciudad frente al país -----------------------------------------------------------
st.space('medium')
c.subtitulo('La ciudad frente al país', 'Mujeres de 12 años y más. El nivel nacional se muestra en gris, como contexto.')
c.leyenda_mujeres_hombres('Ciudad de México', 'Nacional (contexto)')
enut = d.tabla('enut_carga_actividad')
enut = enut[enut['sexo'] == 'Mujeres']
cdmx = enut[enut['ambito'] == 'CDMX'].set_index('actividad')
nac = enut[enut['ambito'] == 'Nacional'].set_index('actividad')


def etiqueta_pais(actividad):
    return c.corta(actividad) + (' *' if bool(cdmx.loc[actividad, 'precision_baja']) else '')


def largo_pais(campo, formato):
    filas = []
    for actividad, fila in cdmx.iterrows():
        fragil = bool(fila.precision_baja)
        nota = f'En la CDMX la cifra sale de {c.f_ent(fila.n_muestral)} casos: es frágil, solo un indicio.' if fragil else ''
        filas.append({'categoria': etiqueta_pais(actividad), 'serie': 'Ciudad de México', 'valor': fila[campo],
                      'texto': formato(fila[campo]), 'fragil': fragil, 'nota': nota})
        v = nac.loc[actividad, campo] if actividad in nac.index else None
        filas.append({'categoria': etiqueta_pais(actividad), 'serie': 'Nacional (contexto)', 'valor': v,
                      'texto': formato(v), 'fragil': False, 'nota': ''})
    return pd.DataFrame(filas)


orden_pais = [etiqueta_pais(a) for a in cdmx.index]
series_pais = [('Ciudad de México', ACENTO), ('Nacional (contexto)', REFERENCIA)]
tabla_pais = pd.DataFrame({
    'Actividad (mujeres)': cdmx.index,
    '% CDMX': [c.f_pct(v) for v in cdmx['pct_realiza']],
    '% nacional': [c.f_pct(nac.loc[a, 'pct_realiza']) for a in cdmx.index],
    'h/semana CDMX': [c.f_horas(v) for v in cdmx['horas_semana']],
    'h/semana nacional': [c.f_horas(nac.loc[a, 'horas_semana']) for a in cdmx.index],
    'Casos CDMX': [c.f_ent(n) + (' *' if f else '') for n, f in zip(cdmx['n_muestral'], cdmx['precision_baja'])],
})
nota_fragil = '\\* Cifra de la CDMX con menos de 100 casos: frágil, se muestra atenuada.'
izq, der = st.columns(2, gap='medium')
with izq, c.tarjeta('Qué porcentaje de las mujeres cuida', '% de las mujeres de 12 años y más.'):
    st.altair_chart(g.barras_comparadas(largo_pais('pct_realiza', c.f_pct), orden=orden_pais, series=series_pais,
                                        sufijo=' %'), width='stretch')
    st.caption(nota_fragil)
    c.nota_fuente('INEGI, ENUT 2024', ['CDMX', 'Nacional'])
    c.ver_tabla(tabla_pais)
with der, c.tarjeta('Cuántas horas a la semana le dedican', 'Promedio entre las mujeres que realizan la actividad.'):
    st.altair_chart(g.barras_comparadas(largo_pais('horas_semana', c.f_horas), orden=orden_pais, series=series_pais,
                                        sufijo=' h'), width='stretch')
    st.caption(nota_fragil)
    c.nota_fuente('INEGI, ENUT 2024', ['CDMX', 'Nacional'])
    c.ver_tabla(tabla_pais)

# --- Brecha por actividad ---------------------------------------------------------------
st.space('medium')
c.subtitulo('Cuánto más cuidan las mujeres',
            'Horas a la semana entre quienes realizan cada actividad. La barra es de las mujeres y el punto gris, de '
            'los hombres (referencia); la etiqueta dice cuántas veces las horas de ellas equivalen a las de ellos.')
br = d.tabla('enut_brecha_mujeres_cdmx')
br_df = pd.DataFrame({
    'categoria': [c.corta(a) + (' *' if n < 100 else '') for a, n in zip(br['actividad'], br['n_mujeres'])],
    'valor': br['horas_mujeres'], 'referencia': br['horas_hombres_ref'],
    'texto': [f'{c.f_horas(h)} · {c.f_num(r, 2)}×' for h, r in zip(br['horas_mujeres'], br['razon_mujeres_hombres'])],
    'texto_ref': [c.f_horas(v) for v in br['horas_hombres_ref']],
    'fragil': br['n_mujeres'] < 100,
    'nota': [f'{c.f_pct(p)} de las mujeres lo realiza' + (f'; solo {n} casos: cifra frágil' if n < 100 else '')
             for p, n in zip(br['pct_realiza_mujeres'], br['n_mujeres'])],
})
with c.tarjeta('Brecha de horas por actividad, Ciudad de México',
               'Mujeres que realizan la actividad frente a hombres que la realizan (referencia).'):
    c.leyenda([('Mujeres que lo realizan', ACENTO, 'cuadro'), ('Hombres que lo realizan (referencia)', REFERENCIA, 'punto')])
    st.altair_chart(g.barras_con_referencia(br_df, orden=br_df['categoria'].tolist()), width='stretch')
    st.caption('\\* Menos de 100 casos en la muestra: la cifra es frágil y se lee solo como indicio.')
    c.nota_fuente('INEGI, ENUT 2024', 'CDMX')
    c.ver_tabla(pd.DataFrame({
        'Actividad': br['actividad'],
        '% de mujeres que lo realiza': [c.f_pct(v) for v in br['pct_realiza_mujeres']],
        'h/semana mujeres': [c.f_horas(v) for v in br['horas_mujeres']],
        'h/semana hombres (ref.)': [c.f_horas(v) for v in br['horas_hombres_ref']],
        'Mujeres / hombres': [c.f_num(v, 2) for v in br['razon_mujeres_hombres']],
        'Casos (mujeres)': [c.f_ent(n) + (' *' if n < 100 else '') for n in br['n_mujeres']],
    }))

# --- ¿Qué mujeres cuidan más? -------------------------------------------------------------
st.space('medium')
c.subtitulo('¿Qué mujeres cuidan más?',
            'Horas de cuidado a la semana, promedio por mujer del grupo, contando también a las que no cuidan (por eso '
            'son menores que en la brecha). Las dos vistas son la misma población partida de dos maneras: no se suman.')
grupos = d.tabla('enut_cuidado_por_grupo')
# El diccionario de datos obliga a filtrar por tipo_grupo antes de graficar.
edad = grupos[grupos['tipo_grupo'] == 'Grupo de edad']
condicion = grupos[grupos['tipo_grupo'] == 'Condición de actividad'].sort_values('horas_cuidado', ascending=False)


def df_grupo(sub):
    confiable = sub['confiable'].fillna(False).astype(bool)
    return pd.DataFrame({
        'categoria': [gr + ('' if ok else ' †') for gr, ok in zip(sub['grupo'], confiable)],
        'serie': 'Horas de cuidado por mujer', 'valor': sub['horas_cuidado'],
        'texto': [c.f_horas(v) for v in sub['horas_cuidado']], 'fragil': ~confiable,
        'nota': [f'{c.f_pct(p)} de las mujeres del grupo cuida; {c.f_ent(n)} casos' + ('' if ok else '; muestra chica: solo indicio')
                 for p, n, ok in zip(sub['pct_que_cuida'], sub['n_muestral'], confiable)],
    })


def tabla_grupo(titulo, sub):
    confiable = sub['confiable'].fillna(False).astype(bool)
    return pd.DataFrame({titulo: sub['grupo'],
                         'h/semana (promedio por mujer)': [c.f_horas(v) for v in sub['horas_cuidado']],
                         '% que cuida': [c.f_pct(v) for v in sub['pct_que_cuida']],
                         'Casos': [c.f_ent(n) + ('' if ok else ' †') for n, ok in zip(sub['n_muestral'], confiable)]})


nota_daga = '† Menos de 60 casos: la cifra no se cita como dato, solo como indicio. Se muestra atenuada.'
izq, der = st.columns(2, gap='medium')
with izq, c.tarjeta('Por grupo de edad', 'Mujeres de 12 años y más de la CDMX.'):
    de = df_grupo(edad)
    st.altair_chart(g.columnas(de, orden=de['categoria'].tolist()), width='stretch')
    if (~edad['confiable'].fillna(False).astype(bool)).any():
        st.caption(nota_daga)
    c.nota_fuente('INEGI, ENUT 2024', 'CDMX')
    c.ver_tabla(tabla_grupo('Grupo de edad', edad))
with der, c.tarjeta('Por condición de actividad', 'Mujeres de 12 años y más de la CDMX.'):
    dc = df_grupo(condicion)
    st.altair_chart(g.barras_comparadas(dc, orden=dc['categoria'].tolist(),
                                        series=[('Horas de cuidado por mujer', ACENTO)], sufijo=' h',
                                        ancho_etiqueta=190), width='stretch')
    if (~condicion['confiable'].fillna(False).astype(bool)).any():
        st.caption(nota_daga)
    c.nota_fuente('INEGI, ENUT 2024', 'CDMX')
    c.ver_tabla(tabla_grupo('Condición de actividad', condicion))

st.space('medium')
c.subtitulo('Lo que dicen los datos de la ciudad')
c.hallazgos(d.hallazgos('cdmx'))
