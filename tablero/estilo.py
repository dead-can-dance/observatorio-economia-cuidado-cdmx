"""Colores y estilos de la app: la paleta Jacaranda de frontend/css/tokens.css.

Streamlit no siempre sabe, al abrir la app, si quien la visita usa tema claro u oscuro.
Por eso las gráficas usan colores de datos que funcionan en los dos, validados con
validate_palette.py (guía de visualización) contra #f9f9f7, #0d0d0d y #1a1a19:

  - acento #6f5bf0 frente al gris de referencia #898781: ΔE 22.8 en visión normal y
    21.9 o más con protanopía y deuteranopía; contraste del acento 4.5:1 en claro y
    3.7:1 o más en oscuro;
  - trabajo pagado #898781, doméstico #a8a8fe y cuidado #5644c0: ΔE de 19 o más entre
    vecinos con y sin daltonismo. Doméstico (en claro) y cuidado (en oscuro) quedan bajo
    3:1 de contraste, así que esa gráfica siempre lleva etiquetas y tabla.

El texto de las gráficas usa `currentColor`: toma el color de texto del tema activo.
"""

import streamlit as st

ACENTO = '#6f5bf0'       # mujeres, cifra principal, alcaldía elegida
REFERENCIA = '#898781'   # hombres (referencia) y contexto nacional
MERCADO = '#898781'      # trabajo pagado
DOMESTICO = '#a8a8fe'    # trabajo doméstico no remunerado
CUIDADO = '#5644c0'      # cuidado no remunerado
CRITICO = '#d03b3b'      # alta carga sin respaldo (estado; siempre con ícono y etiqueta)
AVISO = '#fab219'        # dato exploratorio (estado)
SIN_DATO = '#c3c2b7'     # "No aplica"
TEXTO = 'currentColor'
TINTA = '#0b0b0b'
BLANCO = '#ffffff'

VIOLETA = {100: '#dbdcfe', 150: '#c9cbfe', 200: '#b9bafe', 250: '#a8a8fe', 300: '#9895fd',
           350: '#8a82fd', 400: '#7c6cfd', 450: '#6f5bf0', 500: '#6250d6', 550: '#5644c0',
           600: '#4a3aa8', 650: '#3e2e92', 700: '#322679'}
# Magnitud (mosaico y mapa): un solo tono, de claro a oscuro.
SECUENCIAL = [VIOLETA[p] for p in (150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700)]


def _luminancia(hexa):
    canales = [int(hexa[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in canales]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contraste(a, b):
    x, y = sorted((_luminancia(a), _luminancia(b)), reverse=True)
    return (x + 0.05) / (y + 0.05)


def texto_sobre(fondo):
    """Blanco o tinta, lo que tenga más contraste sobre un relleno."""
    return BLANCO if contraste(fondo, BLANCO) >= contraste(fondo, TINTA) else TINTA


def color_secuencial(valor, minimo, maximo, escala=SECUENCIAL):
    if valor is None or valor != valor:  # None o NaN
        return None
    t = (valor - minimo) / (maximo - minimo) if maximo > minimo else 0.5
    return escala[round(min(1, max(0, t)) * (len(escala) - 1))]


def rgb(hexa, alfa=255):
    return [int(hexa[i:i + 2], 16) for i in (1, 3, 5)] + [alfa]


# Bordes y fondos translúcidos: se ven bien sobre el fondo claro y sobre el oscuro.
CSS = f"""
<style>
.block-container {{ max-width: 1240px; padding-top: 5rem; }}
.obs-escalon {{ min-height: 236px; }}
.obs-escala {{ display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin: 0 0 -6px;
  font-size: .9rem; opacity: .8; }}
.obs-insignia {{ display: inline-flex; align-items: center; gap: 5px; font-size: .74rem; line-height: 1.5;
  padding: 0 8px; border-radius: 999px; border: 1px solid rgba(128,128,128,.45); white-space: nowrap; }}
.obs-insignia::before {{ content: ""; width: 6px; height: 6px; border-radius: 50%; background: currentColor; opacity: .55; }}
.obs-insignia--nacional {{ border-color: rgba(111,91,240,.55); background: rgba(111,91,240,.10); }}
.obs-insignia--exploratorio {{ border-color: rgba(250,178,25,.8); background: rgba(250,178,25,.14); }}
.obs-insignia--exploratorio::before {{ background: {AVISO}; opacity: 1; }}
.obs-nota {{ display: flex; flex-wrap: wrap; align-items: center; gap: 6px 12px; font-size: .8rem; opacity: .78;
  margin-top: 6px; }}
.obs-tarjeta {{ border: 1px solid rgba(128,128,128,.28); border-radius: 12px; padding: 16px 18px; height: 100%;
  display: flex; flex-direction: column; gap: 6px; }}
.obs-tarjeta--destacada {{ border-color: rgba(111,91,240,.6); background: rgba(111,91,240,.06); }}
.obs-tile-etiqueta {{ font-size: .88rem; opacity: .8; margin: 0; }}
.obs-tile-valor {{ font-size: 2rem; font-weight: 700; line-height: 1.1; margin: 2px 0;
  font-variant-numeric: tabular-nums; }}
.obs-tile-contexto {{ font-size: .82rem; opacity: .72; margin: 0; }}
.obs-tile-pie {{ margin-top: auto; padding-top: 6px; display: flex; flex-wrap: wrap; gap: 6px; align-items: center;
  font-size: .76rem; opacity: .8; }}
.obs-rejilla {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(290px, 1fr)); gap: 14px; }}
.obs-hallazgo h4 {{ margin: 0; font-size: 1.02rem; line-height: 1.3; padding: 0; }}
.obs-hallazgo p {{ margin: 0; font-size: .93rem; line-height: 1.5; }}
.obs-hallazgo .obs-advertencia {{ font-size: .82rem; opacity: .8; border-top: 1px dashed rgba(128,128,128,.4);
  padding-top: 6px; }}
.obs-heroe {{ border: 1px solid rgba(111,91,240,.5); border-radius: 16px; padding: 22px 24px;
  background: rgba(111,91,240,.07); }}
.obs-heroe .obs-cifra {{ font-size: 4.6rem; font-weight: 800; line-height: 1; letter-spacing: -.02em;
  font-variant-numeric: tabular-nums; margin: 8px 0; }}
.obs-heroe .obs-cifra span {{ font-size: 2rem; font-weight: 600; opacity: .7; margin-left: 4px; }}
.obs-apoyo {{ border-radius: 10px; padding: 10px 12px; background: rgba(128,128,128,.12); font-size: .9rem; }}
.obs-pregunta {{ border-left: 3px solid {ACENTO}; padding: 4px 0 4px 14px; margin-top: 10px; }}
.obs-pregunta b {{ display: block; font-size: .8rem; opacity: .75; }}
.obs-leyenda {{ display: flex; flex-wrap: wrap; gap: 6px 18px; font-size: .85rem; margin: 2px 0 6px; }}
.obs-leyenda span {{ display: inline-flex; align-items: center; gap: 7px; }}
.obs-muestra {{ width: 12px; height: 12px; border-radius: 3px; display: inline-block; flex: none; }}
.obs-muestra--punto {{ border-radius: 50%; }}
.obs-muestra--anillo {{ border-radius: 50%; border: 2.5px solid {CRITICO}; background: transparent; width: 14px; height: 14px; }}
.obs-muestra--hueco {{ border-radius: 50%; border: 1.5px solid {REFERENCIA}; background: transparent; }}
.obs-gradiente {{ width: 44px; height: 10px; border-radius: 3px; display: inline-block; }}
.obs-medidor {{ display: grid; gap: 4px; margin: 10px 0; }}
.obs-medidor div {{ display: flex; justify-content: space-between; gap: 12px; font-size: .9rem; }}
.obs-medidor .obs-pista {{ height: 10px; border-radius: 99px; background: rgba(128,128,128,.18); overflow: hidden; display: block; }}
.obs-medidor .obs-pista i {{ display: block; height: 100%; border-radius: 99px; background: {ACENTO}; }}
.obs-embudo {{ display: grid; gap: 12px; }}
.obs-embudo div {{ display: grid; gap: 3px; }}
.obs-embudo .obs-fila {{ display: flex; justify-content: space-between; gap: 10px; font-size: .9rem; }}
.obs-embudo .obs-barra {{ height: 12px; border-radius: 0 4px 4px 0; }}
.obs-embudo small {{ opacity: .72; font-size: .8rem; }}
.obs-no-si {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 4px; }}
.obs-no-si div {{ border-radius: 8px; padding: 8px 10px; font-size: .84rem; }}
.obs-no-si b {{ display: block; font-size: .76rem; margin-bottom: 2px; }}
.obs-no {{ background: rgba(208,59,59,.10); }}
.obs-si {{ background: rgba(0,140,70,.10); }}
.obs-ficha-cifras {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; }}
.obs-ficha-cifras div {{ border-radius: 10px; padding: 10px 12px; background: rgba(128,128,128,.09);
  display: grid; gap: 2px; }}
.obs-ficha-cifras span {{ font-size: .82rem; opacity: .8; }}
.obs-ficha-cifras strong {{ font-size: 1.5rem; font-variant-numeric: tabular-nums; }}
.obs-ficha-cifras small {{ font-size: .78rem; opacity: .72; }}
.obs-pie {{ margin-top: 48px; padding-top: 14px; border-top: 1px solid rgba(128,128,128,.28);
  font-size: .8rem; opacity: .75; }}
@media (max-width: 640px) {{
  .obs-heroe .obs-cifra {{ font-size: 3.4rem; }}
  .obs-no-si {{ grid-template-columns: 1fr; }}
}}
</style>
"""


def inyectar_css():
    st.html(CSS)
