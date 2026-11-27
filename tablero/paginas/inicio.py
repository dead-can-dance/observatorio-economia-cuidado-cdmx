"""Portada: una introducción ejecutiva al observatorio, en cinco pasos.

1. Héroe: la idea con la que el equipo acordó encabezar (cuidar también es trabajo), la
   pregunta rectora y la brecha de trabajo no pagado, con la jornada total como apoyo.
2. El panorama en datos: tres preguntas y tres gráficas que ya usan las páginas del tablero.
3. Lo que los datos permiten observar: tres hallazgos tal como los redacta el backend.
4. ¿Por qué una plataforma digital?: la visión del proyecto y las iniciativas que reúne.
5. Explorar el observatorio: un índice de las páginas, con su pregunta y su cifra.

Toda cifra se lee de los datos, igual que en su página. El programa de la página Decisión
es un escenario simulado, y se dice así en cada lugar donde aparece.
"""

import pandas as pd
import streamlit as st

import datos as d
import graficas as g
from componentes import (ESTADOS, embudo, esc, f_ent, f_horas, f_num, f_pct, insignias, leyenda, medidores,
                         nota_fuente, tarjeta, vacio, ver_tabla)
from estilo import CRITICO, CUIDADO, DOMESTICO, MERCADO, VIOLETA

CUIDARED = 'https://karenitzelsanchez41-rgb.github.io/cuidared/'
FLECHA = ':material/arrow_forward:'
# Las mismas fechas de pronóstico y anotaciones que la página Decisión.
FECHA_PERIODO = {'2026-S2': '2026-11-01', '2027-S1': '2027-05-01', '2027-S2': '2027-11-01'}
EVENTOS = [(pd.Timestamp('2019-02-01'), 'Fin de Estancias Infantiles\ny Censos Económicos 2019'),
           (pd.Timestamp('2024-08-01'), 'Censos Económicos\n2024')]
# Hallazgos que la portada adelanta, en este orden: (nivel del backend, título del hallazgo).
HALLAZGOS = [('cdmx', 'Tener empleo no libera del cuidado'),
             ('alcaldias', 'La presión sobre las guarderías'),
             ('alcaldias', 'Dónde se concentran las zonas sin respaldo')]


def millones(v):
    """Pesos en millones, con el mismo formato que la página Decisión: $1.08 M o −$0.49 M."""
    return '—' if vacio(v) else f'{"−" if v < 0 else ""}${abs(v) / 1e6:,.2f} M'


def seccion(numero, etiqueta, titulo=None, texto=None):
    """Antetítulo corto con número (01 · Panorama) y, si se da, el título de la sección."""
    st.html(f'<p class="obs-portada-seccion"><b>{esc(numero)}</b>{esc(etiqueta)}</p>')
    if titulo:
        st.subheader(titulo, anchor=False)
    if texto:
        st.markdown(texto)


def hallazgo(nivel, titulo):
    return next((h for h in d.hallazgos(nivel) if h['titulo'] == titulo), None)


m = d.metodologia
repo = d.repositorio()
r = d.resumen_decision()
brecha = d.kpi(d.KPI_BRECHA)
jornada = d.kpi(d.KPI_JORNADA_MUJERES)

# --- 1. Héroe ---------------------------------------------------------------------------------
izquierda, derecha = st.columns([1.25, 1], gap='large', vertical_alignment='center')
with izquierda:
    st.html('<p class="obs-escala">Observatorio de la Economía del Cuidado · Ciudad de México</p>')
    st.title('Cuidar también es trabajo', anchor=False)
    st.html('<p class="obs-portada-entrada">Cocinar, limpiar, criar y acompañar a quien no puede valerse por sí '
            'mismo sostiene a cada hogar, aunque no aparezca en ningún recibo de pago. Este observatorio usa datos '
            'del INEGI para medir cuánto de ese trabajo recae sobre las mujeres, dónde falta oferta de cuidado '
            'cerca de ellas y qué haría falta para invertir en una red de cuidado.</p>')
    st.html(f'<div class="obs-pregunta"><b>Pregunta rectora</b>{esc(m.PREGUNTA_RECTORA)}</div>')
    with st.container(horizontal=True, gap='medium'):
        st.page_link('paginas/cdmx.py', label='Empieza por la Ciudad de México', icon=FLECHA)
        st.page_link('paginas/decision.py', label='Del dato a la decisión', icon=FLECHA)
with derecha:
    st.html(f'''<aside class="obs-heroe" aria-label="Cifra principal del observatorio">
      <p style="margin:0">Las mujeres ocupadas de la Ciudad de México hacen</p>
      <p class="obs-cifra">+{esc(f_num(brecha))}<span>h</span></p>
      <p style="margin:0 0 12px">más de trabajo no pagado <strong>cada semana</strong> que los hombres ocupados
        (referencia): trabajo doméstico y cuidado de su propio hogar.</p>
      <p class="obs-apoyo" style="margin:0">Sumando el trabajo pagado, su jornada total llega a
        <strong>{esc(f_num(jornada))} horas</strong> a la semana.</p>
      <div class="obs-nota"><span>Fuente: INEGI, ENUT 2024</span><span>Nivel: {insignias("CDMX")}</span></div>
    </aside>''')

# --- 2. El panorama en datos ------------------------------------------------------------------
st.space('large')
seccion('01', 'Panorama', 'El panorama en datos',
        'Tres preguntas para entender el tema: cuánto se trabaja sin pago, dónde falta respaldo y si la oferta '
        'formal de cuidado está creciendo.')

dj = d.tabla('enut_doble_jornada').set_index('grupo')
componentes = [('Trabajo para el mercado (pagado)', 'horas_trabajo_mercado', MERCADO),
               ('Trabajo doméstico no remunerado', 'horas_trabajo_domestico', DOMESTICO),
               ('Cuidado no remunerado', 'horas_cuidado', CUIDADO)]
cortas = {'Mujeres ocupadas': 'Mujeres', 'Hombres ocupados (ref.)': 'Hombres (ref.)'}
filas = [{'categoria': cortas.get(grupo, grupo), 'componente': n, 'valor': fila[col], 'texto': f_horas(fila[col])}
         for grupo, fila in dj.iterrows() for n, col, _ in componentes]
totales = {cortas.get(grupo, grupo): f_horas(fila.horas_jornada_total) for grupo, fila in dj.iterrows()}

izq, der = st.columns([1.15, 1], gap='medium')
with izq, tarjeta('¿Cuánto trabaja a la semana una persona ocupada en la CDMX?',
                  'Horas de trabajo pagado, doméstico y de cuidado de las mujeres ocupadas, frente a los hombres '
                  'ocupados (referencia). La parte sin pago es la que separa a unas de otros.'):
    leyenda([(n, color, 'cuadro') for n, _, color in componentes])
    st.altair_chart(g.barra_apilada(pd.DataFrame(filas), orden=list(totales), totales=totales,
                                    componentes=[(n, color) for n, _, color in componentes]), width='stretch')
    ver_tabla(pd.DataFrame({
        'Componente': [n for n, _, _ in componentes] + ['Jornada total'],
        **{grupo: [f_horas(fila[col]) for _, col, _ in componentes] + [f_horas(fila.horas_jornada_total)]
           for grupo, fila in dj.iterrows()}}))
    nota_fuente('INEGI, ENUT 2024', 'CDMX')
    st.page_link('paginas/cdmx.py', label='Ver la doble jornada completa', icon=FLECHA)

terr = d.territorio(None)
with der, tarjeta('¿Cuántas mujeres viven en zonas de alta carga sin servicios cerca?',
                  'AGEB urbanas de la ciudad. Cada etapa es un subconjunto de la anterior; el respaldo es una '
                  'guardería, residencia o centro de día a menos de 1 km.'):
    embudo(terr['embudo'], [VIOLETA[300], VIOLETA[450], VIOLETA[600], CRITICO])
    st.caption('Hallazgo exploratorio: la ubicación de cada AGEB es aproximada y el resultado depende del radio.')
    nota_fuente('INEGI, Censo 2020 + DENUE 05/2026', 'AGEB', exploratorio=True)
    st.page_link('paginas/territorio.py', label='Ver el mapa de las zonas sin respaldo', icon=FLECHA)

hist = d.tabla('oferta_historica')
h = (hist.groupby(['edicion', 'periodo'], as_index=False)['establecimientos'].sum()
     .rename(columns={'establecimientos': 'valor'}))
h['fecha'] = pd.to_datetime(h['edicion'] + '-01')
h['texto'] = h['valor'].map(f_ent)
pron = d.tabla('pronostico_oferta')
p = pron[(pron['serie'] == 'Total de respaldo') & pron['elegido']].copy()
p['fecha'] = pd.to_datetime(p['periodo'].map(FECHA_PERIODO))
with tarjeta(f'¿La oferta formal de cuidado está creciendo? Pasó de {f_ent(r["oferta_2016"])} establecimientos '
             f'en 2016 a {f_ent(r["oferta_hoy"])} en 2026',
             'Guarderías, residencias y centros de día de la CDMX en cada edición del DENUE. La línea discontinua y '
             'las bandas son el pronóstico a 2027 (intervalos de 80 % y 95 %): no anticipa una recuperación.'):
    st.altair_chart(g.serie_y_pronostico(h, p, eventos=EVENTOS), width='stretch')
    ver_tabla(h[['periodo', 'texto']].rename(columns={'periodo': 'Semestre', 'texto': 'Establecimientos'}))
    nota_fuente('INEGI, DENUE (19 ediciones, 01/2016 a 05/2026)', 'CDMX')
    st.page_link('paginas/decision.py', label='Ver el pronóstico y el modelo', icon=FLECHA)

# --- 3. Lo que los datos permiten observar ----------------------------------------------------
st.space('large')
seccion('02', 'Hallazgos', 'Lo que los datos permiten observar',
        'Tres hallazgos del observatorio, cada uno con su fuente y su nivel geográfico.')
def articulo(i, x):
    advertencia = (f'<p style="font-size:.84rem;opacity:.8">{esc(x["advertencia"])}</p>'
                   if x.get('advertencia') else '')
    return (f'<article class="obs-portada-hallazgo"><span class="obs-portada-num" aria-hidden="true">{i:02d}</span>'
            f'<h4>{esc(x["titulo"])}</h4><p>{esc(x["texto"])}</p>{advertencia}'
            f'<div class="obs-tile-pie">{insignias(x["nivel_geografico"], x["exploratorio"])}'
            f'<span>{esc(x["fuente"])}</span></div></article>')


elegidos = [x for x in (hallazgo(nivel, titulo) for nivel, titulo in HALLAZGOS) if x]
articulos = ''.join(articulo(i, x) for i, x in enumerate(elegidos, start=1))
st.html(f'<div class="obs-portada-hallazgos">{articulos}</div>')

# --- 4. ¿Por qué una plataforma digital? -------------------------------------------------------
st.space('large')
seccion('03', 'Visión')
izq, der = st.columns([1.35, 1], gap='large')
with izq:
    st.html('''<section class="obs-portada-vision" aria-labelledby="obs-vision">
      <h3 id="obs-vision">¿Por qué una plataforma digital?</h3>
      <p>Los datos del cuidado existen, pero están repartidos en encuestas, censos y directorios difíciles de
        consultar. Una plataforma digital permite verlos, explorarlos y compararlos, del país a cada AGEB, con su
        fuente y sus límites a la vista.</p>
      <p>También permite acercar el análisis a necesidades reales y reunir, en un mismo lugar, iniciativas que se
        complementan: medir el problema, evaluar una respuesta y proponer una herramienta para atenderlo.</p>
    </section>''')
with der, tarjeta('Lo que dicen las cuidadoras del país',
                  'Mujeres cuidadoras de 15 años y más. La ENASIC es nacional: no permite cifras de la CDMX.'):
    medidores([('Preferiría que el servicio de cuidado fuera en su casa', d.kpi('ENASIC · % cuidadoras que prefiere cuidado en casa')),
               ('Sería cuidadora profesional si le pagaran', d.kpi('ENASIC · % cuidadoras que sería cuidadora pagada')),
               ('Buscó una guardería, casa de día o asilo', d.kpi('ENASIC · % cuidadoras que buscó un servicio'))])
    st.caption('El cuidado sucede sobre todo en casa y casi nadie busca servicios: eso invita a pensar en '
               'soluciones cercanas a los hogares.')
    nota_fuente('INEGI, ENASIC 2022', 'Nacional')

st.space('small')
iniciativas = [
    ('Observatorio de datos', 'Mide dónde y cuánto trabajo de cuidado recae sobre las mujeres y qué oferta tienen '
     'cerca.'),
    ('Del dato a la decisión', 'Evalúa, como escenario simulado, una red de cuidado a domicilio en Iztapalapa.'),
    ('CuidaRed', 'Una aplicación del equipo para conectar necesidades de cuidado con personas que pueden ofrecer '
     'apoyo. Tiene su propio espacio en la exposición.'),
]
for col, (nombre, texto) in zip(st.columns(3, gap='large'), iniciativas):
    with col:
        st.html(f'<ul class="obs-portada-iniciativas"><li><b>{esc(nombre)}</b>{esc(texto)}</li></ul>')
        if nombre == 'CuidaRed':
            st.link_button('Conoce el prototipo de CuidaRed', CUIDARED, icon=':material/open_in_new:',
                           type='tertiary')

# --- 5. Explorar el observatorio --------------------------------------------------------------
st.space('large')
seccion('04', 'Explorar', 'Explorar el observatorio', 'De lo general a lo particular, y del dato a la decisión.')

enut = d.tabla('enut_carga_actividad')
nac = enut[(enut['ambito'] == 'Nacional') & (enut['sexo'] == 'Mujeres') & (enut['actividad'] == d.TOTAL_CUIDADO)]
alc = d.tabla('resumen_alcaldia').sort_values('carga_directa_x100_mujeres', ascending=False).iloc[0]
sin = terr['embudo'][-1]
cuadran, controles = sum(x['ok'] for x in repo.controles), len(repo.controles)
simulado = '<span class="obs-insignia obs-insignia--exploratorio">Simulado</span>'
# (escala, pregunta, cifra, texto de la cifra, insignias, fuente, página)
destinos = [
    ('México', '¿Cuánto cuidan las mujeres del país?', f_pct(nac['pct_realiza'].iloc[0] if len(nac) else None),
     'de las mujeres de 12 años y más cuida a integrantes de su hogar.', insignias('Nacional'), 'ENUT 2024',
     'paginas/mexico.py'),
    ('Ciudad de México', '¿Cómo es la doble jornada en la capital?', f_pct(d.kpi(d.KPI_PCT_CUIDAN)),
     f'de las mujeres cuida, {f_horas(d.kpi(d.KPI_HORAS_CUIDAN))} a la semana las que lo hacen.', insignias('CDMX'),
     'ENUT 2024', 'paginas/cdmx.py'),
    ('Alcaldías', '¿En qué alcaldías pesa más el cuidado?', f_num(alc['carga_directa_x100_mujeres']),
     f'personas que necesitan cuidado por cada 100 mujeres de 15 a 59 en {alc["alcaldia"]}.', insignias('Alcaldía'),
     'Censo 2020', 'paginas/alcaldias.py'),
    ('Territorio', '¿Qué zonas no tienen servicios de cuidado cerca?', f_ent(sin['mujeres_15a59']),
     f'mujeres de 15 a 59 viven en {f_ent(sin["agebs"])} AGEB de alta carga sin respaldo a 1 km.',
     insignias('AGEB', exploratorio=True), 'Censo 2020 + DENUE', 'paginas/territorio.py'),
    ('Decisión', '¿Conviene una red de cuidado a domicilio en Iztapalapa?', millones(r['van_esperado_etapas']),
     'de VAN esperado si se invierte por etapas. Escenario simulado.', insignias('AGEB') + simulado,
     'Escenario simulado', 'paginas/decision.py'),
    ('Metodología', '¿Cómo leer (y cómo no leer) estos datos?', f_ent(len(m.ADVERTENCIAS)),
     'advertencias de lectura dicen qué se puede y qué no se puede afirmar con cada cifra.',
     insignias(['Nacional', 'CDMX', 'Alcaldía', 'AGEB']), 'INEGI', 'paginas/metodologia.py'),
]
for bloque in (destinos[:3], destinos[3:]):
    for col, (escala, pregunta, cifra, texto, marcas, fuente, pagina) in zip(st.columns(3, gap='large'), bloque):
        with col:
            st.html(f'''<div class="obs-portada-destino"><p class="obs-portada-etiqueta">{esc(escala)}</p>
              <h4>{esc(pregunta)}</h4>
              <p class="obs-portada-gancho"><strong>{esc(cifra)}</strong> {esc(texto)}</p>
              <div class="obs-tile-pie">{marcas}<span>{esc(fuente)}</span></div></div>''')
            st.page_link(pagina, label=f'Ir a {escala}', icon=FLECHA)

clase, forma, _ = ESTADOS['ok' if repo.controles_ok else 'critico']
st.html(f'''<div class="obs-nota" style="margin-top:18px"><span>Fuentes: INEGI · {esc(" · ".join(f["clave"] for f in m.FUENTES))}.
  Toda cifra se publica con su fuente, su año y su nivel geográfico.</span><span class="obs-estado {clase}">
  <span aria-hidden="true">{forma}</span> {cuadran} de {controles} cifras de control cuadran</span></div>''')
