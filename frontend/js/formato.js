// Formato de cifras para México: 1,234.5 · 62.2 % · 12.7 h. El espacio antes de % y de h
// es duro (U+00A0) para que la unidad nunca quede sola en otra línea.

const NBSP = ' ';
const formateadores = new Map();

function formateador(decimales) {
  if (!formateadores.has(decimales)) {
    formateadores.set(decimales, new Intl.NumberFormat('es-MX', {
      minimumFractionDigits: decimales,
      maximumFractionDigits: decimales,
    }));
  }
  return formateadores.get(decimales);
}

export const vacio = (v) => v === null || v === undefined || Number.isNaN(v);

export const num = (v, decimales = 1) => (vacio(v) ? '—' : formateador(decimales).format(v));
export const ent = (v) => num(v, 0);
export const pct = (v, decimales = 1) => (vacio(v) ? '—' : `${num(v, decimales)}${NBSP}%`);
export const horas = (v) => (vacio(v) ? '—' : `${num(v, 1)}${NBSP}h`);
export const veces = (v) => (vacio(v) ? '—' : `${num(v, 2)}×`);

// Marcas de los ejes: sin decimales (las etiquetas de las barras y la tabla llevan el dato exacto).
export const ejePct = (v) => pct(v, 0);
export const ejeHoras = (v) => `${num(v, 0)}${NBSP}h`;
export const ejeNum = (v) => num(v, 0);
export const ejeIndicador = (v, indicador) => (indicador.unidad.startsWith('%') ? pct(v, 0) : num(v, 0));

/** Formatea según los decimales que declara el indicador en la API. */
export function segunIndicador(valor, indicador) {
  if (vacio(valor)) return 'No aplica';
  const texto = num(valor, indicador.decimales ?? 1);
  return indicador.unidad.startsWith('%') ? `${texto}${NBSP}%` : texto;
}

/** Las etiquetas de categoría vienen de datos: se escapan antes de entrar a HTML. */
export function escapar(texto) {
  return String(texto ?? '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

// --- Contraste WCAG, para decidir si un texto sobre un relleno va en blanco o en tinta.
function luminancia(hex) {
  const h = hex.replace('#', '');
  const canal = (i) => {
    const c = parseInt(h.slice(i, i + 2), 16) / 255;
    return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * canal(0) + 0.7152 * canal(2) + 0.0722 * canal(4);
}

export function contraste(a, b) {
  const [x, y] = [luminancia(a), luminancia(b)].sort((p, q) => q - p);
  return (x + 0.05) / (y + 0.05);
}

export function textoSobre(fondo, claro = '#ffffff', oscuro = '#0b0b0b') {
  return contraste(fondo, claro) >= contraste(fondo, oscuro) ? claro : oscuro;
}

export const formato = { num, ent, pct, horas, veces, segunIndicador };
