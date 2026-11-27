// 03 · Alcaldías. La comparación entre las 16 alcaldías (mosaico y ranking por
// indicador), la ficha de una alcaldía con sus hallazgos y el cruce entre la carga de
// cuidado y la presión sobre las guarderías.

import { computed, ref, watch } from 'vue';
import { api } from '../api.js';
import Grafica from '../componentes/Grafica.js';
import Mosaico, { CUADRICULA } from '../componentes/Mosaico.js';
import TarjetaGrafica from '../componentes/TarjetaGrafica.js';
import { Hallazgo, Icono, Insignia, NotaFuente, TablaDatos } from '../componentes/base.js';
import { seleccion } from '../estado.js';
import { ejeIndicador, ent, num, pct, segunIndicador } from '../formato.js';
import { dispersion, ranking } from '../graficas.js';

export default {
  name: 'SeccionAlcaldias',
  components: { Grafica, Mosaico, TarjetaGrafica, Hallazgo, Icono, Insignia, NotaFuente, TablaDatos },
  props: { d: { type: Object, required: true }, t: { type: Object, required: true } },
  setup(props) {
    const filas = computed(() => props.d.alcaldias.filas);
    const indicadores = computed(() => props.d.alcaldias.indicadores);
    const ciudad = computed(() => props.d.alcaldias.ciudad);
    const columna = ref('carga_directa_x100_mujeres');
    const indicador = computed(() => indicadores.value.find((i) => i.columna === columna.value));
    const alfabetico = computed(() => [...filas.value].sort((a, b) => a.alcaldia.localeCompare(b.alcaldia, 'es')));

    // --- Ranking -----------------------------------------------------------------
    const formatoIndicador = (v) => segunIndicador(v, indicador.value);
    const referencia = computed(() => {
      if (columna.value === 'carga_directa_x100_mujeres' && ciudad.value.carga_cdmx !== null) {
        return { valor: ciudad.value.carga_cdmx, etiqueta: `Ciudad: ${num(ciudad.value.carga_cdmx)}` };
      }
      const m = ciudad.value.medianas[columna.value];
      return m === null || m === undefined ? null : { valor: m, etiqueta: `Mediana: ${formatoIndicador(m)}` };
    });
    const anchoRanking = ref(0);
    const opcionRanking = computed(() => {
      const ordenadas = [...filas.value].sort((a, b) => {
        const x = a[columna.value], y = b[columna.value];
        if (x === null || x === undefined) return 1;
        if (y === null || y === undefined) return -1;
        return y - x;
      });
      return ranking(props.t, {
        filas: ordenadas.map((f) => ({ cve: f.cve_mun, nombre: f.alcaldia, valor: f[columna.value] })),
        seleccion: seleccion.ficha,
        formato: formatoIndicador,
        formatoEje: (v) => ejeIndicador(v, indicador.value),
        referencia: referencia.value,
        unidad: indicador.value.unidad,
        ancho: anchoRanking.value,
      });
    });
    const elegir = (cve) => { if (cve) seleccion.ficha = cve; };
    const clicGrafica = (p) => elegir(p.data?.cve);

    // --- Ficha de la alcaldía (se conserva la anterior, atenuada, mientras carga) ---
    const ficha = ref(null);
    const cargandoFicha = ref(false);
    const errorFicha = ref(null);
    watch(() => seleccion.ficha, async (cve) => {
      if (!cve) return;
      cargandoFicha.value = true;
      errorFicha.value = null;
      try {
        ficha.value = await api.alcaldia(cve);
      } catch (e) {
        errorFicha.value = e.message;
      } finally {
        cargandoFicha.value = false;
      }
    }, { immediate: true });
    const lugar = (col) => ficha.value?.posiciones?.[col];
    const tablaEstablecimientos = computed(() => ({
      columnas: [
        { clave: 'tipo', etiqueta: 'Tipo de establecimiento' },
        { clave: 'publico', etiqueta: 'Públicos', numerica: true, formato: (v) => ent(v) },
        { clave: 'privado', etiqueta: 'Privados', numerica: true, formato: (v) => ent(v) },
        { clave: 'total', etiqueta: 'Total', numerica: true, formato: (v) => ent(v) },
        { clave: 'es_respaldo', etiqueta: 'Cuenta como respaldo', formato: (v) => (v ? 'Sí' : 'No') },
      ],
      filas: ficha.value?.establecimientos.por_tipo ?? [],
    }));
    function verEnMapa() {
      seleccion.mapa = seleccion.ficha;
      document.getElementById('territorio')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // --- Dispersión: carga × presión sobre guarderías ------------------------------
    const opcionDispersion = computed(() => dispersion(props.t, {
      puntos: filas.value.map((f) => ({
        cve: f.cve_mun, nombre: f.alcaldia, abrev: CUADRICULA[f.cve_mun]?.abrev ?? f.alcaldia,
        x: f.carga_directa_x100_mujeres, y: f.ninos_0a5_por_guarderia,
      })),
      seleccion: seleccion.ficha,
      medianas: {
        x: ciudad.value.medianas.carga_directa_x100_mujeres,
        y: ciudad.value.medianas.ninos_0a5_por_guarderia,
      },
      formatoX: (v) => num(v),
      formatoY: (v) => ent(v),
      formatoEjeX: (v) => num(v, 0),
      nombreX: 'Carga de cuidado (personas por cada 100 mujeres de 15 a 59)',
      nombreY: 'Niñas y niños de 0 a 5 por guardería',
      rotuloCuadrante: 'Más carga y más presión',
    }));

    // --- Tabla completa -------------------------------------------------------------
    const tablaCompleta = computed(() => ({
      columnas: [
        { clave: 'alcaldia', etiqueta: 'Alcaldía' },
        { clave: 'mujeres_15a59', etiqueta: 'Mujeres 15–59', numerica: true, formato: (v) => ent(v) },
        { clave: 'carga_directa_x100_mujeres', etiqueta: 'Carga x100 mujeres', numerica: true, formato: (v) => num(v) },
        { clave: 'pct_hog_jefa', etiqueta: '% hogares jefa', numerica: true, formato: (v) => pct(v) },
        { clave: 'pct_mujeres_inactivas', etiqueta: '% mujeres fuera del mercado laboral', numerica: true, formato: (v) => pct(v) },
        { clave: 'agebs_alta_carga', etiqueta: 'AGEB alta carga', numerica: true, formato: (v) => ent(v) },
        { clave: 'agebs_sin_respaldo', etiqueta: 'AGEB sin respaldo', numerica: true, formato: (v) => ent(v) },
        { clave: 'mujeres_sin_respaldo', etiqueta: 'Mujeres sin respaldo', numerica: true, formato: (v) => ent(v) },
        { clave: 'guarderias', etiqueta: 'Guarderías', numerica: true, formato: (v) => ent(v) },
        { clave: 'ninos_0a5_por_guarderia', etiqueta: 'Niñas/os por guardería', numerica: true, formato: (v) => ent(v) },
        { clave: 'cuidado_mayores', etiqueta: 'Estab. personas mayores', numerica: true, formato: (v) => ent(v) },
        { clave: 'mayores_60_por_establecimiento', etiqueta: '60+ por estab.', numerica: true, formato: (v) => ent(v) },
        { clave: 'pct_guarderias_publicas', etiqueta: '% guarderías públicas', numerica: true, formato: (v) => pct(v) },
      ],
      filas: filas.value,
    }));
    const filaActiva = (f) => f.cve_mun === seleccion.ficha;

    const hallazgos = computed(() => props.d.hallazgos.alcaldias.hallazgos);

    return {
      filas, indicadores, ciudad, columna, indicador, alfabetico, seleccion, elegir, clicGrafica,
      anchoRanking, opcionRanking, ficha, cargandoFicha, errorFicha, lugar, tablaEstablecimientos, verEnMapa,
      opcionDispersion, tablaCompleta, filaActiva, hallazgos, ent, num, pct,
    };
  },
  template: `<section class="seccion" id="alcaldias" aria-labelledby="titulo-alcaldias">
    <div class="contenedor">
      <header class="seccion__cabeza">
        <span class="seccion__numero" aria-hidden="true">03</span>
        <div>
          <p class="seccion__escala">Escala de alcaldía <insignia nivel="Alcaldía" /></p>
          <h2 class="seccion__titulo" id="titulo-alcaldias">Alcaldías: dónde pesa más el cuidado</h2>
          <p class="seccion__entrada">Cuántas personas necesitan cuidado directo por cada mujer en edad de cuidar,
            cuánta oferta formal de cuidado hay cerca y dónde hay zonas de alta carga sin ningún respaldo.</p>
          <p class="seccion__fuentes">Fuentes: INEGI, Censo de Población y Vivienda 2020 · INEGI, DENUE 05/2026</p>
        </div>
      </header>

      <div class="hallazgos">
        <hallazgo v-for="h in hallazgos" :key="h.clave" :h="h" />
      </div>

      <div class="subtitulo-bloque">
        <h3>Compara las 16 alcaldías</h3>
        <p>Elige un indicador y una alcaldía. También puedes hacer clic en un cuadro del mosaico o en una barra.</p>
      </div>
      <div class="filtros tarjeta" role="group" aria-label="Filtros de la comparación entre alcaldías">
        <label class="campo"><span>Indicador</span>
          <select v-model="columna">
            <option v-for="i in indicadores" :key="i.columna" :value="i.columna">{{ i.etiqueta }}</option>
          </select>
        </label>
        <label class="campo"><span>Alcaldía de la ficha</span>
          <select :value="seleccion.ficha" @change="elegir($event.target.value)">
            <option v-for="f in alfabetico" :key="f.cve_mun" :value="f.cve_mun">{{ f.alcaldia }}</option>
          </select>
        </label>
      </div>

      <div class="rejilla-1-2">
        <figure class="tarjeta tarjeta-grafica">
          <figcaption class="tarjeta-grafica__cabeza"><div>
            <h4 class="tarjeta-grafica__titulo">{{ indicador.etiqueta }}</h4>
            <p class="tarjeta-grafica__subtitulo">{{ indicador.unidad }}. Cada cuadro es una alcaldía, en su posición aproximada (norte arriba).</p>
          </div></figcaption>
          <mosaico :filas="filas" :indicador="indicador" :seleccion="seleccion.ficha" :tokens="t" @seleccionar="elegir" />
          <p class="nota-fuente"><span><span class="nota-fuente__etiqueta">Fuente:</span> {{ indicador.fuente }}</span>
            <span><span class="nota-fuente__etiqueta">Nivel:</span> <insignia nivel="Alcaldía" /></span>
            <span v-if="indicador.exploratorio" class="insignia insignia--exploratorio">Exploratorio</span></p>
        </figure>
        <tarjeta-grafica titulo="Las 16 alcaldías en orden" :subtitulo="indicador.descripcion"
          :fuente="indicador.fuente" nivel="Alcaldía" :tabla="tablaCompleta">
          <grafica :opcion="opcionRanking" :alto="520" :etiqueta="'Ranking de alcaldías por ' + indicador.etiqueta"
            @clic="clicGrafica" @ancho="anchoRanking = $event" />
          <template #notas>
            <span v-if="indicador.advertencia">{{ indicador.advertencia }}</span>
            <span v-if="indicador.exploratorio">Exploratorio: las ubicaciones de las AGEB son aproximadas.</span>
          </template>
        </tarjeta-grafica>
      </div>

      <article class="tarjeta ficha separacion" :class="{ atenuado: cargandoFicha }" aria-live="polite" v-if="ficha">
        <div class="ficha__cabeza">
          <div>
            <p class="antetitulo">Ficha de alcaldía</p>
            <h3 class="ficha__nombre">{{ ficha.alcaldia.alcaldia }}</h3>
          </div>
          <button type="button" class="boton-primario" @click="verEnMapa"><icono nombre="mapa" />Ver sus AGEB en el mapa</button>
        </div>
        <div class="ficha__cifras">
          <div class="ficha__cifra"><span>Mujeres de 15 a 59 años</span>
            <strong>{{ ent(ficha.alcaldia.mujeres_15a59) }}</strong>
            <small>{{ pct(ficha.alcaldia.mujeres_15a59 / ficha.ciudad.mujeres_15a59 * 100) }} de la ciudad</small></div>
          <div class="ficha__cifra"><span>Carga de cuidado directo</span>
            <strong>{{ num(ficha.alcaldia.carga_directa_x100_mujeres) }}</strong>
            <small>Lugar {{ ficha.alcaldia.rango_carga }} de 16 · ciudad: {{ num(ficha.ciudad.carga_cdmx) }}</small></div>
          <div class="ficha__cifra"><span>Mujeres en zonas sin respaldo</span>
            <strong>{{ ent(ficha.alcaldia.mujeres_sin_respaldo) }}</strong>
            <small>{{ ficha.alcaldia.agebs_sin_respaldo }} de {{ ficha.alcaldia.agebs_alta_carga }} AGEB de alta carga · exploratorio</small></div>
          <div class="ficha__cifra"><span>Niñas y niños por guardería</span>
            <strong>{{ ent(ficha.alcaldia.ninos_0a5_por_guarderia) }}</strong>
            <small>Lugar {{ lugar('ninos_0a5_por_guarderia')?.lugar }} de 16 en presión</small></div>
        </div>
        <div class="hallazgos">
          <hallazgo v-for="h in ficha.hallazgos" :key="h.clave" :h="h" />
        </div>
        <div class="subtitulo-bloque" style="margin-top:28px">
          <h4>Establecimientos de cuidado registrados</h4>
          <p>{{ ent(ficha.establecimientos.total) }} establecimientos en el DENUE, de los cuales
            {{ ent(ficha.establecimientos.respaldo) }} cuentan como respaldo (sustituyen horas de cuidado en el hogar).</p>
        </div>
        <tabla-datos :columnas="tablaEstablecimientos.columnas" :filas="tablaEstablecimientos.filas"
          :titulo="'Establecimientos de cuidado en ' + ficha.alcaldia.alcaldia" />
        <nota-fuente :fuente="[ficha.establecimientos.fuente, 'INEGI, Censo 2020']" nivel="Alcaldía" />
      </article>
      <p v-if="errorFicha" class="aviso aviso--precaucion separacion">No se pudo cargar la ficha: {{ errorFicha }}</p>

      <div class="subtitulo-bloque">
        <h3>Mucha carga y poca oferta</h3>
        <p>Cada punto es una alcaldía. A la derecha, más personas que necesitan cuidado por cada mujer; arriba, más
          niñas y niños por cada guardería registrada. Las líneas marcan la mediana de las alcaldías.</p>
      </div>
      <tarjeta-grafica titulo="Carga de cuidado y presión sobre las guarderías"
        subtitulo="La presión sobre la oferta no es cobertura: el DENUE registra establecimientos, no lugares disponibles."
        fuente="INEGI, Censo 2020 + DENUE 05/2026" nivel="Alcaldía" :tabla="tablaCompleta">
        <grafica :opcion="opcionDispersion" :alto="440" etiqueta="Dispersión de alcaldías: carga de cuidado contra niñas y niños por guardería" @clic="clicGrafica" />
      </tarjeta-grafica>

      <div class="subtitulo-bloque">
        <h3>Todas las cifras por alcaldía</h3>
        <p>Haz clic en un encabezado para ordenar. <a href="/api/indicadores/resumen_alcaldia.csv" download>Descargar en CSV</a>.</p>
      </div>
      <div class="tarjeta tarjeta-grafica">
        <tabla-datos :columnas="tablaCompleta.columnas" :filas="tablaCompleta.filas" titulo="Indicadores de las 16 alcaldías"
          ordenable :activa="filaActiva" />
        <nota-fuente fuente="INEGI, Censo 2020 + DENUE 05/2026" nivel="Alcaldía" />
      </div>
    </div>
  </section>`,
};
