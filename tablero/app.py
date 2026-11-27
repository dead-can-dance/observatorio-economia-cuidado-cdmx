"""Observatorio de la Economía del Cuidado, versión Streamlit.

    streamlit run tablero/app.py        (o: python iniciar.py --streamlit)

Es la misma historia que la página web (frontend/), de lo general a lo particular:
México, Ciudad de México, alcaldías y AGEB, más la metodología. La página «Decisión» agrega
la capa analítica del trabajo integrador: pronóstico, modelo y escenarios del programa. Lee solo el esquema
`indicadores`, a través del backend del observatorio (ver tablero/datos.py).
"""

import streamlit as st

import componentes
import datos
import estilo

st.set_page_config(page_title='Observatorio de la Economía del Cuidado',
                   page_icon=':material/volunteer_activism:', layout='wide')
estilo.inyectar_css()

repo = datos.repositorio()
# Selecciones que sobreviven al cambiar de página (los widgets se reinician al salir).
st.session_state.setdefault('ficha', datos.alcaldia_por_omision())
st.session_state.setdefault('mapa', None)

paginas = [
    st.Page('paginas/inicio.py', title='Inicio', icon=':material/home:', default=True),
    st.Page('paginas/mexico.py', title='México', icon=':material/public:', url_path='mexico'),
    st.Page('paginas/cdmx.py', title='Ciudad de México', icon=':material/location_city:', url_path='cdmx'),
    st.Page('paginas/alcaldias.py', title='Alcaldías', icon=':material/grid_view:', url_path='alcaldias'),
    st.Page('paginas/territorio.py', title='Territorio', icon=':material/map:', url_path='territorio'),
    st.Page('paginas/decision.py', title='Decisión', icon=':material/insights:', url_path='decision'),
    st.Page('paginas/metodologia.py', title='Metodología', icon=':material/menu_book:', url_path='metodologia'),
]
pagina = st.navigation(paginas, position='top')

if not repo.controles_ok:
    fallan = [c['etiqueta'] for c in repo.controles if not c['ok']]
    st.error(f'Hay cifras de control que no cuadran ({len(fallan)}): {", ".join(fallan)}. '
             'Revisa la página de Metodología antes de citar cifras.', icon=':material/error:')

pagina.run()
componentes.pie()
