// Envoltorio de ECharts (global `echarts`, cargado en index.html). Se redibuja cuando
// cambian las opciones (por datos o por tema) y se ajusta al tamaño de su contenedor.
// Emite `ancho` (px) al montarse y al cambiar de tamaño: algunas gráficas lo usan para
// decidir qué etiquetas caben dentro de su barra en vez de recortarlas.

import { onBeforeUnmount, onMounted, ref, watch } from 'vue';

export default {
  name: 'Grafica',
  props: {
    opcion: { type: Object, required: true },
    alto: { type: [Number, String], default: 320 },
    etiqueta: { type: String, default: '' },
  },
  emits: ['clic', 'ancho'],
  setup(props, { emit }) {
    const el = ref(null);
    let grafica = null;
    let observador = null;
    let anchoPrevio = 0;

    const aplicar = () => grafica?.setOption(props.opcion, { notMerge: true, lazyUpdate: true });

    onMounted(() => {
      grafica = window.echarts.init(el.value, null, { renderer: 'svg' });
      aplicar();
      grafica.on('click', (p) => emit('clic', p));
      observador = new ResizeObserver(() => {
        grafica?.resize();
        const ancho = Math.round(el.value?.clientWidth ?? 0);
        if (ancho && ancho !== anchoPrevio) {
          anchoPrevio = ancho;
          emit('ancho', ancho);
        }
      });
      observador.observe(el.value);
    });
    watch(() => props.opcion, aplicar);
    onBeforeUnmount(() => {
      observador?.disconnect();
      grafica?.dispose();
      grafica = null;
    });
    return { el };
  },
  template: `<div ref="el" class="grafica" role="img" :aria-label="etiqueta"
    :style="{ height: typeof alto === 'number' ? alto + 'px' : alto }"></div>`,
};
