"""Decisión. Del dato a la decisión: la oferta formal no va a cerrar la brecha (serie y
pronóstico del DENUE), cuánto se cuida en cada zona (modelo de horas con la ENUT y el
Censo) y si conviene invertir en una red de cuidado a domicilio en Iztapalapa (escenarios,
VAN y simulador). Es la capa analítica del trabajo integrador (notebook 03).

El programa y su operador son un escenario simulado; los datos del observatorio no.
"""

import pandas as pd
import streamlit as st

import componentes as c
import datos as d
import graficas as g
from estilo import ACENTO, CRITICO, REFERENCIA

fac = d.factibilidad
FECHA_PERIODO = {'2026-S2': '2026-11-01', '2027-S1': '2027-05-01', '2027-S2': '2027-11-01'}
SERIES = ['Total de respaldo', 'Guardería', 'Residencia / asilo', 'Centro de día']
COLORES = {'Pesimista': CRITICO, 'Realista': ACENTO, 'Optimista': '#2a9d5c', 'Tu escenario': '#3e3d3a'}


def pesos(v, millones=False):
    if c.vacio(v):
        return '—'
    signo = '−' if v < 0 else ''
    return f'{signo}${abs(v) / 1e6:,.2f} M' if millones else f'{signo}${abs(v):,.0f}'


def meses(v, corto=False):
    if c.vacio(v):
        return 'No se recupera'
    return f'{int(v)} meses' if corto else f'{int(v)} meses ({v / 12:.1f} años)'


def md(texto):
    """Escapa el signo de pesos: en Markdown de Streamlit, $...$ se lee como LaTeX."""
    return texto.replace('$', '\\$')


def tir(v):
    """TIR anual como fracción (0.315) -> '31.5 %'."""
    return 'No existe' if c.vacio(v) else c.f_pct(v * 100)


# --- Datos -----------------------------------------------------------------------------------
hist = d.tabla('oferta_historica')
total_ed = hist.groupby('edicion')['establecimientos'].sum()
oferta_hoy, oferta_2016 = int(total_ed.loc['2026-05']), int(total_ed.loc['2016-01'])
horas = d.tabla('horas_cuidado_ageb')
sin = horas[horas['sin_respaldo'].fillna(False)]
horas_sin = float(sin['horas_semana_total'].sum())
hm_sin = horas_sin / float(sin['mujeres_15a59'].sum())
hm_ciudad = float(horas['horas_semana_total'].sum()) / float(horas['mujeres_15a59'].sum())
esc = d.tabla('escenarios_programa')


def valor(escenario, indicador):
    fila = esc[(esc['escenario'] == escenario) & (esc['indicador'] == indicador)]
    return None if fila.empty or pd.isna(fila['valor'].iloc[0]) else float(fila['valor'].iloc[0])


fam_real, pe_fam = valor('Realista', 'Familias atendidas en estado estable'), valor('Realista', 'Punto de equilibrio en familias')
ve_rev, van_real = valor('Valor esperado', 'VAN con revisión en el mes 12'), valor('Realista', 'VAN')
sub_eq = valor('Zona del programa', 'Subsidio mínimo para VAN ≥ 0 (realista)')
sub_real = valor('Realista', 'Supuesto: Subsidio público por hora')

# --- Encabezado y KPIs ------------------------------------------------------------------------
c.encabezado(
    'Del dato a la decisión', '¿Conviene una red de cuidado a domicilio en Iztapalapa?',
    'La oferta formal de cuidado se contrajo y no hay señales de que vuelva a crecer por sí sola. Mientras tanto, '
    'en las zonas sin respaldo las mujeres cargan más horas de cuidado. Esta página junta el pronóstico, el '
    'modelo y la evaluación financiera de un programa que deriva de esos hallazgos, y termina en una recomendación.',
    'INEGI, DENUE (19 ediciones, 2016-2026) · Modelo PP7 con INEGI, ENUT 2024 y Censo 2020 · Escenario simulado PP7',
    ['CDMX', 'AGEB'])
st.info('**Escenario simulado.** El programa y su operador (Centro Comunitario «Manos que Cuidan», Iztapalapa) son '
        'hipotéticos, como acordó el equipo al no tener institución de partida. Los datos del observatorio son '
        'reales; los supuestos financieros llevan su fuente en `backend/observatorio/factibilidad.py`.',
        icon=':material/science:')

c.kpis_con_meta([
    {'etiqueta': 'Oferta formal de respaldo en la CDMX', 'valor': c.f_ent(oferta_hoy),
     'meta': f'Referencia: {c.f_ent(oferta_2016)} en 01/2016 ({c.f_cambio((oferta_hoy / oferta_2016 - 1) * 100)}). '
             'Pronóstico a 2027-S2: sin recuperación.',
     'estado': 'critico', 'detalle_estado': 'a la baja', 'nivel': 'CDMX', 'fuente': 'DENUE 2016-2026'},
    {'etiqueta': 'Horas de cuidado a la semana en las 88 AGEB sin respaldo', 'valor': f'{horas_sin / 1e6:,.2f} M h',
     'meta': f'{c.f_num(hm_sin)} h por mujer contra {c.f_num(hm_ciudad)} h en la ciudad '
             f'(≈ {c.f_ent(horas_sin / 40)} jornadas de 40 h).',
     'estado': 'aviso', 'detalle_estado': 'carga mayor', 'nivel': 'AGEB', 'exploratorio': True,
     'fuente': 'Modelo con ENUT + Censo'},
    {'etiqueta': 'Familias del programa en estado estable (realista)', 'valor': c.f_ent(fam_real),
     'meta': f'Meta: punto de equilibrio de {c.f_ent(pe_fam)} familias ({c.f_cambio((fam_real / pe_fam - 1) * 100)}).',
     'estado': 'ok' if fam_real >= pe_fam else 'critico', 'nivel': 'AGEB', 'simulado': True,
     'fuente': 'Escenario simulado'},
    {'etiqueta': 'VAN esperado, invirtiendo por etapas', 'valor': pesos(ve_rev, millones=True),
     'meta': f'Meta: VAN > 0 al 10 % real. Realista: {pesos(van_real, millones=True)}.',
     'estado': 'ok' if ve_rev > 0 else 'critico', 'nivel': 'AGEB', 'simulado': True, 'fuente': 'Escenario simulado'},
    {'etiqueta': 'Subsidio mínimo para VAN ≥ 0', 'valor': f'${sub_eq:,.2f}/h',
     'meta': f'Supuesto del escenario realista: ${sub_real:,.0f}/h. Margen de solo ${sub_real - sub_eq:,.2f}.',
     'estado': 'aviso', 'detalle_estado': 'variable crítica', 'nivel': 'AGEB', 'simulado': True,
     'fuente': 'Escenario simulado'},
])

# --- 1. La oferta -------------------------------------------------------------------------------
st.space('medium')
c.subtitulo('1 · La oferta formal no va a cerrar la brecha',
            'Establecimientos de respaldo en cada edición del DENUE y pronóstico a 1, 2 y 3 semestres. Las caídas '
            'llegan en escalones, cuando el DENUE incorpora un censo económico: acumulan cierres de varios años.')
with st.container(border=True, horizontal=True, gap='medium', vertical_alignment='bottom'):
    serie = st.pills('Serie', SERIES, default='Total de respaldo', key='serie_oferta') or 'Total de respaldo'
    alternativo = st.selectbox('Comparar con otro método', ['Ninguno', 'Holt amortiguado', 'Deriva', 'ARIMA(0,1,1)'],
                               index=1, key='metodo_alt', width=260)

h = hist if serie == 'Total de respaldo' else hist[hist['tipo'] == serie]
h = (h.groupby(['edicion', 'periodo'], as_index=False)['establecimientos'].sum()
     .rename(columns={'establecimientos': 'valor'}))
h['fecha'] = pd.to_datetime(h['edicion'] + '-01')
h['texto'] = h['valor'].map(c.f_ent)
pron = d.tabla('pronostico_oferta')
p = pron[(pron['serie'] == serie) & pron['elegido']].copy()
p['fecha'] = pd.to_datetime(p['periodo'].map(FECHA_PERIODO))
alt_df = None
if alternativo != 'Ninguno':
    alt_df = pron[(pron['serie'] == serie) & (pron['metodo'] == alternativo)].copy()
    alt_df = alt_df.assign(fecha=pd.to_datetime(alt_df['periodo'].map(FECHA_PERIODO)), valor=alt_df['pronostico'])[
        ['fecha', 'valor', 'metodo', 'periodo']]
eventos = [(pd.Timestamp('2019-02-01'), 'Fin de Estancias Infantiles\ny Censos Económicos 2019'),
           (pd.Timestamp('2024-08-01'), 'Censos Económicos\n2024')]
cambio = (h['valor'].iloc[-1] / h['valor'].iloc[0] - 1) * 100
with c.tarjeta(f'{serie}: {c.f_ent(h["valor"].iloc[0])} en 2016 → {c.f_ent(h["valor"].iloc[-1])} en 2026 ({c.f_cambio(cambio)})',
               'Línea continua: observado. Línea discontinua y bandas: pronóstico ingenuo (el que ganó el backtesting) '
               'con intervalos empíricos de 80 % y 95 %. Gris punteado: método alternativo.'):
    st.altair_chart(g.serie_y_pronostico(h, p, eventos=eventos, alternativo=alt_df), width='stretch')
    c.leyenda([('Observado', ACENTO, 'cuadro'), ('Pronóstico ingenuo e intervalos', ACENTO, 'hueco'),
               ('Método alternativo', REFERENCIA, 'cuadro')])
    c.nota_fuente('INEGI, DENUE (19 ediciones, 01/2016 a 05/2026)', 'CDMX')
    c.ver_tabla(p[['periodo', 'pronostico', 'li_80', 'ls_80', 'li_95', 'ls_95']].rename(columns={
        'periodo': 'Semestre', 'pronostico': 'Pronóstico', 'li_80': 'Mín. 80 %', 'ls_80': 'Máx. 80 %',
        'li_95': 'Mín. 95 %', 'ls_95': 'Máx. 95 %'}), titulo='Ver el pronóstico en tabla')

val = d.tabla('validacion_modelos')
bt = val[val['tarea'].str.startswith('Pronóstico') & (val['metrica'] == 'MAPE')]
izq, der = st.columns([1, 1], gap='medium')
with izq, c.tarjeta('¿Por qué el pronóstico ingenuo?', 'MAPE con origen móvil a 1 semestre (9 pronósticos). Menos es mejor.'):
    b1 = bt[bt['tarea'].str.contains('h = 1')].sort_values('valor')
    st.altair_chart(g.barras_horizontales(pd.DataFrame({'categoria': b1['modelo'], 'valor': b1['valor'],
                                                        'texto': b1['valor'].map(lambda v: f'{v:.1f} %')}),
                                          sufijo=' %', destacar='Ingenuo', ancho_etiqueta=170), width='stretch')
    st.caption('Los modelos con tendencia leen los escalones como pendiente y pronostican caídas que no ocurren '
               'entre censos. El suavizamiento simple empata porque, con esta serie, se vuelve el ingenuo.')
with der, c.tarjeta('Lo que el pronóstico no ve',
                    'Dos cambios estructurales que no están en la serie y por eso se tratan como riesgo.'):
    st.markdown('- **Al alza:** los **300 Centros de Cuidado Infantil** gratuitos que anunció el Gobierno de la '
                'CDMX al instalar la Junta del Sistema de Cuidados (septiembre de 2026). Atienden de 0 a 6 años, '
                'de 6:30 a 18:00.\n'
                '- **A la baja:** los próximos **Censos Económicos (2029)**, que podrían traer otro escalón, como '
                'en 2019 y 2024.\n\n'
                'Por eso el programa se enfoca en lo que esos centros no cubren: personas mayores y con '
                'discapacidad, y horarios fuera de 6:30 a 18:00.')

# --- 2. Cuánto se cuida ---------------------------------------------------------------------------
st.space('medium')
c.subtitulo('2 · Cuánto se cuida en cada zona: modelo de horas de cuidado',
            'Una regresión lineal con la ENUT 2024 predice las horas semanales de cuidado de cada mujer de 15 a 59 '
            'según su hogar. Como sus variables existen en el Censo por AGEB, se puede aplicar a cada AGEB '
            '(estimación en áreas pequeñas), calibrada para que la CDMX dé lo que mide la ENUT.')
por_alc = (horas.groupby('alcaldia', as_index=False)[['horas_semana_total', 'mujeres_15a59']].sum()
           .assign(valor=lambda x: x['horas_semana_total'] / x['mujeres_15a59']).sort_values('valor', ascending=False))
por_alc['categoria'] = por_alc['alcaldia']
por_alc['texto'] = por_alc['valor'].map(lambda v: f'{v:.1f} h')
izq, der = st.columns([1, 1], gap='medium')
with izq:
    alc = st.selectbox('Alcaldía a destacar', por_alc['alcaldia'].tolist(),
                       index=por_alc['alcaldia'].tolist().index('Iztapalapa'), key='alc_horas', width=300)
    fila = por_alc[por_alc['alcaldia'] == alc].iloc[0]
    with c.tarjeta('Horas de cuidado por mujer de 15 a 59, a la semana (estimación)',
                   f'{alc}: {fila["valor"]:.1f} h por mujer y {c.f_ent(fila["horas_semana_total"])} horas a la semana en total.'):
        st.altair_chart(g.barras_horizontales(por_alc[['categoria', 'valor', 'texto']], sufijo=' h', destacar=alc,
                                              ancho_etiqueta=170), width='stretch')
        st.caption('Estimación, no medición: hereda el error del modelo (≈ 8 % en una entidad; más en una AGEB) y las '
                   'ubicaciones aproximadas del hallazgo B.')
        c.nota_fuente('Modelo PP7 con INEGI, ENUT 2024 + Censo 2020', 'Alcaldía', exploratorio=True)
with der:
    coef = d.tabla('modelo_horas_coeficientes')
    coef = coef[~coef['variable'].isin(['constante', 'urbana'])].sort_values('coeficiente', ascending=False)
    with c.tarjeta('Qué mueve las horas de cuidado de una mujer',
                   'Horas semanales que suma o resta cada variable, manteniendo las demás fijas (ENUT 2024, '
                   '30,301 mujeres de 15 a 59).'):
        st.altair_chart(g.barras_horizontales(pd.DataFrame({
            'categoria': coef['descripcion'], 'valor': coef['coeficiente'],
            'texto': coef['coeficiente'].map(lambda v: f'{"−" if v < 0 else "+"}{abs(v):.1f} h')}), sufijo=' h', ancho_etiqueta=300), width='stretch')
        c.nota_fuente('Modelo PP7 con INEGI, ENUT 2024', 'Nacional')
    eco = val[val['tarea'].str.startswith('Horas de cuidado promedio') & (val['metrica'] == 'MAPE')].sort_values('valor')
    with c.tarjeta('¿Por qué una regresión lineal y no un Random Forest?',
                   'Error al predecir el promedio de una entidad que el modelo no vio (MAPE, 32 entidades).'):
        st.altair_chart(g.barras_horizontales(pd.DataFrame({
            'categoria': eco['modelo'], 'valor': eco['valor'], 'texto': eco['valor'].map(lambda v: f'{v:.1f} %')}),
            sufijo=' %', destacar='Regresión lineal', ancho_etiqueta=250), width='stretch')
        st.caption('El Random Forest gana por poco con mujeres individuales (R² 0.36 contra 0.31), pero se desploma con '
                   'promedios, que es lo único que publica el Censo. El promedio de las predicciones de un modelo lineal '
                   'es la predicción del promedio; el de un bosque, no.')

# --- 3. ¿Conviene invertir? ----------------------------------------------------------------------------
st.space('medium')
c.subtitulo('3 · ¿Conviene invertir? Tres escenarios y un simulador',
            'Red de Cuidado a Domicilio en las 25 AGEB de Iztapalapa sin respaldo (9,415 hogares con necesidad de '
            'cuidado). Piloto de 15 familias y 6 cuidadoras y escalamiento hasta el estado estable; flujos mensuales '
            'a 60 meses en pesos de 2026, descontados al 10 % real (tasa social de descuento de la SHCP).')

resultados = fac.evaluar_escenarios()
FILAS = [('Probabilidad asignada', lambda r: c.f_pct(fac.PROBABILIDADES[r.escenario] * 100, 0)),
         ('Adopción (hogares de la zona)', lambda r: c.f_pct(r.supuestos.adopcion * 100)),
         ('Horas por familia a la semana', lambda r: c.f_num(r.supuestos.horas_semana_familia, 0)),
         ('Subsidio por hora', lambda r: f'${r.supuestos.subsidio_hora:,.0f}'),
         ('VAN (operando 60 meses)', lambda r: pesos(r.van)),
         ('VAN con revisión en el mes 12', lambda r: pesos(r.van_con_revision)),
         ('¿Se cierra en la revisión?', lambda r: 'Sí' if r.se_cierra_en_revision else 'No'),
         ('TIR anual', lambda r: tir(r.tir_anual)),
         ('Payback', lambda r: meses(r.payback_meses, corto=True)),
         ('Punto de equilibrio', lambda r: f'{c.f_ent(r.punto_equilibrio_familias)} familias' if r.punto_equilibrio_familias else '—'),
         ('Familias en estado estable', lambda r: c.f_ent(r.familias_estable)),
         ('Cuidadoras empleadas', lambda r: c.f_ent(r.cuidadoras_estable)),
         ('Capital (fórmula clásica)', lambda r: pesos(r.capital_total)),
         ('Déficit acumulado máximo', lambda r: pesos(r.deficit_maximo))]
tabla = pd.DataFrame({'Indicador': [f for f, _ in FILAS],
                      **{n: [fn(r) for _, fn in FILAS] for n, r in resultados.items()}})
izq, der = st.columns([1.05, 1], gap='medium')
with izq, c.tarjeta('Tabla comparativa de escenarios',
                    md(f'Valor esperado del VAN: {pesos(fac.valor_esperado(resultados))} operando pase lo que pase y '
                       f'{pesos(fac.valor_esperado(resultados, con_revision=True))} invirtiendo por etapas.')):
    st.dataframe(tabla, hide_index=True, width='stretch', height=530)
with der:
    with st.container(border=True):
        st.markdown('**Tu escenario: mueve los supuestos**')
        st.caption('Parte del escenario realista. El resultado se calcula en vivo con las mismas reglas del Excel '
                   'del anexo.')
        base = fac.ESCENARIOS['Realista']
        a1, a2 = st.columns(2)
        adop = a1.slider('Adopción (% de hogares)', 0.5, 5.0, base.adopcion * 100, 0.1, format='%.1f %%', key='sim_adop')
        horas_f = a2.slider('Horas por familia a la semana', 4, 14, int(base.horas_semana_familia), key='sim_horas')
        sub = a1.slider('Subsidio público por hora', 0, 60, int(base.subsidio_hora), format='$%d', key='sim_sub')
        mss = a2.slider('Mes en que se llega al estado estable', 9, 30, base.meses_estado_estable, key='sim_mss')
        tasa = a1.slider('Tasa de descuento real', 5.0, 15.0, base.tasa_descuento_anual * 100, 0.5, format='%.1f %%',
                         key='sim_tasa')
        etapas = a2.toggle('Revisión en el mes 12', value=True, key='sim_etapas',
                           help='Invertir por etapas: si en el mes 12 hay menos de la mitad de las familias del punto '
                                'de equilibrio, el programa se cierra.')
        propio = fac.evaluar(fac.con_cambios(base, adopcion=adop / 100, horas_semana_familia=horas_f, subsidio_hora=sub,
                                             meses_estado_estable=mss, tasa_descuento_anual=tasa / 100), 'Tu escenario')
        van_p = propio.van_con_revision if etapas else propio.van
        cierra = etapas and propio.se_cierra_en_revision
        c.indicadores([
            {'etiqueta': 'VAN', 'valor': pesos(van_p, millones=True),
             'contexto': 'Se cierra en el mes 12: no alcanza la mitad del equilibrio.' if cierra else
             ('Positivo: el programa crea valor.' if van_p > 0 else 'Negativo: destruye valor.')},
            {'etiqueta': 'TIR anual', 'valor': '—' if cierra else tir(propio.tir_anual),
             'contexto': f'Payback: {"—" if cierra else meses(propio.payback_meses)}'},
            {'etiqueta': 'Punto de equilibrio',
             'valor': f'{c.f_ent(propio.punto_equilibrio_familias)} fam.' if propio.punto_equilibrio_familias else 'No existe',
             'contexto': f'Familias en estado estable: {c.f_ent(propio.familias_estable)}'},
            {'etiqueta': 'Déficit acumulado máximo', 'valor': pesos(propio.deficit_maximo, millones=True),
             'contexto': 'Lo que hay que financiar antes del equilibrio.'},
        ])

filas_flujo = []
for nombre, r in list(resultados.items()) + [('Tu escenario', propio)]:
    hasta = fac.ESCENARIOS['Realista'].mes_revision + 1 if (nombre == 'Tu escenario' and cierra) else None
    for m in r.meses[:hasta]:
        filas_flujo.append({'mes': m['mes'], 'escenario': nombre, 'millones': m['flujo_acumulado'] / 1e6,
                            'texto': pesos(m['flujo_acumulado'])})
with c.tarjeta('Flujo acumulado por escenario',
               'Cuándo se recupera la inversión. En la revisión del mes 12 se decide seguir o cerrar; si «Tu escenario» '
               'se cierra, la línea termina ahí.'):
    st.altair_chart(g.flujos_acumulados(pd.DataFrame(filas_flujo), colores=COLORES,
                                        mes_revision=fac.ESCENARIOS['Realista'].mes_revision), width='stretch')
    c.nota_fuente('Escenario simulado PP7 (backend/observatorio/factibilidad.py)', 'AGEB')

# --- Recomendación -----------------------------------------------------------------------------------
st.space('medium')
real = resultados['Realista']
st.html(f'''<div class="obs-decision"><h4>Recomendación: invertir por etapas, condicionado a tres cosas</h4>
  <p style="margin:0">El VAN esperado es positivo ({c.esc(pesos(fac.valor_esperado(resultados, con_revision=True), millones=True))}
  invirtiendo por etapas), pero el riesgo no es simétrico: si se opera pase lo que pase, el escenario pesimista pierde
  {c.esc(pesos(-resultados["Pesimista"].van, millones=True))}.</p>
  <ol>
    <li><b>Convenio de subsidio de al menos $40 por hora</b> con el Sistema Público de Cuidados de la CDMX: el VAN
      realista llega a cero con ${sub_eq:,.2f}.</li>
    <li><b>Revisión en el mes 12:</b> seguir solo con al menos {c.esc(c.f_ent(real.punto_equilibrio_familias / 2))}
      familias activas (la mitad del punto de equilibrio). Si no se cumple, cerrar a tiempo limita la pérdida.</li>
    <li><b>Financiamiento comprometido por {c.esc(pesos(real.deficit_maximo * 1.1, millones=True))}</b> (déficit
      acumulado máximo del escenario realista más 10 %). La fórmula clásica de capital da
      {c.esc(pesos(real.capital_total, millones=True))} y se queda corta.</li>
  </ol>
  <p style="margin:8px 0 0;font-size:.9rem;opacity:.85">Cómo medirlo: familias activas contra el punto de equilibrio,
  horas de cuidado al mes, tasa de vinculación de la plataforma, rotación de cuidadoras e incidentes reportados.</p>
</div>''')
