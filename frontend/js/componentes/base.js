// Piezas pequeñas que comparten todas las secciones.

import { computed, ref } from 'vue';
import { ent } from '../formato.js';

const TRAZOS = {
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5"/><path d="M12 7.5h.01"/>',
  aviso: '<path d="M10.3 3.9 2.6 17.3A2 2 0 0 0 4.3 20h15.4a2 2 0 0 0 1.7-2.7L13.7 3.9a2 2 0 0 0-3.4 0Z"/><path d="M12 9v4"/><path d="M12 16.5h.01"/>',
  flecha: '<path d="M5 12h14"/><path d="m13 6 6 6-6 6"/>',
  abajo: '<path d="M12 5v14"/><path d="m6 13 6 6 6-6"/>',
  sol: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
  luna: '<path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5Z"/>',
  descarga: '<path d="M12 4v11"/><path d="m7 10 5 5 5-5"/><path d="M5 20h14"/>',
  mapa: '<path d="M12 21s-6-5.4-6-10a6 6 0 0 1 12 0c0 4.6-6 10-6 10Z"/><circle cx="12" cy="11" r="2.2"/>',
  externo: '<path d="M14 4h6v6"/><path d="M20 4 11 13"/><path d="M19 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h5"/>',
};

export const Icono = {
  name: 'Icono',
  props: { nombre: { type: String, required: true } },
  computed: { trazo() { return TRAZOS[this.nombre] ?? ''; } },
  template: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
    stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false" v-html="trazo"></svg>`,
};

/** Nivel geográfico de una cifra. La de «Nacional» se distingue a propósito. */
export const Insignia = {
  name: 'Insignia',
  props: { nivel: { type: [String, Array], default: null } },
  computed: {
    niveles() { return [].concat(this.nivel ?? []).filter(Boolean); },
  },
  template: `<span v-for="n in niveles" :key="n" class="insignia"
    :class="{ 'insignia--nacional': n === 'Nacional' }" :title="'Nivel geográfico: ' + n">{{ n }}</span>`,
};

export const NotaFuente = {
  name: 'NotaFuente',
  components: { Insignia },
  props: { fuente: { type: [String, Array], default: null }, nivel: { type: [String, Array], default: null } },
  computed: {
    fuentes() { return [].concat(this.fuente ?? []).filter(Boolean).join(' · '); },
  },
  template: `<p class="nota-fuente">
    <span><span class="nota-fuente__etiqueta">Fuente:</span> {{ fuentes }}</span>
    <span v-if="nivel"><span class="nota-fuente__etiqueta">Nivel:</span> <insignia :nivel="nivel" /></span>
  </p>`,
};

export const Aviso = {
  name: 'Aviso',
  components: { Icono },
  props: { tipo: { type: String, default: 'nota' } },
  computed: {
    icono() { return this.tipo === 'precaucion' ? 'aviso' : 'info'; },
  },
  template: `<div class="aviso" :class="'aviso--' + tipo" role="note">
    <icono :nombre="icono" />
    <div><slot /></div>
  </div>`,
};

export const Hallazgo = {
  name: 'Hallazgo',
  components: { Insignia, Icono },
  props: { h: { type: Object, required: true } },
  template: `<article class="hallazgo tarjeta" :class="{ 'hallazgo--destacado': h.destacado }">
    <div class="hallazgo__cabeza">
      <h4 class="hallazgo__titulo">{{ h.titulo }}</h4>
      <div class="hallazgo__insignias">
        <insignia :nivel="h.nivel_geografico" />
        <span v-if="h.exploratorio" class="insignia insignia--exploratorio" title="Ubicaciones aproximadas">Exploratorio</span>
      </div>
    </div>
    <p class="hallazgo__texto">{{ h.texto }}</p>
    <p v-if="h.advertencia" class="hallazgo__advertencia"><icono nombre="info" /><span>{{ h.advertencia }}</span></p>
    <p class="hallazgo__fuente">{{ h.fuente }}</p>
  </article>`,
};

export const Indicador = {
  name: 'Indicador',
  components: { Insignia },
  props: {
    etiqueta: String, valor: String, unidad: String, contexto: String,
    nivel: [String, Array], fuente: String,
  },
  template: `<div class="indicador tarjeta">
    <div class="indicador__etiqueta">{{ etiqueta }}</div>
    <div class="indicador__valor">{{ valor }}<span v-if="unidad" class="indicador__unidad">{{ unidad }}</span></div>
    <div v-if="contexto" class="indicador__contexto">{{ contexto }}</div>
    <div class="indicador__pie"><insignia :nivel="nivel" /><span>{{ fuente }}</span></div>
  </div>`,
};

export const Medidor = {
  name: 'Medidor',
  props: { etiqueta: String, valor: Number, texto: String },
  template: `<div class="medidor">
    <div class="medidor__cabeza"><span>{{ etiqueta }}</span><strong>{{ texto }}</strong></div>
    <div class="medidor__pista" role="meter" :aria-valuenow="valor" aria-valuemin="0" aria-valuemax="100"
      :aria-label="etiqueta + ': ' + texto">
      <div class="medidor__relleno" :style="{ width: Math.max(0, Math.min(100, valor)) + '%' }"></div>
    </div>
  </div>`,
};

/**
 * Tabla accesible: la vista de datos gemela de cada gráfica.
 * columnas: [{ clave, etiqueta, formato?(valor, fila), numerica? }]
 */
export const TablaDatos = {
  name: 'TablaDatos',
  props: {
    columnas: Array, filas: Array, titulo: String, ordenable: Boolean,
    activa: { type: Function, default: null }, alta: Boolean,
  },
  setup(props) {
    const orden = ref({ clave: null, desc: true });
    const ordenadas = computed(() => {
      const { clave, desc } = orden.value;
      if (!clave) return props.filas;
      return [...props.filas].sort((a, b) => {
        const x = a[clave], y = b[clave];
        if (x === y) return 0;
        if (x === null || x === undefined) return 1;
        if (y === null || y === undefined) return -1;
        const r = typeof x === 'number' ? x - y : String(x).localeCompare(String(y), 'es');
        return desc ? -r : r;
      });
    });
    function ordenar(clave) {
      orden.value = orden.value.clave === clave
        ? { clave, desc: !orden.value.desc }
        : { clave, desc: true };
    }
    function ariaSort(clave) {
      if (!props.ordenable) return undefined;
      if (orden.value.clave !== clave) return 'none';
      return orden.value.desc ? 'descending' : 'ascending';
    }
    const mostrar = (c, f) => {
      const v = f[c.clave];
      if (c.formato) return c.formato(v, f);
      return v === null || v === undefined ? '—' : v;
    };
    return { ordenadas, ordenar, ariaSort, mostrar };
  },
  template: `<div class="tabla-envoltura" :class="{ 'tabla-alta': alta }" tabindex="0" role="region" :aria-label="'Tabla: ' + titulo">
    <table class="tabla">
      <caption class="sr">{{ titulo }}</caption>
      <thead><tr>
        <th v-for="c in columnas" :key="c.clave" scope="col" :class="{ num: c.numerica }" :aria-sort="ariaSort(c.clave)">
          <button v-if="ordenable" type="button" @click="ordenar(c.clave)">{{ c.etiqueta }}</button>
          <template v-else>{{ c.etiqueta }}</template>
        </th>
      </tr></thead>
      <tbody>
        <tr v-for="(f, i) in ordenadas" :key="i" :class="{ 'fila-activa': activa && activa(f) }">
          <td v-for="c in columnas" :key="c.clave" :class="{ num: c.numerica }">{{ mostrar(c, f) }}</td>
        </tr>
      </tbody>
    </table>
  </div>`,
};

/** Embudo en HTML: etapas anidadas con su barra, conteo de AGEB y de mujeres. */
export const Embudo = {
  name: 'Embudo',
  props: { etapas: Array, colores: Array },
  setup(props) {
    const maximo = computed(() => Math.max(...props.etapas.map((e) => e.agebs), 1));
    return { maximo, ent };
  },
  template: `<ol class="embudo">
    <li v-for="(e, i) in etapas" :key="e.etapa" class="embudo__etapa">
      <div class="embudo__texto"><span>{{ e.etapa }}</span>
        <strong>{{ ent(e.agebs) }} AGEB</strong></div>
      <div class="embudo__pista"><div class="embudo__barra"
        :style="{ width: Math.max(0.6, e.agebs / maximo * 100) + '%', background: colores[i] }"></div></div>
      <div class="embudo__mujeres">{{ ent(e.mujeres_15a59) }} mujeres de 15 a 59 viven ahí</div>
    </li>
  </ol>`,
};
