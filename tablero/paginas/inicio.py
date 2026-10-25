"""Portada: la pregunta rectora, la cifra con la que el equipo acordó encabezar (la brecha
de trabajo no pagado, con la jornada total como apoyo) y la escalera de lo general a lo
particular que ordena las demás páginas."""

import streamlit as st

import datos as d
from componentes import esc, f_ent, f_horas, f_num, f_pct, insignias

brecha = d.kpi(d.KPI_BRECHA)
jornada = d.kpi(d.KPI_JORNADA_MUJERES)

izquierda, derecha = st.columns([1.25, 1], gap='large', vertical_alignment='center')
with izquierda:
    st.html('<p class="obs-escala">Economía del cuidado en México y la Ciudad de México</p>')
    st.title('Cuidar también es trabajo', anchor=False)
    st.markdown('Este observatorio mide dónde y cuánto trabajo de cuidado no remunerado recae sobre las '
                'mujeres: del país a la Ciudad de México, de la ciudad a cada alcaldía y de ahí a cada '
                'AGEB. También mide qué tanto lo alivia la oferta de cuidados que tienen cerca.')
    st.html(f'<div class="obs-pregunta"><b>Pregunta rectora</b>{esc(d.metodologia.PREGUNTA_RECTORA)}</div>')
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

st.space('medium')
st.subheader('De lo general a lo particular', anchor=False)

enut = d.tabla('enut_carga_actividad')
nac = enut[(enut['ambito'] == 'Nacional') & (enut['sexo'] == 'Mujeres') & (enut['actividad'] == d.TOTAL_CUIDADO)]
alc = d.tabla('resumen_alcaldia').sort_values('carga_directa_x100_mujeres', ascending=False).iloc[0]
sin = d.territorio(None)['embudo'][-1]
escalones = [
    ('México', f_pct(nac['pct_realiza'].iloc[0] if len(nac) else None),
     'de las mujeres de 12 años y más del país cuida a integrantes de su hogar.',
     'Nacional', 'ENUT 2024', False, 'paginas/mexico.py'),
    ('Ciudad de México', f_pct(d.kpi(d.KPI_PCT_CUIDAN)),
     f'de las mujeres de la ciudad cuida; las que cuidan le dedican {f_horas(d.kpi(d.KPI_HORAS_CUIDAN))} a la semana.',
     'CDMX', 'ENUT 2024', False, 'paginas/cdmx.py'),
    ('Alcaldías', f_num(alc['carga_directa_x100_mujeres']),
     f'personas que necesitan cuidado directo por cada 100 mujeres de 15 a 59 en {alc["alcaldia"]}, '
     f'la carga más alta (ciudad: {f_num(d.kpi(d.KPI_CARGA_CDMX))}).',
     'Alcaldía', 'Censo 2020', False, 'paginas/alcaldias.py'),
    ('AGEB', f_ent(sin['mujeres_15a59']),
     f'mujeres de 15 a 59 viven en {f_ent(sin["agebs"])} AGEB de alta carga sin guardería, residencia ni '
     f'centro de día a 1 km.', 'AGEB', 'Censo 2020 + DENUE', True, 'paginas/territorio.py'),
]
for col, (escala, valor, texto, nivel, fuente, exploratorio, destino) in zip(st.columns(4), escalones):
    with col:
        st.html(f'''<div class="obs-tarjeta obs-escalon"><p class="obs-tile-etiqueta">{esc(escala)}</p>
          <p class="obs-tile-valor">{esc(valor)}</p><p class="obs-tile-contexto">{esc(texto)}</p>
          <div class="obs-tile-pie">{insignias(nivel, exploratorio)}<span>{esc(fuente)}</span></div></div>''')
        st.page_link(destino, label=f'Ir a {escala}', icon=':material/arrow_forward:')
