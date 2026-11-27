"""México. Lo general: el cuidado en todo el país (ENUT 2024, nacional) y la relación de
las cuidadoras con los servicios (ENASIC 2022, que SOLO es nacional)."""

import pandas as pd
import streamlit as st

import componentes as c
import datos as d
import graficas as g
from estilo import ACENTO, REFERENCIA

c.encabezado(
    'Escala nacional', 'México: el cuidado que sostienen las mujeres',
    'El trabajo de cuidado no remunerado (atender a niñas y niños, a personas mayores, enfermas o con '
    'discapacidad) es una parte de la economía que no se paga ni aparece en los salarios, y recae sobre '
    'todo en las mujeres. Así se ve en todo el país.',
    'INEGI, ENUT 2024 (nacional) · INEGI, ENASIC 2022 (nacional)', 'Nacional')

enut = d.tabla('enut_carga_actividad')
nac = enut[enut['ambito'] == 'Nacional']
muj = nac[nac['sexo'] == 'Mujeres'].set_index('actividad')
hom = nac[nac['sexo'] == 'Hombres'].set_index('actividad')
total_m, total_h = muj.loc[d.TOTAL_CUIDADO], hom.loc[d.TOTAL_CUIDADO]

enasic = d.tabla('enasic_cuidadoras')
temas = {t: enasic[enasic['tema'] == t] for t in d.TEMAS_ENASIC}


def pct_de(tema, categoria):
    fila = temas[tema][temas[tema]['categoria'] == categoria]
    return None if fila.empty else float(fila['pct'].iloc[0])


busco, no_busco = pct_de('Búsqueda de servicios', 'Sí buscó'), pct_de('Búsqueda de servicios', 'No buscó')
casa = pct_de('Preferencia de cuidado', 'En su casa')

c.indicadores([
    dict(etiqueta='Mujeres de 12 años y más que cuidan a integrantes de su hogar', valor=c.f_pct(total_m.pct_realiza),
         contexto=f'Hombres (referencia): {c.f_pct(total_h.pct_realiza)}', nivel='Nacional', fuente='INEGI, ENUT 2024'),
    dict(etiqueta='Horas a la semana que dedican las que cuidan', valor=c.f_horas(total_m.horas_semana),
         contexto=f'Hombres que cuidan (referencia): {c.f_horas(total_h.horas_semana)}', nivel='Nacional',
         fuente='INEGI, ENUT 2024'),
    dict(etiqueta='Mujeres cuidadoras que buscó un servicio de cuidado', valor=c.f_pct(busco),
         contexto='Guardería, casa de día o asilo.', nivel='Nacional', fuente='INEGI, ENASIC 2022'),
    dict(etiqueta='Mujeres cuidadoras que preferiría el cuidado en casa', valor=c.f_pct(casa),
         contexto='Si tuviera que contratar un servicio.', nivel='Nacional', fuente='INEGI, ENASIC 2022'),
])

st.space('medium')
c.subtitulo('Quiénes cuidan y cuánto tiempo',
            'Porcentaje de la población de 12 años y más que realiza cada tipo de cuidado, y horas a la semana '
            'que le dedica quien lo realiza. Los hombres aparecen solo como referencia para medir la brecha.')
c.leyenda_mujeres_hombres()

orden = [c.corta(a) for a in muj.index]
series = [('Mujeres', ACENTO), ('Hombres (referencia)', REFERENCIA)]


def largo(campo, formato):
    filas = []
    for actividad in muj.index:
        for serie, tabla in (('Mujeres', muj), ('Hombres (referencia)', hom)):
            v = tabla.loc[actividad, campo] if actividad in tabla.index else None
            filas.append({'categoria': c.corta(actividad), 'serie': serie, 'valor': v,
                          'texto': formato(v), 'fragil': False, 'nota': ''})
    return pd.DataFrame(filas)


tabla_enut = pd.DataFrame({
    'Actividad': muj.index,
    '% mujeres que lo realiza': [c.f_pct(v) for v in muj['pct_realiza']],
    '% hombres (ref.)': [c.f_pct(hom.loc[a, 'pct_realiza']) for a in muj.index],
    'h/semana mujeres': [c.f_horas(v) for v in muj['horas_semana']],
    'h/semana hombres (ref.)': [c.f_horas(hom.loc[a, 'horas_semana']) for a in muj.index],
    'Casos (mujeres)': [c.f_ent(v) for v in muj['n_muestral']],
})

izq, der = st.columns(2, gap='medium')
with izq, c.tarjeta('Qué porcentaje cuida, por tipo de cuidado',
                    '% de la población de 12 años y más que realiza la actividad.'):
    st.altair_chart(g.barras_comparadas(largo('pct_realiza', c.f_pct), orden=orden, series=series, sufijo=' %'),
                    width='stretch')
    c.nota_fuente('INEGI, ENUT 2024', 'Nacional')
    c.ver_tabla(tabla_enut)
with der, c.tarjeta('Cuántas horas a la semana le dedican',
                    'Promedio entre quienes realizan la actividad (no entre toda la población).'):
    st.altair_chart(g.barras_comparadas(largo('horas_semana', c.f_horas), orden=orden, series=series, sufijo=' h'),
                    width='stretch')
    c.nota_fuente('INEGI, ENUT 2024', 'Nacional')
    c.ver_tabla(tabla_enut)

hallazgos = d.hallazgos('nacional')
c.hallazgos([h for h in hallazgos if 'ENUT' in h['fuente']])

st.space('medium')
c.subtitulo('Las cuidadoras y los servicios de cuidado')
st.info('**Cifras solo nacionales.** Los microdatos públicos de la ENASIC 2022 no traen entidad ni municipio: '
        'estas cifras describen a las cuidadoras de todo el país y no se pueden atribuir a la Ciudad de México '
        'ni ponerse en un mapa. Cada gráfica indica su base, porque cambia entre preguntas.',
        icon=':material/public:')


def base_de(tema):
    t = temas[tema]
    return (t['base'].iloc[0], t['variable_enasic'].iloc[0]) if len(t) else ('—', '—')


izq, der = st.columns(2, gap='medium')
with izq, c.tarjeta('¿Buscaron un servicio de cuidado?', 'Base: {} ({}).'.format(*base_de('Búsqueda de servicios'))):
    c.medidores([('Buscó una guardería, casa de día o asilo', busco), ('No buscó', no_busco)])
    c.nota_fuente('INEGI, ENASIC 2022', 'Nacional')
with der, c.tarjeta('¿Cuidarían a cambio de un pago?', 'Base: {} ({}).'.format(*base_de('Disposición a cuidar'))):
    c.medidores([(f.categoria, f.pct) for f in temas['Disposición a cuidar'].itertuples()])
    c.nota_fuente('INEGI, ENASIC 2022', 'Nacional')


def grafica_tema(tema):
    t = temas[tema]
    df = pd.DataFrame({'categoria': t['categoria'], 'serie': '% de mujeres cuidadoras', 'valor': t['pct'],
                       'texto': [c.f_pct(v) for v in t['pct']], 'fragil': False, 'nota': ''})
    return g.barras_comparadas(df, orden=t['categoria'].tolist(), series=[('% de mujeres cuidadoras', ACENTO)],
                               sufijo=' %', ancho_etiqueta=210)


def tabla_tema(tema):
    t = temas[tema]
    return pd.DataFrame({'Respuesta': t['categoria'], '%': [c.f_pct(v) for v in t['pct']]})


izq, der = st.columns(2, gap='medium')
with izq, c.tarjeta('¿Por qué no buscaron un servicio?',
                    f'Base: {base_de("Razones para no buscar")[0]}. Respuesta múltiple: los porcentajes no suman 100.'):
    st.altair_chart(grafica_tema('Razones para no buscar'), width='stretch')
    c.nota_fuente('INEGI, ENASIC 2022', 'Nacional')
    c.ver_tabla(tabla_tema('Razones para no buscar'))
with der, c.tarjeta('Si contrataran un servicio, ¿dónde lo preferirían?',
                    f'Base: {base_de("Preferencia de cuidado")[0]}. Una sola respuesta: suma 100 %.'):
    st.altair_chart(grafica_tema('Preferencia de cuidado'), width='stretch')
    c.nota_fuente('INEGI, ENASIC 2022', 'Nacional')
    c.ver_tabla(tabla_tema('Preferencia de cuidado'))

c.hallazgos([h for h in hallazgos if 'ENASIC' in h['fuente']])
