// Contenedor de cada gráfica: título, subtítulo, la gráfica, su tabla gemela (para quien
// no puede o no quiere leer la gráfica) y la nota de fuente con el nivel geográfico.

import { ref } from 'vue';
import { NotaFuente, TablaDatos } from './base.js';

export default {
  name: 'TarjetaGrafica',
  components: { NotaFuente, TablaDatos },
  props: {
    titulo: String,
    subtitulo: String,
    fuente: [String, Array],
    nivel: [String, Array],
    tabla: { type: Object, default: null }, // { columnas, filas }
  },
  setup() {
    const verTabla = ref(false);
    return { verTabla };
  },
  template: `<figure class="tarjeta tarjeta-grafica">
    <figcaption class="tarjeta-grafica__cabeza">
      <div>
        <h4 class="tarjeta-grafica__titulo">{{ titulo }}</h4>
        <p v-if="subtitulo" class="tarjeta-grafica__subtitulo">{{ subtitulo }}</p>
      </div>
      <button v-if="tabla" type="button" class="boton-texto" :aria-pressed="verTabla ? 'true' : 'false'"
        @click="verTabla = !verTabla">{{ verTabla ? 'Ver gráfica' : 'Ver tabla' }}</button>
    </figcaption>
    <div v-show="!verTabla"><slot /></div>
    <tabla-datos v-if="tabla && verTabla" :columnas="tabla.columnas" :filas="tabla.filas" :titulo="titulo" />
    <div v-if="$slots.notas" class="tarjeta-grafica__notas"><slot name="notas" /></div>
    <nota-fuente :fuente="fuente" :nivel="nivel" />
  </figure>`,
};
