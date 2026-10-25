// Punto de entrada del frontend (Vue 3 sin paso de compilación: las plantillas se
// compilan en el navegador). Carga los datos de la API y arma la página de lo general
// a lo particular: México → Ciudad de México → alcaldías → AGEB.

import { createApp, nextTick, onBeforeUnmount, onMounted, ref, shallowRef } from 'vue';
import { api } from './api.js';
import { Icono } from './componentes/base.js';
import { seleccion } from './estado.js';
import { formato } from './formato.js';
import { alternarTema, tema, tokens } from './tema.js';
import Portada from './secciones/Portada.js';
import SeccionNacional from './secciones/Nacional.js';
import SeccionCdmx from './secciones/Cdmx.js';
import SeccionAlcaldias from './secciones/Alcaldias.js';
import SeccionTerritorio from './secciones/Territorio.js';
import SeccionMetodologia from './secciones/Metodologia.js';

const SECCIONES = [
  { id: 'mexico', num: '01', nombre: 'México' },
  { id: 'cdmx', num: '02', nombre: 'CDMX' },
  { id: 'alcaldias', num: '03', nombre: 'Alcaldías' },
  { id: 'territorio', num: '04', nombre: 'Territorio' },
  { id: 'metodologia', num: '05', nombre: 'Metodología' },
];

async function cargarDatos() {
  const [
    estado, metodologia, kpis, hNacional, hCdmx, hAlcaldias, enutActividad, brecha,
    dobleJornada, porEdad, porCondicion, enasic, alcaldias, territorio,
  ] = await Promise.all([
    api.estado(), api.metodologia(), api.kpis(), api.hallazgos('nacional'), api.hallazgos('cdmx'),
    api.hallazgos('alcaldias'), api.enutActividad(), api.enutBrecha(), api.dobleJornada(),
    api.porGrupo('Grupo de edad'), api.porGrupo('Condición de actividad'), api.enasic(),
    api.alcaldias(), api.territorio(null),
  ]);
  return {
    estado, metodologia, kpis, enutActividad, brecha, dobleJornada, porEdad, porCondicion, enasic,
    alcaldias, territorio, hallazgos: { nacional: hNacional, cdmx: hCdmx, alcaldias: hAlcaldias },
  };
}

const App = {
  name: 'Observatorio',
  components: {
    Icono, Portada, SeccionNacional, SeccionCdmx, SeccionAlcaldias, SeccionTerritorio, SeccionMetodologia,
  },
  setup() {
    const d = shallowRef(null);
    const capasMapa = shallowRef(null);
    const error = ref(null);
    const activa = ref(null);
    let observador = null;

    function observarSecciones() {
      const visibles = new Map();
      observador = new IntersectionObserver((entradas) => {
        for (const e of entradas) visibles.set(e.target.id, e.isIntersecting ? e.intersectionRatio : 0);
        const [id, ratio] = [...visibles.entries()].sort((a, b) => b[1] - a[1])[0] ?? [];
        activa.value = ratio > 0 ? id : null;
      }, { rootMargin: '-80px 0px -45% 0px', threshold: [0, 0.1, 0.25, 0.5] });
      SECCIONES.forEach((s) => { const el = document.getElementById(s.id); if (el) observador.observe(el); });
    }

    onMounted(async () => {
      try {
        const datos = await cargarDatos();
        // La ficha arranca en la alcaldía con más mujeres en zonas sin respaldo.
        const filas = datos.alcaldias.filas;
        seleccion.ficha = [...filas].sort((a, b) => b.mujeres_sin_respaldo - a.mujeres_sin_respaldo)[0]?.cve_mun;
        d.value = datos;
        // Las capas del mapa pesan más: se piden después, sin bloquear el resto.
        Promise.all([api.agebs(), api.establecimientos()])
          .then(([agebs, establecimientos]) => { capasMapa.value = { agebs, establecimientos }; })
          .catch((e) => { error.value = `No se pudieron cargar las capas del mapa: ${e.message}`; });
        await nextTick();
        observarSecciones();
        if (window.location.hash) document.querySelector(window.location.hash)?.scrollIntoView();
      } catch (e) {
        error.value = e.message;
      }
    });
    onBeforeUnmount(() => observador?.disconnect());

    return { d, capasMapa, error, activa, secciones: SECCIONES, tema, tokens, alternarTema };
  },
  template: `
    <header class="encabezado">
      <div class="contenedor encabezado__fila">
        <a class="marca" href="#inicio">
          <img class="marca__icono" src="img/icono.svg" alt="" width="30" height="30">
          <span class="marca__texto">Observatorio de la Economía del Cuidado<small>Mujeres cuidadoras · México y CDMX</small></span>
        </a>
        <nav class="navegacion" aria-label="Secciones del observatorio">
          <ol>
            <li v-for="s in secciones" :key="s.id">
              <a :href="'#' + s.id" :aria-current="activa === s.id ? 'true' : null"><span>{{ s.num }}</span>{{ s.nombre }}</a>
            </li>
          </ol>
        </nav>
        <button type="button" class="boton-icono" @click="alternarTema"
          :aria-label="tema === 'dark' ? 'Cambiar a tema claro' : 'Cambiar a tema oscuro'"
          :title="tema === 'dark' ? 'Tema claro' : 'Tema oscuro'">
          <icono :nombre="tema === 'dark' ? 'sol' : 'luna'" />
        </button>
      </div>
    </header>

    <div v-if="d && !d.estado.controles_ok" class="banda-alerta" role="alert">
      <div class="contenedor">Alguna cifra de control no cuadra con la del ETL. Revisa «Estado de los datos» en
        <a href="#metodologia">Metodología</a> antes de citar cualquier cifra.</div>
    </div>

    <main id="contenido" tabindex="-1">
      <div v-if="error && !d" class="error-carga">
        <div class="tarjeta">
          <h2>No se pudieron cargar los datos</h2>
          <p>{{ error }}</p>
          <p style="margin-top:10px">Revisa que el servidor siga corriendo (<code>python iniciar.py</code>) y vuelve a cargar la página.</p>
        </div>
      </div>
      <div v-else-if="!d" class="cargando-inicial" role="status">Cargando el observatorio…</div>
      <template v-else>
        <portada :d="d" />
        <seccion-nacional :d="d" :t="tokens" />
        <seccion-cdmx :d="d" :t="tokens" />
        <seccion-alcaldias :d="d" :t="tokens" />
        <seccion-territorio :d="d" :t="tokens" :capas-mapa="capasMapa" />
        <seccion-metodologia :d="d" />
      </template>
    </main>

    <footer class="pie" v-if="d">
      <div class="contenedor pie__rejilla">
        <div>
          <strong>Observatorio de la Economía del Cuidado</strong><br>
          Proyecto universitario de Ciencia de Datos · UNRC · 7.º semestre.<br>
          Datos: INEGI (ENUT 2024, ENASIC 2022, Censo de Población y Vivienda 2020, DENUE 05/2026).
        </div>
        <div>
          <a href="/api/docs">API de datos</a> · <a href="#metodologia">Metodología</a><br>
          Fuente activa: {{ d.estado.fuente === 'postgres' ? 'PostgreSQL (esquema indicadores)' : 'respaldo local desde data/curada/' }}
        </div>
      </div>
    </footer>
  `,
};

const app = createApp(App);
app.config.globalProperties.$f = formato;
app.mount('#app');
