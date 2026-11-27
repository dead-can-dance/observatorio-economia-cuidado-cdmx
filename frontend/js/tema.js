// Tema claro u oscuro. Los colores viven en css/tokens.css; las gráficas los leen de ahí
// con getComputedStyle, así que cambiar de tema es volver a leer los tokens.

import { ref } from 'vue';

const CLAVE = 'observatorio-tema';
const raiz = document.documentElement;
const consultaOscuro = window.matchMedia('(prefers-color-scheme: dark)');
const PASOS = [100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700];

function temaActual() {
  const marcado = raiz.dataset.theme;
  if (marcado === 'light' || marcado === 'dark') return marcado;
  return consultaOscuro.matches ? 'dark' : 'light';
}

export function leerTokens() {
  const estilos = getComputedStyle(raiz);
  const v = (nombre) => estilos.getPropertyValue(nombre).trim();
  const violeta = Object.fromEntries(PASOS.map((p) => [p, v(`--violeta-${p}`)]));
  const oscuro = temaActual() === 'dark';
  return {
    oscuro,
    pagina: v('--pagina'),
    superficie: v('--superficie'),
    hundida: v('--superficie-hundida'),
    tinta1: v('--tinta-1'),
    tinta2: v('--tinta-2'),
    tinta3: v('--tinta-3'),
    reticula: v('--reticula'),
    eje: v('--eje'),
    borde: v('--borde-fuerte'),
    acento: v('--acento'),
    referencia: v('--referencia'),
    critico: v('--critico'),
    mercado: v('--g-mercado'),
    domestico: v('--g-domestico'),
    cuidado: v('--g-cuidado'),
    sombraEje: v('--g-sombra-eje'),
    // Tono de énfasis inverso: el resto de las barras cuando una está seleccionada.
    atenuado: violeta[oscuro ? 600 : 200],
    ordinal: [1, 2, 3, 4, 5].map((i) => v(`--g-ordinal-${i}`)),
    embudo: [1, 2, 3, 4].map((i) => v(`--g-embudo-${i}`)),
    // Secuencial: de menos a más. En oscuro el ancla se invierte (lo bajo se hunde
    // hacia la superficie oscura y lo alto se ilumina).
    secuencial: oscuro
      ? [650, 600, 550, 500, 450, 400, 350, 300, 250, 200, 150].map((p) => violeta[p])
      : [150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700].map((p) => violeta[p]),
    violeta,
    fuente: getComputedStyle(document.body).fontFamily,
  };
}

export const tema = ref(temaActual());
export const tokens = ref(leerTokens());

function refrescar() {
  tema.value = temaActual();
  tokens.value = leerTokens();
}

export function alternarTema() {
  const nuevo = temaActual() === 'dark' ? 'light' : 'dark';
  raiz.dataset.theme = nuevo;
  try { localStorage.setItem(CLAVE, nuevo); } catch { /* sin almacenamiento: dura la sesión */ }
  refrescar();
}

consultaOscuro.addEventListener('change', () => {
  if (!raiz.dataset.theme) refrescar();
});

/** Color de la escala secuencial para un valor entre min y max. */
export function colorSecuencial(valor, min, max, escala = tokens.value.secuencial) {
  if (valor === null || valor === undefined || Number.isNaN(valor)) return null;
  const t = max > min ? (valor - min) / (max - min) : 0.5;
  const i = Math.round(Math.min(1, Math.max(0, t)) * (escala.length - 1));
  return escala[i];
}
