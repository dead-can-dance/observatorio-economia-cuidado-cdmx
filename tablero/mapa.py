"""Mapa de AGEB y establecimientos de cuidado con pydeck (viene incluido con Streamlit).

El mapa base es el de CARTO que Streamlit elige según el tema activo (claro u oscuro).
En pydeck, las cadenas se leen como expresiones; los valores literales como 'pixels' van
entre comillas simples dentro de la cadena.
"""

import math

import pydeck as pdk

from componentes import esc, f_ent, f_num, f_pct
from estilo import CRITICO, SECUENCIAL, SIN_DATO, color_secuencial, rgb

CENTRO = (19.37, -99.13)
# La escala recorta el extremo más claro para que ningún punto se pierda en el fondo.
ESCALA = SECUENCIAL[1:]
PIXELES = "'pixels'"


def _vista(puntos):
    if puntos.empty:
        return pdk.ViewState(latitude=CENTRO[0], longitude=CENTRO[1], zoom=9.6)
    lat0, lat1 = puntos['lat'].quantile([0.02, 0.98])
    lon0, lon1 = puntos['lon'].quantile([0.02, 0.98])
    lat, lon = (lat0 + lat1) / 2, (lon0 + lon1) / 2
    extension = max(lat1 - lat0, (lon1 - lon0) * math.cos(math.radians(lat)), 0.01)
    zoom = max(9.4, min(13.2, 9.6 + math.log2(0.32 / extension)))
    return pdk.ViewState(latitude=lat, longitude=lon, zoom=zoom)


def _tooltip_ageb(a):
    if a.sin_respaldo:
        alerta = '<br/><b>⚠ Alta carga y sin ningún servicio de respaldo a 1 km (exploratorio)</b>'
    elif a.alta_carga:
        alerta = '<br/>AGEB de alta carga de cuidado'
    else:
        alerta = ''
    return (f'<b>AGEB {esc(a.cvegeo_ageb)}</b><br/>{esc(a.alcaldia)}<br/>'
            f'Carga de cuidado directo: {esc(f_num(a.carga_directa_x100_mujeres))}<br/>'
            f'Mujeres de 15 a 59: {esc(f_ent(a.mujeres_15a59))}<br/>'
            f'Niñas y niños de 0 a 5: {esc(f_ent(a.pob_0a5))}<br/>'
            f'Guarderías a 1 km: {esc(f_ent(a.guarderias_1km))}<br/>'
            f'Servicios de respaldo a 1 km: {esc(f_ent(a.respaldo_total_1km))}<br/>'
            f'Hogares con jefatura femenina: {esc(f_pct(a.pct_hog_jefa))}{alerta}'
            f'<br/><i>Ubicación aproximada del AGEB</i>')


def _tooltip_estab(e):
    return (f'<b>{esc(e.nom_estab or "Sin nombre registrado")}</b><br/>{esc(e.tipo)} · {esc(e.sector)}<br/>'
            f'Alcaldía: {esc(e.alcaldia)}<br/>Personal ocupado: {esc(e.per_ocu or "—")}<br/>'
            f'Cuenta como respaldo: {"Sí" if e.es_respaldo else "No"}<br/>'
            f'<i>El personal ocupado no es capacidad de atención</i>')


def construir(agebs, establecimientos, *, seleccion=None, capas=()):
    """Deck con las capas pedidas. Fuera de la alcaldía elegida, los puntos se atenúan."""
    a = agebs.dropna(subset=['lat', 'lon']).copy()
    a['sin_respaldo'] = a['sin_respaldo'].fillna(False).astype(bool)
    a['alta_carga'] = a['alta_carga'].fillna(False).astype(bool)
    dentro = a['cve_mun'].eq(seleccion) if seleccion else a['cve_mun'].notna()
    carga = a['carga_directa_x100_mujeres']
    minimo, maximo = carga.min(), carga.max()
    a['relleno'] = [rgb(color_secuencial(v, minimo, maximo, ESCALA) or SIN_DATO, 240 if d else 40)
                    for v, d in zip(carga, dentro)]
    a['borde'] = [[255, 255, 255, 160 if d else 30] for d in dentro]
    a['anillo'] = [rgb(CRITICO, 255 if d else 60) for d in dentro]
    a['tt'] = [_tooltip_ageb(f) for f in a.itertuples()]

    e = establecimientos.dropna(subset=['lat', 'lon']).copy()
    e['es_respaldo'] = e['es_respaldo'].fillna(False).astype(bool)
    dentro_e = e['cve_mun'].eq(seleccion) if seleccion else e['cve_mun'].notna()
    e['alfa'] = [230 if d else 50 for d in dentro_e]
    e['relleno'] = [[62, 61, 58, x] for x in e['alfa']]
    e['borde_resp'] = [[255, 255, 255, x] for x in e['alfa']]
    e['borde_otro'] = [[137, 135, 129, x] for x in e['alfa']]
    e['tt'] = [_tooltip_estab(f) for f in e.itertuples()]

    comunes = dict(get_position='[lon, lat]', pickable=True, radius_units=PIXELES,
                   line_width_units=PIXELES)
    capas_deck = []
    if 'carga' in capas:
        capas_deck.append(pdk.Layer(
            'ScatterplotLayer', id='agebs', data=a[['lon', 'lat', 'relleno', 'borde', 'tt']],
            get_fill_color='relleno', get_line_color='borde', stroked=True, get_line_width=1,
            get_radius=5, **comunes))
    if 'sin_respaldo' in capas:
        capas_deck.append(pdk.Layer(
            'ScatterplotLayer', id='sin_respaldo', data=a.loc[a['sin_respaldo'], ['lon', 'lat', 'anillo', 'tt']],
            filled=False, stroked=True, get_line_color='anillo', get_line_width=2.5, get_radius=9, **comunes))
    if 'otros' in capas:
        capas_deck.append(pdk.Layer(
            'ScatterplotLayer', id='otros', data=e.loc[~e['es_respaldo'], ['lon', 'lat', 'borde_otro', 'tt']],
            filled=False, stroked=True, get_line_color='borde_otro', get_line_width=1.3, get_radius=3.5, **comunes))
    if 'respaldo' in capas:
        capas_deck.append(pdk.Layer(
            'ScatterplotLayer', id='respaldo', data=e.loc[e['es_respaldo'], ['lon', 'lat', 'relleno', 'borde_resp', 'tt']],
            get_fill_color='relleno', get_line_color='borde_resp', stroked=True, get_line_width=1,
            get_radius=3.5, **comunes))

    enfoque = a[dentro] if seleccion else a
    return pdk.Deck(
        layers=capas_deck, initial_view_state=_vista(enfoque), map_style=None,
        tooltip={'html': '{tt}', 'style': {'backgroundColor': '#1a1a19', 'color': '#f0efec',
                                           'fontSize': '12.5px', 'maxWidth': '290px', 'lineHeight': '1.45'}})
