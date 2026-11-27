// Mosaico de las 16 alcaldías: un cuadro por alcaldía, acomodado según su posición
// aproximada en la ciudad (norte arriba). Sustituye al mapa de coropletas mientras el
// repositorio no tenga los polígonos del Marco Geoestadístico: no finge una geografía
// que no tenemos, y todas las alcaldías pesan lo mismo a la vista.

import { computed, ref } from 'vue';
import { segunIndicador, textoSobre } from '../formato.js';
import { colorSecuencial } from '../tema.js';

export const CUADRICULA = {
  '002': { col: 1, fila: 0, abrev: 'AZC' },
  '005': { col: 2, fila: 0, abrev: 'GAM' },
  '016': { col: 1, fila: 1, abrev: 'MH' },
  '015': { col: 2, fila: 1, abrev: 'CUH' },
  '017': { col: 3, fila: 1, abrev: 'VC' },
  '004': { col: 0, fila: 2, abrev: 'CUJ' },
  '010': { col: 1, fila: 2, abrev: 'AO' },
  '014': { col: 2, fila: 2, abrev: 'BJ' },
  '006': { col: 3, fila: 2, abrev: 'IZC' },
  '008': { col: 1, fila: 3, abrev: 'MC' },
  '003': { col: 2, fila: 3, abrev: 'COY' },
  '007': { col: 3, fila: 3, abrev: 'IZP' },
  '012': { col: 1, fila: 4, abrev: 'TLP' },
  '013': { col: 2, fila: 4, abrev: 'XOC' },
  '011': { col: 3, fila: 4, abrev: 'TLH' },
  '009': { col: 3, fila: 5, abrev: 'MA' },
};

const ANCHO = 100;
const ALTO = 78;
const HUECO = 8;
const MARGEN = 4;

export default {
  name: 'Mosaico',
  props: {
    filas: { type: Array, required: true },
    indicador: { type: Object, required: true },
    seleccion: { type: String, default: null },
    tokens: { type: Object, required: true },
  },
  emits: ['seleccionar'],
  setup(props) {
    const envoltura = ref(null);
    const burbuja = ref(null);

    const valores = computed(() => props.filas
      .map((f) => f[props.indicador.columna])
      .filter((v) => v !== null && v !== undefined));
    const minimo = computed(() => Math.min(...valores.value));
    const maximo = computed(() => Math.max(...valores.value));

    const lugares = computed(() => {
      const orden = props.filas
        .filter((f) => f[props.indicador.columna] !== null && f[props.indicador.columna] !== undefined)
        .map((f) => f[props.indicador.columna]);
      return Object.fromEntries(props.filas.map((f) => {
        const v = f[props.indicador.columna];
        if (v === null || v === undefined) return [f.cve_mun, null];
        return [f.cve_mun, orden.filter((o) => o > v).length + 1];
      }));
    });

    const celdas = computed(() => props.filas.filter((f) => CUADRICULA[f.cve_mun]).map((f) => {
      const pos = CUADRICULA[f.cve_mun];
      const v = f[props.indicador.columna];
      const relleno = colorSecuencial(v, minimo.value, maximo.value, props.tokens.secuencial)
        ?? props.tokens.hundida;
      return {
        cve: f.cve_mun,
        nombre: f.alcaldia,
        abrev: pos.abrev,
        x: MARGEN + pos.col * (ANCHO + HUECO),
        y: MARGEN + pos.fila * (ALTO + HUECO),
        relleno,
        texto: v === null || v === undefined ? props.tokens.tinta2 : textoSobre(relleno),
        valor: segunIndicador(v, props.indicador),
        lugar: lugares.value[f.cve_mun],
      };
    }));

    const anchoTotal = MARGEN * 2 + 4 * ANCHO + 3 * HUECO;
    const altoTotal = MARGEN * 2 + 6 * ALTO + 5 * HUECO;
    const gradiente = computed(() => `linear-gradient(90deg, ${props.tokens.secuencial.join(', ')})`);
    const hayNulos = computed(() => valores.value.length < props.filas.length);

    function mostrar(celda, evento) {
      const caja = envoltura.value?.getBoundingClientRect();
      if (!caja) return;
      const escala = caja.width / anchoTotal;
      const x = evento ? evento.clientX - caja.left + 14 : (celda.x + ANCHO) * escala + 8;
      const y = evento ? evento.clientY - caja.top + 14 : celda.y * escala;
      burbuja.value = { ...celda, x: Math.min(x, caja.width - 180), y };
    }
    const ocultar = () => { burbuja.value = null; };

    return {
      envoltura, burbuja, celdas, anchoTotal, altoTotal, gradiente, hayNulos, minimo, maximo,
      mostrar, ocultar, ANCHO, ALTO, segunIndicador,
    };
  },
  template: `<div class="mosaico" ref="envoltura">
    <svg :viewBox="'0 0 ' + anchoTotal + ' ' + altoTotal" role="group"
      :aria-label="'Mosaico de las 16 alcaldías coloreado por ' + indicador.etiqueta">
      <g v-for="c in celdas" :key="c.cve" class="mosaico__celda" :transform="'translate(' + c.x + ',' + c.y + ')'"
        tabindex="0" role="button" :aria-pressed="c.cve === seleccion ? 'true' : 'false'"
        :aria-label="c.nombre + ': ' + c.valor + (c.lugar ? ', lugar ' + c.lugar + ' de 16' : '')"
        @click="$emit('seleccionar', c.cve)"
        @keydown.enter.prevent="$emit('seleccionar', c.cve)" @keydown.space.prevent="$emit('seleccionar', c.cve)"
        @mousemove="mostrar(c, $event)" @mouseleave="ocultar" @focus="mostrar(c, null)" @blur="ocultar">
        <rect class="mosaico__aro" x="-3" y="-3" :width="ANCHO + 6" :height="ALTO + 6" rx="12" fill="none" stroke="none" />
        <rect class="mosaico__fondo" :width="ANCHO" :height="ALTO" rx="9" :fill="c.relleno" />
        <text class="mosaico__abrev" x="10" y="21" :fill="c.texto">{{ c.abrev }}</text>
        <text class="mosaico__valor" x="10" :y="ALTO - 12" :fill="c.texto">{{ c.valor }}</text>
      </g>
    </svg>
    <div class="escala-color" aria-hidden="true">
      <div class="escala-color__barra" :style="{ background: gradiente }"></div>
      <div class="escala-color__extremos">
        <span>{{ segunIndicador(minimo, indicador) }}</span>
        <span v-if="hayNulos" class="escala-color__na"><i></i>No aplica</span>
        <span>{{ segunIndicador(maximo, indicador) }}</span>
      </div>
    </div>
    <div v-if="burbuja" class="burbuja" :style="{ left: burbuja.x + 'px', top: burbuja.y + 'px' }">
      <strong>{{ burbuja.valor }}</strong>
      {{ burbuja.nombre }}<template v-if="burbuja.lugar"> · lugar {{ burbuja.lugar }} de 16</template>
    </div>
  </div>`,
};
