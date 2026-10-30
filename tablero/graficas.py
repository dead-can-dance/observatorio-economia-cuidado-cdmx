"""Gráficas en Altair con las reglas de la guía de visualización.

- Barras delgadas con el extremo de datos redondeado y etiqueta directa solo en la serie
  principal; los hombres (referencia) y el contexto nacional van en gris.
- Las cifras frágiles (muestra chica) se dibujan atenuadas y su categoría lleva * o †.
- El texto usa `currentColor`, así que se lee en tema claro y en oscuro; los ejes y la
  retícula los pone el tema de Streamlit.
- Cada gráfica tiene su tabla en la página (componentes.ver_tabla).

Todas reciben un DataFrame ya preparado, con el texto de las etiquetas formateado.
"""

import altair as alt
import pandas as pd

from estilo import ACENTO, REFERENCIA, TEXTO, texto_sobre

ALTO_BARRA = 14


def _eje_valor(sufijo, maximo=None, titulo=None):
    escala = alt.Scale(domain=[0, maximo], nice=False) if maximo else alt.Scale(nice=True)
    return alt.X('valor:Q', title=titulo, scale=escala,
                 axis=alt.Axis(labelExpr=f"format(datum.value, ',.0f') + '{sufijo}'", tickCount=5,
                               domain=False, ticks=False, labelFontSize=11))


def _eje_categorias(orden, ancho_etiqueta):
    return alt.Y('categoria:N', sort=orden, title=None,
                 scale=alt.Scale(paddingInner=0.3, paddingOuter=0.15),
                 axis=alt.Axis(labelLimit=ancho_etiqueta, ticks=False, domain=False, labelPadding=8,
                               labelFontSize=12))


def _tope(df, columna='valor', holgura=1.22):
    """Deja aire a la derecha para la etiqueta de la barra más larga."""
    maximo = pd.to_numeric(df[columna], errors='coerce').max()
    return float(maximo) * holgura if maximo and maximo == maximo else None


def _tooltip(df):
    campos = [alt.Tooltip('texto:N', title='Valor'), alt.Tooltip('categoria:N', title='Categoría')]
    if 'serie' in df:
        campos.insert(1, alt.Tooltip('serie:N', title='Serie'))
    if 'nota' in df and df['nota'].astype(str).str.len().gt(0).any():
        campos.append(alt.Tooltip('nota:N', title='Nota'))
    return campos


def barras_comparadas(df, *, orden, series, etiquetar=None, sufijo='', ancho_etiqueta=200):
    """Barras horizontales agrupadas. df: categoria, serie, valor, texto, fragil, nota.

    series: [(nombre, color)] en el orden de la leyenda. Solo las series de `etiquetar`
    llevan etiqueta directa (por omisión, la primera).
    """
    nombres = [s for s, _ in series]
    etiquetar = etiquetar or nombres[:1]
    df = df.assign(fragil=df['fragil'].fillna(False).astype(bool))
    alto = len(orden) * (len(nombres) * ALTO_BARRA + 18)
    color = alt.Color('serie:N', sort=nombres, scale=alt.Scale(domain=nombres, range=[c for _, c in series]),
                      legend=None)
    base = alt.Chart(df).encode(y=_eje_categorias(orden, ancho_etiqueta),
                                yOffset=alt.YOffset('serie:N', sort=nombres))
    barras = base.mark_bar(cornerRadiusEnd=4).encode(
        x=_eje_valor(sufijo, _tope(df)), color=color, tooltip=_tooltip(df),
        opacity=alt.condition('datum.fragil', alt.value(0.38), alt.value(1)))
    textos = (base.transform_filter(alt.FieldOneOfPredicate(field='serie', oneOf=list(etiquetar)))
              .mark_text(align='left', dx=5, fontSize=12, color=TEXTO)
              .encode(x='valor:Q', text='texto:N'))
    return (barras + textos).properties(height=alto)


def barra_apilada(df, *, orden, componentes, totales):
    """Doble jornada. df: categoria, componente, valor, texto. componentes: [(nombre, color)].

    totales: {categoria: texto del total}. La etiqueta de cada tramo va dentro solo si cabe.
    """
    nombres = [n for n, _ in componentes]
    colores = dict(componentes)
    df = df.copy()
    df['orden'] = df['componente'].map({n: i for i, n in enumerate(nombres)})
    df = df.sort_values(['categoria', 'orden'])
    df['fin'] = df.groupby('categoria')['valor'].cumsum()
    df['medio'] = df['fin'] - df['valor'] / 2
    df['color_texto'] = df['componente'].map(lambda n: texto_sobre(colores[n]))
    df['cabe'] = df['valor'] >= 7
    tot = pd.DataFrame({'categoria': list(totales), 'texto': list(totales.values())})
    tot['valor'] = tot['categoria'].map(df.groupby('categoria')['valor'].sum())
    maximo = float(tot['valor'].max()) * 1.18

    y = alt.Y('categoria:N', sort=orden, title=None, scale=alt.Scale(paddingInner=0.45, paddingOuter=0.2),
              axis=alt.Axis(ticks=False, domain=False, labelPadding=8, labelFontSize=12, labelLimit=170))
    x = alt.X('valor:Q', stack='zero', title=None, scale=alt.Scale(domain=[0, maximo], nice=False),
              axis=alt.Axis(labelExpr="format(datum.value, ',.0f') + ' h'", tickCount=5, domain=False, ticks=False))
    barras = alt.Chart(df).mark_bar().encode(
        y=y, x=x, order=alt.Order('orden:Q'),
        color=alt.Color('componente:N', sort=nombres, legend=None,
                        scale=alt.Scale(domain=nombres, range=[c for _, c in componentes])),
        tooltip=[alt.Tooltip('texto:N', title='Horas'), alt.Tooltip('componente:N', title='Componente'),
                 alt.Tooltip('categoria:N', title='Grupo')])
    dentro = alt.Chart(df[df['cabe']]).mark_text(fontSize=12, fontWeight=600).encode(
        y=alt.Y('categoria:N', sort=orden), x='medio:Q', text='texto:N',
        color=alt.Color('color_texto:N', scale=None))
    total = alt.Chart(tot).mark_text(align='left', dx=6, fontSize=13, fontWeight=700, color=TEXTO).encode(
        y=alt.Y('categoria:N', sort=orden), x='valor:Q', text='texto:N')
    return (barras + dentro + total).properties(height=len(orden) * 62)


def barras_con_referencia(df, *, orden, ancho_etiqueta=220):
    """Brecha por actividad: barra de las mujeres y punto gris de los hombres (referencia).

    df: categoria, valor (mujeres), referencia (hombres), texto, fragil, nota.
    """
    df = df.assign(fragil=df['fragil'].fillna(False).astype(bool))
    df['tope'] = df[['valor', 'referencia']].max(axis=1)
    y = _eje_categorias(orden, ancho_etiqueta)
    tooltip = [alt.Tooltip('texto:N', title='Mujeres · razón'),
               alt.Tooltip('texto_ref:N', title='Hombres (referencia)'),
               alt.Tooltip('categoria:N', title='Actividad'), alt.Tooltip('nota:N', title='Nota')]
    base = alt.Chart(df).encode(y=y)
    barras = base.mark_bar(cornerRadiusEnd=4, height=ALTO_BARRA + 2, color=ACENTO).encode(
        x=_eje_valor(' h', _tope(df, 'tope', 1.35)), tooltip=tooltip,
        opacity=alt.condition('datum.fragil', alt.value(0.38), alt.value(1)))
    puntos = base.mark_point(filled=True, size=90, color=REFERENCIA, strokeWidth=0).encode(
        x='referencia:Q', tooltip=tooltip)
    textos = base.mark_text(align='left', dx=8, fontSize=12, color=TEXTO).encode(x='tope:Q', text='texto:N')
    return (barras + puntos + textos).properties(height=len(orden) * 44)


def columnas(df, *, orden, sufijo=' h'):
    """Columnas verticales de una sola serie. df: categoria, valor, texto, fragil, nota."""
    df = df.assign(fragil=df['fragil'].fillna(False).astype(bool))
    x = alt.X('categoria:N', sort=orden, title=None, scale=alt.Scale(paddingInner=0.45),
              axis=alt.Axis(labelAngle=0, ticks=False, domain=False, labelFontSize=12, labelPadding=6))
    y = alt.Y('valor:Q', title=None, scale=alt.Scale(domain=[0, _tope(df, holgura=1.2)], nice=False),
              axis=alt.Axis(labelExpr=f"format(datum.value, ',.0f') + '{sufijo}'", tickCount=5,
                            domain=False, ticks=False))
    base = alt.Chart(df).encode(x=x)
    barras = base.mark_bar(cornerRadiusEnd=4, width={'band': 0.55}, color=ACENTO).encode(
        y=y, tooltip=_tooltip(df), opacity=alt.condition('datum.fragil', alt.value(0.38), alt.value(1)))
    textos = base.mark_text(dy=-8, fontSize=12, color=TEXTO).encode(y='valor:Q', text='texto:N')
    return (barras + textos).properties(height=300)


def ranking(df, *, seleccion, referencia=None, sufijo=''):
    """Las 16 alcaldías ordenadas. df: cve_mun, categoria, valor, texto, unidad.

    La alcaldía elegida va en el acento y las demás atenuadas; un clic elige otra.
    """
    df = df.copy()
    df['elegida'] = df['cve_mun'] == seleccion
    df['x_texto'] = df['valor'].fillna(0)
    orden = df['categoria'].tolist()
    nombre = df.loc[df['elegida'], 'categoria']
    nombre = nombre.iloc[0].replace("'", "\\'") if len(nombre) else ''
    punto = alt.selection_point(name='elegida', fields=['cve_mun'], on='click', clear=False)
    y = alt.Y('categoria:N', sort=orden, title=None, scale=alt.Scale(paddingInner=0.32),
              axis=alt.Axis(ticks=False, domain=False, labelPadding=8, labelFontSize=12, labelLimit=170,
                            labelFontWeight=alt.ExprRef(f"datum.value === '{nombre}' ? 700 : 400")))
    tope = _tope(df, holgura=1.2)
    base = alt.Chart(df).encode(y=y)
    barras = base.mark_bar(cornerRadiusEnd=4, height=ALTO_BARRA, color=ACENTO, cursor='pointer').encode(
        x=_eje_valor(sufijo, tope),
        opacity=alt.condition('datum.elegida', alt.value(1), alt.value(0.35)),
        tooltip=[alt.Tooltip('texto:N', title='Valor'), alt.Tooltip('categoria:N', title='Alcaldía'),
                 alt.Tooltip('unidad:N', title='Unidad')]).add_params(punto)
    # El grosor no es un canal de Altair: una capa de texto para la elegida y otra para el resto.
    textos = [base.transform_filter(filtro).mark_text(align='left', dx=5, fontSize=11.5, color=TEXTO, fontWeight=peso)
              .encode(x='x_texto:Q', text='texto:N')
              for filtro, peso in (('datum.elegida', 700), ('!datum.elegida', 400))]
    capas = [barras, *textos]
    if referencia:
        ref = pd.DataFrame({'valor': [referencia[0]], 'texto': [referencia[1]]})
        capas.append(alt.Chart(ref).mark_rule(color=TEXTO, strokeWidth=1, opacity=0.6).encode(x='valor:Q'))
        capas.append(alt.Chart(ref).mark_text(align='left', dx=4, y=-8, fontSize=11, color=TEXTO).encode(
            x='valor:Q', text='texto:N'))
    return alt.layer(*capas).properties(height=len(df) * 28)


def mosaico(df):
    """Una casilla por alcaldía en su posición aproximada (norte arriba).

    df: cve_mun, col, fila, abrev, nombre, texto, relleno, color_texto, elegida, lugar.
    """
    punto = alt.selection_point(name='elegida', fields=['cve_mun'], on='click', clear=False)
    base = alt.Chart(df).encode(
        x=alt.X('col:O', axis=None, scale=alt.Scale(domain=[0, 1, 2, 3], paddingInner=0.08, paddingOuter=0.02)),
        y=alt.Y('fila:O', axis=None, scale=alt.Scale(domain=[0, 1, 2, 3, 4, 5], paddingInner=0.1, paddingOuter=0.02)))
    tooltip = [alt.Tooltip('texto:N', title='Valor'), alt.Tooltip('nombre:N', title='Alcaldía'),
               alt.Tooltip('lugar:N', title='Lugar')]
    casillas = base.mark_rect(cornerRadius=8, cursor='pointer').encode(
        color=alt.Color('relleno:N', scale=None), tooltip=tooltip,
        stroke=alt.condition('datum.elegida', alt.value(TEXTO), alt.value(None)),
        strokeWidth=alt.condition('datum.elegida', alt.value(3), alt.value(0))).add_params(punto)
    abrev = base.mark_text(dy=-11, fontSize=13, fontWeight=700).encode(
        text='abrev:N', color=alt.Color('color_texto:N', scale=None), tooltip=tooltip)
    valor = base.mark_text(dy=11, fontSize=12.5).encode(
        text='texto:N', color=alt.Color('color_texto:N', scale=None), tooltip=tooltip)
    return (casillas + abrev + valor).properties(width=alt.Step(88), height=alt.Step(66))


def dispersion(df, *, medianas, nombre_x, nombre_y, rotulo):
    """Alcaldías: carga de cuidado (x) contra niñas y niños por guardería (y).

    df: cve_mun, abrev, nombre, x, y, texto_x, texto_y, elegida.
    """
    punto = alt.selection_point(name='elegida', fields=['cve_mun'], on='click', clear=False)
    x = alt.X('x:Q', title=nombre_x, scale=alt.Scale(zero=False, padding=20),
              axis=alt.Axis(tickCount=6, domain=False, ticks=False, titleFontWeight=400, titleFontSize=12))
    y = alt.Y('y:Q', title=nombre_y, scale=alt.Scale(zero=False, padding=20),
              axis=alt.Axis(tickCount=6, domain=False, ticks=False, format=',.0f', titleFontWeight=400,
                            titleFontSize=12))
    tooltip = [alt.Tooltip('nombre:N', title='Alcaldía'), alt.Tooltip('texto_x:N', title='Carga'),
               alt.Tooltip('texto_y:N', title='Niñas y niños por guardería')]
    base = alt.Chart(df).encode(x=x, y=y)
    puntos = base.mark_circle(color=ACENTO, cursor='pointer', stroke='white', strokeWidth=1).encode(
        size=alt.condition('datum.elegida', alt.value(260), alt.value(110)),
        opacity=alt.condition('datum.elegida', alt.value(1), alt.value(0.75)), tooltip=tooltip).add_params(punto)
    etiquetas = [base.transform_filter(filtro).mark_text(align='left', dx=9, dy=-7, fontSize=11, color=TEXTO,
                                                          fontWeight=peso).encode(text='abrev:N')
                 for filtro, peso in (('datum.elegida', 700), ('!datum.elegida', 400))]
    mx = pd.DataFrame({'x': [medianas['x']]})
    my = pd.DataFrame({'y': [medianas['y']]})
    reglas = [alt.Chart(mx).mark_rule(strokeDash=[4, 4], color=REFERENCIA).encode(x='x:Q'),
              alt.Chart(my).mark_rule(strokeDash=[4, 4], color=REFERENCIA).encode(y='y:Q')]
    rot = alt.Chart(pd.DataFrame({'t': [rotulo]})).mark_text(
        align='right', baseline='top', x='width', y=4, dx=-4, fontSize=11, color=TEXTO, opacity=0.7).encode(text='t:N')
    return alt.layer(*reglas, puntos, *etiquetas, rot).properties(height=420)


def histograma(df, *, umbral):
    """Carga de cuidado por AGEB en intervalos de 1 punto. df: desde, hasta, grupo, n."""
    grupos = ['Alta carga', 'Resto de las AGEB']
    barras = alt.Chart(df).mark_bar(binSpacing=1).encode(
        x=alt.X('desde:Q', title='Carga de cuidado (personas por cada 100 mujeres)',
                bin=alt.Bin(binned=True, step=1),
                axis=alt.Axis(domain=False, ticks=False, titleFontWeight=400, titleFontSize=11.5)),
        x2='hasta:Q',
        y=alt.Y('n:Q', stack='zero', title=None, axis=alt.Axis(domain=False, ticks=False, tickCount=5)),
        color=alt.Color('grupo:N', sort=grupos, legend=None,
                        scale=alt.Scale(domain=grupos, range=[ACENTO, REFERENCIA])),
        order=alt.Order('orden:Q'),
        tooltip=[alt.Tooltip('n:Q', title='AGEB'), alt.Tooltip('rango:N', title='Carga'),
                 alt.Tooltip('grupo:N', title='Grupo')])
    capas = [barras]
    if umbral is not None:
        u = pd.DataFrame({'u': [umbral], 'texto': [f'Umbral de alta carga: {umbral:,.1f}']})
        capas.append(alt.Chart(u).mark_rule(color=TEXTO, opacity=0.7).encode(x='u:Q'))
        capas.append(alt.Chart(u).mark_text(align='left', dx=4, y=6, baseline='top', fontSize=11, color=TEXTO)
                     .encode(x='u:Q', text='texto:N'))
    return alt.layer(*capas).properties(height=260)


# --- Página «Decisión» ------------------------------------------------------------------------

def serie_y_pronostico(hist, pron, *, eventos, alternativo=None):
    """Serie semestral observada (escalones) y pronóstico con su banda empírica.

    hist: fecha (datetime), valor, texto. pron: fecha, pronostico, li_80, ls_80, li_95, ls_95.
    eventos: [(fecha, texto)] para anotar los escalones. alternativo: fecha, valor, metodo.
    """
    x = alt.X('fecha:T', title=None, axis=alt.Axis(format='%Y', tickCount=8, domain=False, ticks=False))
    tope = float(max(hist['valor'].max(), pron['ls_95'].max())) * 1.18
    escala = alt.Scale(domain=[0, tope], nice=False)
    y = alt.Y('valor:Q', title=None, scale=escala, axis=alt.Axis(format=',.0f', tickCount=5, domain=False, ticks=False))
    ultimo = hist.iloc[[-1]]
    banda = pd.concat([ultimo.assign(li_80=ultimo['valor'], ls_80=ultimo['valor'], li_95=ultimo['valor'],
                                     ls_95=ultimo['valor'], pronostico=ultimo['valor']), pron], ignore_index=True)
    capas = [
        alt.Chart(banda).mark_area(color=ACENTO, opacity=0.12).encode(x='fecha:T', y=alt.Y('li_95:Q', scale=escala), y2='ls_95:Q'),
        alt.Chart(banda).mark_area(color=ACENTO, opacity=0.22).encode(x='fecha:T', y=alt.Y('li_80:Q', scale=escala), y2='ls_80:Q'),
        alt.Chart(hist).mark_line(color=ACENTO, strokeWidth=2.6, interpolate='step-after').encode(
            x=x, y=y, tooltip=[alt.Tooltip('periodo:N', title='Semestre'), alt.Tooltip('texto:N', title='Establecimientos')]),
        alt.Chart(banda).mark_line(color=ACENTO, strokeDash=[6, 4], strokeWidth=2).encode(
            x='fecha:T', y=alt.Y('pronostico:Q', scale=escala),
            tooltip=[alt.Tooltip('periodo:N', title='Semestre'), alt.Tooltip('pronostico:Q', title='Pronóstico', format=',.0f'),
                     alt.Tooltip('li_80:Q', title='Mínimo 80 %', format=',.0f'), alt.Tooltip('ls_80:Q', title='Máximo 80 %', format=',.0f')]),
    ]
    if alternativo is not None and not alternativo.empty:
        alt_df = pd.concat([ultimo.assign(metodo=alternativo['metodo'].iloc[0]), alternativo], ignore_index=True)
        capas.append(alt.Chart(alt_df).mark_line(color=REFERENCIA, strokeDash=[2, 3], strokeWidth=1.6).encode(
            x='fecha:T', y=alt.Y('valor:Q', scale=escala),
            tooltip=[alt.Tooltip('metodo:N', title='Método'), alt.Tooltip('valor:Q', title='Pronóstico', format=',.0f')]))
    ev = pd.DataFrame(eventos, columns=['fecha', 'texto'])
    capas.append(alt.Chart(ev).mark_rule(color='#d03b3b', strokeDash=[2, 3], opacity=0.8).encode(x='fecha:T'))
    capas.append(alt.Chart(ev).mark_text(align='center', baseline='top', y=4, fontSize=10.5, color=TEXTO, lineBreak='\n')
                 .encode(x='fecha:T', text='texto:N'))
    return alt.layer(*capas).properties(height=330)


def barras_horizontales(df, *, sufijo='', ancho_etiqueta=260, destacar=None, color_negativo=REFERENCIA):
    """Barras horizontales de una sola serie. df: categoria, valor, texto. Los negativos en gris."""
    df = df.copy()
    df['opacidad'] = 1.0 if not destacar else df['categoria'].eq(destacar).map({True: 1.0, False: 0.45})
    df['negativo'] = df['valor'] < 0
    orden = df['categoria'].tolist()
    minimo = min(0.0, float(df['valor'].min()) * 1.1)
    maximo = max(0.0, float(df['valor'].max()) * 1.3)
    y = alt.Y('categoria:N', sort=orden, title=None, scale=alt.Scale(paddingInner=0.3),
              axis=alt.Axis(ticks=False, domain=False, labelLimit=ancho_etiqueta, labelFontSize=11.5, labelPadding=8,
                            labelOverlap=False))
    x = alt.X('valor:Q', title=None, scale=alt.Scale(domain=[minimo, maximo], nice=False),
              axis=alt.Axis(labelExpr=f"format(datum.value, ',.0f') + '{sufijo}'", tickCount=5, domain=False, ticks=False))
    base = alt.Chart(df).encode(y=y)
    barras = base.mark_bar(cornerRadiusEnd=4, height=ALTO_BARRA).encode(
        x=x, color=alt.condition('datum.negativo', alt.value(color_negativo), alt.value(ACENTO)),
        opacity=alt.Opacity('opacidad:Q', scale=None),
        tooltip=[alt.Tooltip('categoria:N', title='Categoría'), alt.Tooltip('texto:N', title='Valor')])
    # La etiqueta va a la derecha del extremo positivo; en las barras negativas, a la derecha del cero,
    # para no encimarse con los nombres de las categorías.
    df['x_texto'] = df['valor'].clip(lower=0)
    textos = base.mark_text(align='left', dx=5, fontSize=11.5, color=TEXTO).encode(
        x=alt.X('x_texto:Q', scale=alt.Scale(domain=[minimo, maximo], nice=False)), text='texto:N')
    return alt.layer(barras, textos).properties(height=max(len(df) * 30, 120))


def flujos_acumulados(df, *, colores, mes_revision=None):
    """Flujo acumulado por escenario. df: mes, escenario, millones, texto."""
    nombres = list(colores)
    lineas = alt.Chart(df).mark_line(strokeWidth=2.4).encode(
        x=alt.X('mes:Q', title='Mes', axis=alt.Axis(tickCount=6, domain=False, ticks=False, titleFontWeight=400)),
        y=alt.Y('millones:Q', title='Flujo acumulado (millones de pesos de 2026)',
                axis=alt.Axis(tickCount=6, domain=False, ticks=False, titleFontWeight=400, titleFontSize=11.5)),
        color=alt.Color('escenario:N', sort=nombres, scale=alt.Scale(domain=nombres, range=list(colores.values())),
                        legend=alt.Legend(orient='top', title=None, labelFontSize=12)),
        strokeDash=alt.condition("datum.escenario === 'Tu escenario'", alt.value([6, 4]), alt.value([1, 0])),
        tooltip=[alt.Tooltip('escenario:N', title='Escenario'), alt.Tooltip('mes:Q', title='Mes'),
                 alt.Tooltip('texto:N', title='Flujo acumulado')])
    capas = [alt.Chart(pd.DataFrame({'y': [0]})).mark_rule(color=TEXTO, opacity=0.5).encode(y='y:Q'), lineas]
    if mes_revision:
        r = pd.DataFrame({'mes': [mes_revision], 'texto': [f'Revisión del mes {mes_revision}']})
        capas.append(alt.Chart(r).mark_rule(color=REFERENCIA, strokeDash=[3, 3]).encode(x='mes:Q'))
        capas.append(alt.Chart(r).mark_text(align='left', dx=4, y=6, baseline='top', fontSize=11, color=TEXTO).encode(
            x='mes:Q', text='texto:N'))
    return alt.layer(*capas).properties(height=340)
