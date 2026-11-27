// 04 · Territorio (AGEB). Hallazgo B, exploratorio: AGEB de alta carga de cuidado sin
// guardería, residencia ni centro de día a menos de 1 km.

import { computed, reactive, ref, watch } from 'vue';
import { api } from '../api.js';
import Grafica from '../componentes/Grafica.js';
import MapaAgeb, { escalaMapa } from '../componentes/MapaAgeb.js';
import TarjetaGrafica from '../componentes/TarjetaGrafica.js';
import { Aviso, Embudo, Insignia, NotaFuente, TablaDatos } from '../componentes/base.js';
import { seleccion } from '../estado.js';
import { ent, num, pct } from '../formato.js';
import { histograma } from '../graficas.js';

export default {
  name: 'SeccionTerritorio',
  components: { Grafica, MapaAgeb, TarjetaGrafica, Aviso, Embudo, Insignia, NotaFuente, TablaDatos },
  props: {
    d: { type: Object, required: true },
    t: { type: Object, required: true },
    capasMapa: { type: Object, default: null }, // { agebs, establecimientos } (llegan después)
  },
  setup(props) {
    const capas = reactive({ carga: true, sinRespaldo: true, respaldo: false, otros: false, base: true });
    const alfabetico = computed(() => [...props.d.alcaldias.filas].sort((a, b) => a.alcaldia.localeCompare(b.alcaldia, 'es')));
    const nombre = computed(() => props.d.alcaldias.filas.find((f) => f.cve_mun === seleccion.mapa)?.alcaldia);

    // Resumen del territorio para la ciudad o la alcaldía elegida. Mientras llega el
    // nuevo, se conserva el anterior atenuado (sin saltos de diseño).
    const resumen = ref(props.d.territorio);
    const cargando = ref(false);
    watch(() => seleccion.mapa, async (cve) => {
      cargando.value = true;
      try { resumen.value = await api.territorio(cve); } finally { cargando.value = false; }
    });

    const opcionHistograma = computed(() => histograma(props.t, {
      intervalos: resumen.value.intervalos, umbral: resumen.value.umbral_alta_carga,
    }));
    const tablaHistograma = computed(() => ({
      columnas: [
        { clave: 'rango', etiqueta: 'Carga (personas por cada 100 mujeres)' },
        { clave: 'alta_carga', etiqueta: 'AGEB de alta carga', numerica: true, formato: (v) => ent(v) },
        { clave: 'resto', etiqueta: 'Resto de las AGEB', numerica: true, formato: (v) => ent(v) },
      ],
      filas: resumen.value.intervalos.map((i) => ({ ...i, rango: `${i.desde} a ${i.hasta}` }))
        .filter((i) => i.alta_carga + i.resto > 0),
    }));

    const sinRespaldo = computed(() => (props.capasMapa?.agebs.filas ?? [])
      .filter((a) => a.sin_respaldo && (!seleccion.mapa || a.cve_mun === seleccion.mapa))
      .sort((a, b) => b.mujeres_15a59 - a.mujeres_15a59));
    const tablaSinRespaldo = computed(() => ({
      columnas: [
        { clave: 'cvegeo_ageb', etiqueta: 'AGEB (clave)' },
        { clave: 'alcaldia', etiqueta: 'Alcaldía' },
        { clave: 'mujeres_15a59', etiqueta: 'Mujeres 15–59', numerica: true, formato: (v) => ent(v) },
        { clave: 'carga_directa_x100_mujeres', etiqueta: 'Carga x100 mujeres', numerica: true, formato: (v) => num(v) },
        { clave: 'pob_0a5', etiqueta: 'Niñas y niños 0–5', numerica: true, formato: (v) => ent(v) },
        { clave: 'pct_hog_jefa', etiqueta: '% hogares jefa', numerica: true, formato: (v) => pct(v) },
        { clave: 'guarderias_1km', etiqueta: 'Guarderías a 1 km', numerica: true, formato: (v) => ent(v) },
      ],
      filas: sinRespaldo.value,
    }));

    // La leyenda usa exactamente la escala de los puntos del mapa.
    const gradienteMapa = computed(() => `linear-gradient(90deg, ${escalaMapa(props.t).join(', ')})`);

    const elegir = (valor) => { seleccion.mapa = valor || null; };
    return {
      capas, alfabetico, nombre, seleccion, resumen, cargando, opcionHistograma, tablaHistograma,
      sinRespaldo, tablaSinRespaldo, gradienteMapa, elegir, ent, num,
    };
  },
  template: `<section class="seccion seccion--hundida" id="territorio" aria-labelledby="titulo-territorio">
    <div class="contenedor">
      <header class="seccion__cabeza">
        <span class="seccion__numero" aria-hidden="true">04</span>
        <div>
          <p class="seccion__escala">Escala de AGEB <insignia nivel="AGEB" />
            <span class="insignia insignia--exploratorio">Exploratorio</span></p>
          <h2 class="seccion__titulo" id="titulo-territorio">Territorio: mujeres que cuidan sin respaldo cerca</h2>
          <p class="seccion__entrada">Hallazgo B. Zonas en el cuartil más alto de carga de cuidado de la ciudad que no
            tienen ninguna guardería, residencia para personas mayores ni centro de día a menos de 1 km (unos 12 a 15
            minutos a pie).</p>
          <p class="seccion__fuentes">Fuentes: INEGI, Censo 2020 (AGEB urbanas) + INEGI, DENUE 05/2026</p>
        </div>
      </header>

      <aviso tipo="precaucion">
        <strong>Hallazgo exploratorio.</strong> Mientras no se integre el Marco Geoestadístico del INEGI, el punto de
        cada AGEB es la mediana de los establecimientos del DENUE que caen dentro, no el centroide de su polígono:
        está sesgado hacia las zonas comerciales. Al recalcular con los polígonos oficiales las cifras pueden cambiar.
        Las AGEB urbanas no cubren la zona rural (en Milpa Alta queda fuera el 16 % de la población).
      </aviso>

      <div class="filtros tarjeta separacion" role="group" aria-label="Filtros del mapa">
        <label class="campo"><span>Alcaldía</span>
          <select :value="seleccion.mapa ?? ''" @change="elegir($event.target.value)">
            <option value="">Toda la ciudad</option>
            <option v-for="f in alfabetico" :key="f.cve_mun" :value="f.cve_mun">{{ f.alcaldia }}</option>
          </select>
        </label>
        <fieldset class="campo" style="border:0;padding:0;margin:0"><legend>Capas del mapa</legend>
          <div class="casillas">
            <label class="casilla"><input type="checkbox" v-model="capas.carga">Carga por AGEB</label>
            <label class="casilla"><input type="checkbox" v-model="capas.sinRespaldo">Zonas sin respaldo</label>
            <label class="casilla"><input type="checkbox" v-model="capas.respaldo">Establecimientos de respaldo</label>
            <label class="casilla"><input type="checkbox" v-model="capas.otros">Otros establecimientos</label>
            <label class="casilla"><input type="checkbox" v-model="capas.base">Mapa base</label>
          </div>
        </fieldset>
      </div>

      <div class="rejilla-2-1">
        <figure class="tarjeta tarjeta-grafica mapa-envoltura">
          <figcaption class="tarjeta-grafica__cabeza"><div>
            <h4 class="tarjeta-grafica__titulo">{{ nombre ? 'AGEB de ' + nombre : 'Las 2,320 AGEB analizadas de la ciudad' }}</h4>
            <p class="tarjeta-grafica__subtitulo">Cada punto es una AGEB, coloreada por personas que necesitan cuidado
              directo por cada 100 mujeres de 15 a 59. Haz clic en un punto para ver su detalle.</p>
          </div></figcaption>
          <div class="leyenda">
            <span class="leyenda__item"><span class="leyenda__muestra" :style="{ background: gradienteMapa, width: '36px' }"></span>Carga de cuidado (menos → más)</span>
            <span class="leyenda__item"><span class="leyenda__muestra leyenda__muestra--anillo"></span>⚠ Alta carga sin respaldo a 1 km</span>
            <span class="leyenda__item" v-if="capas.respaldo"><span class="leyenda__muestra leyenda__muestra--punto" :style="{ background: t.tinta1 }"></span>Guardería, residencia o centro de día</span>
            <span class="leyenda__item" v-if="capas.otros"><span class="leyenda__muestra leyenda__muestra--hueco"></span>Otro establecimiento de cuidado</span>
          </div>
          <mapa-ageb v-if="capasMapa" :agebs="capasMapa.agebs.filas" :establecimientos="capasMapa.establecimientos.filas"
            :seleccion="seleccion.mapa" :capas="capas" :tokens="t" />
          <div v-else class="mapa" style="display:grid;place-items:center;color:var(--tinta-2)">Cargando el mapa…</div>
          <p class="mapa-ayuda">Haz clic en el mapa para activar el zoom con la rueda del ratón. Sin internet, el mapa
            base no carga pero los puntos sí se muestran.</p>
          <nota-fuente :fuente="['INEGI, Censo 2020 + DENUE 05/2026', 'mapa base © colaboradores de OpenStreetMap']" nivel="AGEB" />
        </figure>

        <div class="pila" :class="{ atenuado: cargando }">
          <div class="tarjeta tarjeta-grafica">
            <h4 class="tarjeta-grafica__titulo">De la carga a la falta de respaldo</h4>
            <p class="tarjeta-grafica__subtitulo">{{ nombre ?? 'Toda la ciudad' }}. Cada etapa es un subconjunto de la anterior.</p>
            <embudo :etapas="resumen.embudo" :colores="t.embudo" />
            <nota-fuente fuente="INEGI, Censo 2020 + DENUE 05/2026" nivel="AGEB" />
          </div>
          <tarjeta-grafica titulo="Cómo se reparte la carga entre las AGEB"
            :subtitulo="(nombre ?? 'Toda la ciudad') + '. En violeta, las de alta carga (cuartil superior de la ciudad).'"
            fuente="INEGI, Censo 2020" nivel="AGEB" :tabla="tablaHistograma">
            <grafica :opcion="opcionHistograma" :alto="260" etiqueta="Histograma de la carga de cuidado por AGEB" />
            <template #notas><span>Mediana: {{ num(resumen.mediana) }} · percentiles 10 y 90: {{ num(resumen.percentil_10) }} y {{ num(resumen.percentil_90) }}.</span></template>
          </tarjeta-grafica>
        </div>
      </div>

      <div class="subtitulo-bloque">
        <h3>Las AGEB sin respaldo{{ nombre ? ' en ' + nombre : '' }}</h3>
        <p>{{ ent(sinRespaldo.length) }} AGEB de alta carga sin ningún servicio de respaldo a menos de 1 km, ordenadas
          por número de mujeres de 15 a 59 que viven en ellas.</p>
      </div>
      <div class="tarjeta tarjeta-grafica">
        <tabla-datos v-if="sinRespaldo.length" :columnas="tablaSinRespaldo.columnas" :filas="tablaSinRespaldo.filas"
          titulo="AGEB de alta carga sin respaldo a 1 km" ordenable alta />
        <p v-else class="hallazgo__texto">No hay AGEB de alta carga sin respaldo en {{ nombre }}.</p>
        <nota-fuente fuente="INEGI, Censo 2020 + DENUE 05/2026" nivel="AGEB" />
      </div>
    </div>
  </section>`,
};
