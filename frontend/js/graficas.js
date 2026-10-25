// Opciones de ECharts para las gráficas del observatorio.
//
// Reglas de la guía de visualización que se aplican aquí en todas:
//   - Barras delgadas (<= 24 px), extremo de datos redondeado a 4 px y base recta.
//   - Cuadrícula y ejes en línea fina, sólida y recesiva. Nunca dos ejes Y.
//   - El texto usa tintas, nunca el color de la serie. Etiquetas directas selectivas.
//   - Tooltip por marca o por categoría, con el valor primero y el nombre después.
//   - Las etiquetas vienen de datos: se escapan antes de entrar al HTML del tooltip.
// Los colores llegan en `t` (tokens leídos de css/tokens.css).

import { escapar, ent, num, textoSobre } from './formato.js';

const movimientoReducido = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;

function base(t) {
  return {
    animation: !movimientoReducido(),
    animationDuration: 420,
    animationDurationUpdate: 320,
    textStyle: { fontFamily: t.fuente, color: t.tinta2, fontSize: 12 },
    tooltip: {
      confine: true,
      backgroundColor: t.superficie,
      borderColor: t.borde,
      borderWidth: 1,
      padding: [8, 10],
      textStyle: { color: t.tinta1, fontFamily: t.fuente, fontSize: 12 },
      extraCssText: 'border-radius:10px;box-shadow:0 6px 22px rgba(0,0,0,.16);',
    },
  };
}

/** HTML del tooltip: título, filas «valor + nombre» con clave de línea, nota opcional. */
export function tooltipHtml(titulo, filas = [], nota = '') {
  const cuerpo = filas.map((f) => (
    `<div class="tt-fila"><span class="tt-clave" style="background:${f.color}"></span>`
    + `<span class="tt-valor">${escapar(f.valor)}</span><span>${escapar(f.nombre)}</span></div>`
  )).join('');
  const pie = nota ? `<div class="tt-nota">${escapar(nota)}</div>` : '';
  return `<div class="tt"><div class="tt-titulo">${escapar(titulo)}</div>${cuerpo}${pie}</div>`;
}

const ejeValor = (t, formato, extra = {}) => ({
  type: 'value',
  axisLabel: { color: t.tinta3, formatter: (v) => formato(v), hideOverlap: true },
  splitLine: { lineStyle: { color: t.reticula, width: 1, type: 'solid' } },
  axisLine: { show: false },
  axisTick: { show: false },
  ...extra,
});

const ejeCategorias = (t, categorias, etiqueta = {}, extra = {}) => ({
  type: 'category',
  data: categorias,
  axisTick: { show: false },
  axisLine: { lineStyle: { color: t.eje } },
  axisLabel: { color: t.tinta2, fontSize: 12, lineHeight: 15, ...etiqueta },
  ...extra,
});

const sombraEje = (t) => ({ type: 'shadow', shadowStyle: { color: t.sombraEje } });

// Las categorías frágiles llevan * (menos de 100 casos) o † (menos de 60) en el eje; el
// tooltip ya explica la razón en su nota, así que el título va sin la marca.
const sinMarca = (texto) => String(texto).replace(/\s*[*†]$/, '');

/** Dato de una barra; si es frágil (muestra chica) va en el tono atenuado y su etiqueta en
 * tinta secundaria. No se usa opacidad: apagaría también la etiqueta y bajaría su contraste. */
const dato = (t, valor, color, fragil) => ({
  value: valor,
  itemStyle: { color: fragil ? t.atenuado : color },
  label: { color: fragil ? t.tinta2 : t.tinta1 },
});

/**
 * Barras horizontales agrupadas: la serie de interés en acento y la de referencia en gris.
 * series: [{ nombre, valores, color, etiquetar, fragiles? }]
 */
export function barrasComparadas(t, {
  categorias, series, formato, formatoEje = formato, max, anchoEtiqueta = 150, notas = [],
}) {
  return {
    ...base(t),
    grid: { left: 4, right: 54, top: 4, bottom: 4, containLabel: true },
    xAxis: ejeValor(t, formatoEje, { max }),
    yAxis: ejeCategorias(t, categorias, { width: anchoEtiqueta, overflow: 'break' }, { inverse: true }),
    series: series.map((s) => ({
      type: 'bar',
      name: s.nombre,
      data: s.valores.map((v, i) => dato(t, v, s.color, s.fragiles?.[i])),
      barMaxWidth: 12,
      barGap: '40%',
      barCategoryGap: '36%',
      itemStyle: { color: s.color, borderRadius: [0, 4, 4, 0] },
      label: {
        show: Boolean(s.etiquetar), position: 'right', distance: 6,
        color: t.tinta1, fontSize: 12, fontWeight: 600, formatter: (p) => formato(p.value),
      },
      emphasis: { disabled: true },
    })),
    tooltip: {
      ...base(t).tooltip,
      trigger: 'axis',
      axisPointer: sombraEje(t),
      formatter: (ps) => tooltipHtml(
        sinMarca(ps[0].name),
        ps.map((p) => ({ color: p.color, nombre: p.seriesName, valor: formato(p.value) })),
        notas[ps[0].dataIndex],
      ),
    },
  };
}

/** Ancho aproximado de una etiqueta de 12 px en negritas (cifras y unidades cortas). */
const anchoTexto = (texto) => String(texto).length * 6.8;

/**
 * Barra apilada horizontal (la doble jornada). `totales` son los oficiales: la suma de
 * componentes redondeados puede diferir por una décima (45.6 + 23.3 + 8.0 = 76.9 ≠ 77.0).
 * Con `ancho` (px del contenedor) se calcula cuánto mide cada segmento y la etiqueta solo
 * se pinta dentro si cabe con holgura; si no, el valor queda en el tooltip y en la tabla.
 */
export function barraApilada(t, {
  categorias: largas, categoriasCortas, segmentos, totales, formato, formatoEje = formato, ancho = 0,
}) {
  const angosto = ancho > 0 && ancho < 560;
  const categorias = angosto && categoriasCortas ? categoriasCortas : largas;
  const anchoEje = angosto ? 92 : 170;
  const maximo = Math.ceil(Math.max(...totales) / 10) * 10;
  const util = (ancho || 640) - anchoEje - 64 - 16;
  const cabe = (v) => (v / maximo) * util >= anchoTexto(formato(v)) + 12;
  const series = segmentos.map((seg, k) => ({
    type: 'bar',
    stack: 'total',
    name: seg.nombre,
    data: seg.valores,
    barMaxWidth: 24,
    barCategoryGap: '48%',
    itemStyle: {
      color: seg.color,
      borderColor: t.superficie, // separación de 2 px en el color de la superficie
      borderWidth: 2,
      borderRadius: k === segmentos.length - 1 ? [0, 4, 4, 0] : 0,
    },
    label: {
      show: true,
      position: 'inside',
      color: textoSobre(seg.color),
      fontSize: 12,
      fontWeight: 600,
      formatter: (p) => (cabe(p.value) ? formato(p.value) : ''),
    },
    emphasis: { disabled: true },
  }));
  // Serie vacía al final de la pila: solo lleva la etiqueta del total.
  series.push({
    type: 'bar',
    stack: 'total',
    name: '__total',
    data: totales.map(() => 0),
    silent: true,
    label: {
      show: true, position: 'right', distance: 8, color: t.tinta1, fontSize: 13, fontWeight: 700,
      formatter: (p) => formato(totales[p.dataIndex]),
    },
  });
  return {
    ...base(t),
    grid: { left: 4, right: 64, top: 4, bottom: 4, containLabel: true },
    xAxis: ejeValor(t, formatoEje, { max: maximo }),
    yAxis: ejeCategorias(t, categorias, {
      color: t.tinta1, fontSize: 13, fontWeight: 600, width: anchoEje, overflow: 'break',
    }, { inverse: true }),
    series,
    tooltip: {
      ...base(t).tooltip,
      trigger: 'axis',
      axisPointer: sombraEje(t),
      formatter: (ps) => tooltipHtml(
        ps[0].name,
        ps.filter((p) => p.seriesName !== '__total')
          .map((p) => ({ color: p.color, nombre: p.seriesName, valor: formato(p.value) })),
        `Jornada total: ${formato(totales[ps[0].dataIndex])}`,
      ),
    },
  };
}

/**
 * Barras de la serie principal con un punto gris para la referencia (brecha por actividad).
 */
export function barrasConReferencia(t, {
  categorias, valores, referencias, etiquetas, formato, formatoEje = formato, fragiles = [],
  notas = [], nombrePrincipal, nombreReferencia, anchoEtiqueta = 170,
}) {
  return {
    ...base(t),
    grid: { left: 4, right: 110, top: 4, bottom: 4, containLabel: true },
    xAxis: ejeValor(t, formatoEje),
    yAxis: ejeCategorias(t, categorias, { width: anchoEtiqueta, overflow: 'break' }, { inverse: true }),
    series: [
      {
        type: 'bar',
        name: nombrePrincipal,
        data: valores.map((v, i) => dato(t, v, t.acento, fragiles[i])),
        barMaxWidth: 16,
        barCategoryGap: '42%',
        itemStyle: { color: t.acento, borderRadius: [0, 4, 4, 0] },
        label: {
          show: true, position: 'right', distance: 14, color: t.tinta1, fontSize: 12,
          fontWeight: 600, formatter: (p) => etiquetas[p.dataIndex],
        },
        emphasis: { disabled: true },
        z: 2,
      },
      {
        type: 'scatter',
        name: nombreReferencia,
        data: referencias.map((v, i) => [v, i]),
        symbolSize: 10,
        itemStyle: { color: t.referencia, borderColor: t.superficie, borderWidth: 2 },
        emphasis: { disabled: true },
        z: 3,
      },
    ],
    tooltip: {
      ...base(t).tooltip,
      trigger: 'axis',
      axisPointer: sombraEje(t),
      formatter: (ps) => {
        const i = ps[0].dataIndex;
        return tooltipHtml(sinMarca(categorias[i]), [
          { color: t.acento, nombre: nombrePrincipal, valor: formato(valores[i]) },
          { color: t.referencia, nombre: nombreReferencia, valor: formato(referencias[i]) },
        ], notas[i]);
      },
    },
  };
}

/** Columnas verticales para categorías ordenadas (grupos de edad). */
export function columnas(t, {
  categorias, valores, colores, formato, formatoEje = formato, fragiles = [], notas = [], nombre,
}) {
  return {
    ...base(t),
    grid: { left: 4, right: 4, top: 26, bottom: 4, containLabel: true },
    xAxis: ejeCategorias(t, categorias, { color: t.tinta1, fontWeight: 600 }),
    yAxis: ejeValor(t, formatoEje),
    series: [{
      type: 'bar',
      name: nombre,
      data: valores.map((v, i) => dato(t, v, colores[i], fragiles[i])),
      barMaxWidth: 24,
      itemStyle: { borderRadius: [4, 4, 0, 0] },
      label: {
        show: true, position: 'top', color: t.tinta1, fontSize: 12, fontWeight: 600,
        formatter: (p) => formato(p.value),
      },
      emphasis: { disabled: true },
    }],
    tooltip: {
      ...base(t).tooltip,
      trigger: 'axis',
      axisPointer: sombraEje(t),
      formatter: (ps) => tooltipHtml(sinMarca(ps[0].name), [
        { color: colores[ps[0].dataIndex], nombre, valor: formato(ps[0].value) },
      ], notas[ps[0].dataIndex]),
    },
  };
}

/**
 * Ranking de las 16 alcaldías para un indicador. Todas en acento; si hay una seleccionada,
 * las demás se atenúan (énfasis) y su nombre va en negritas. `referencia` dibuja una
 * línea fina (la cifra de la CDMX o la mediana de las alcaldías).
 */
export function ranking(t, {
  filas, seleccion, formato, formatoEje = formato, referencia, unidad, ancho = 0,
}) {
  const categorias = filas.map((f) => f.nombre);
  const nombreSel = filas.find((f) => f.cve === seleccion)?.nombre;
  // En pantallas angostas los nombres largos (La Magdalena Contreras) van en dos líneas.
  const angosto = ancho > 0 && ancho < 520;
  return {
    ...base(t),
    grid: { left: 4, right: angosto ? 52 : 70, top: referencia ? 26 : 4, bottom: 4, containLabel: true },
    xAxis: ejeValor(t, formatoEje),
    yAxis: ejeCategorias(t, categorias, {
      formatter: (v) => (v === nombreSel ? `{sel|${v}}` : v),
      rich: { sel: { fontWeight: 700, color: t.tinta1, fontSize: 12 } },
      ...(angosto ? { width: 96, overflow: 'break', lineHeight: 13 } : {}),
    }, { inverse: true }),
    series: [{
      type: 'bar',
      // Énfasis con un tono más claro de la misma rampa y no con opacidad: la
      // opacidad también apagaría las etiquetas de valor.
      data: filas.map((f) => ({
        value: f.valor,
        cve: f.cve,
        itemStyle: { color: seleccion && f.cve !== seleccion ? t.atenuado : t.acento },
      })),
      barMaxWidth: 14,
      barCategoryGap: '32%',
      itemStyle: { color: t.acento, borderRadius: [0, 4, 4, 0] },
      label: {
        show: true, position: 'right', distance: 6, fontSize: 11.5, color: t.tinta1,
        formatter: (p) => (p.value === null || p.value === undefined ? 'No aplica' : formato(p.value)),
      },
      cursor: 'pointer',
      emphasis: { disabled: true },
      markLine: referencia ? {
        silent: true,
        symbol: 'none',
        lineStyle: { color: t.tinta2, width: 1, type: 'solid' },
        label: { formatter: referencia.etiqueta, color: t.tinta2, fontSize: 11, position: 'start', distance: 6 },
        data: [{ xAxis: referencia.valor }],
      } : undefined,
    }],
    tooltip: {
      ...base(t).tooltip,
      trigger: 'item',
      formatter: (p) => tooltipHtml(p.name, [
        { color: t.acento, nombre: unidad, valor: p.value === null || p.value === undefined ? 'No aplica' : formato(p.value) },
      ], 'Clic para ver su ficha'),
    },
  };
}

/**
 * Dispersión carga de cuidado × presión sobre las guarderías, con medianas. Una serie
 * invisible de puntos grandes hace de área de clic (>= 24 px) sobre cada alcaldía.
 */
export function dispersion(t, {
  puntos, seleccion, medianas, formatoX, formatoY, formatoEjeX = formatoX, formatoEjeY = formatoY,
  nombreX, nombreY, rotuloCuadrante,
}) {
  const datos = puntos.map((p) => ({ value: [p.x, p.y], nombre: p.nombre, cve: p.cve, abrev: p.abrev }));
  return {
    ...base(t),
    grid: { left: 8, right: 36, top: 36, bottom: 40, containLabel: true },
    xAxis: {
      ...ejeValor(t, formatoEjeX), scale: true, name: nombreX, nameLocation: 'middle', nameGap: 30,
      nameTextStyle: { color: t.tinta2, fontSize: 12 },
    },
    yAxis: {
      ...ejeValor(t, formatoEjeY), scale: true, name: nombreY, nameLocation: 'end', nameGap: 14,
      nameTextStyle: { color: t.tinta2, fontSize: 12, align: 'left' },
    },
    series: [
      {
        type: 'scatter',
        silent: true,
        data: datos.map((d) => {
          const sel = d.cve === seleccion;
          return {
            ...d,
            symbolSize: sel ? 16 : 11,
            itemStyle: {
              color: t.acento,
              borderColor: sel ? t.tinta1 : t.superficie,
              borderWidth: 2,
            },
            label: {
              show: true, position: 'right', distance: 6, formatter: d.abrev, fontSize: 11,
              color: sel ? t.tinta1 : t.tinta2, fontWeight: sel ? 700 : 500,
            },
            z: sel ? 3 : 2,
          };
        }),
        labelLayout: { hideOverlap: true },
        markLine: {
          silent: true,
          symbol: 'none',
          lineStyle: { color: t.eje, width: 1, type: 'solid' },
          label: { color: t.tinta3, fontSize: 11, formatter: 'mediana' },
          data: [
            { xAxis: medianas.x, label: { position: 'end' } },
            { yAxis: medianas.y, label: { position: 'insideEndTop' } },
          ],
        },
      },
      {
        type: 'scatter',
        data: datos,
        symbolSize: 28,
        itemStyle: { color: 'rgba(0,0,0,0)' },
        cursor: 'pointer',
        emphasis: { disabled: true },
        z: 4,
      },
    ],
    graphic: rotuloCuadrante ? [{
      type: 'text', right: 36, top: 40, silent: true,
      style: { text: rotuloCuadrante, fill: t.tinta3, font: `600 11px ${t.fuente}`, textAlign: 'right' },
    }] : [],
    tooltip: {
      ...base(t).tooltip,
      trigger: 'item',
      formatter: (p) => tooltipHtml(p.data.nombre, [
        { color: t.acento, nombre: nombreX, valor: formatoX(p.data.value[0]) },
        { color: t.acento, nombre: nombreY, valor: formatoY(p.data.value[1]) },
      ], 'Clic para ver su ficha'),
    },
  };
}

/**
 * Histograma de la carga por AGEB. Las de alta carga van en acento y el resto en gris:
 * se separan por la bandera, no por el valor (el umbral se aplicó sin redondear).
 */
export function histograma(t, { intervalos, umbral }) {
  const categorias = intervalos.map((i) => `${i.desde}–${i.hasta}`);
  const indiceUmbral = intervalos.findIndex((i) => umbral >= i.desde && umbral < i.hasta);
  return {
    ...base(t),
    grid: { left: 4, right: 12, top: 30, bottom: 34, containLabel: true },
    xAxis: {
      ...ejeCategorias(t, categorias, { color: t.tinta3, interval: 4, hideOverlap: true }),
      name: 'Personas que necesitan cuidado directo por cada 100 mujeres de 15 a 59',
      nameLocation: 'middle', nameGap: 28, nameTextStyle: { color: t.tinta2, fontSize: 11.5 },
    },
    yAxis: ejeValor(t, (v) => ent(v)),
    series: [
      {
        type: 'bar', stack: 'h', name: 'Resto de las AGEB',
        data: intervalos.map((i) => i.resto),
        barCategoryGap: '14%',
        itemStyle: { color: t.mercado },
        emphasis: { disabled: true },
      },
      {
        type: 'bar', stack: 'h', name: 'AGEB de alta carga',
        data: intervalos.map((i) => i.alta_carga),
        itemStyle: { color: t.acento },
        emphasis: { disabled: true },
        markLine: indiceUmbral >= 0 ? {
          silent: true,
          symbol: 'none',
          lineStyle: { color: t.tinta1, width: 1, type: 'solid' },
          label: { formatter: `Umbral de alta carga: ${num(umbral)}`, color: t.tinta1, fontSize: 11, position: 'end' },
          data: [{ xAxis: categorias[indiceUmbral] }],
        } : undefined,
      },
    ],
    tooltip: {
      ...base(t).tooltip,
      trigger: 'axis',
      axisPointer: sombraEje(t),
      formatter: (ps) => tooltipHtml(`Carga ${ps[0].name}`, ps.map((p) => ({
        color: p.color, nombre: p.seriesName, valor: `${ent(p.value)} AGEB`,
      }))),
    },
  };
}
