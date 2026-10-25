// 05 · Cómo leer estos datos: las advertencias del diccionario de datos, las fuentes,
// el glosario, las descargas y el estado de la fuente de datos (con las cifras de control).

import { computed } from 'vue';
import { Icono, Insignia, TablaDatos } from '../componentes/base.js';
import { ent } from '../formato.js';

const DESCRIPCION_TABLAS = {
  kpi_cdmx: 'Cifras de cabecera',
  resumen_alcaldia: 'Las 16 alcaldías',
  carga_ageb: 'Carga y acceso por AGEB (capa del mapa)',
  establecimientos_cuidado: 'Establecimientos de cuidado del DENUE',
  enut_carga_actividad: 'ENUT: cuidado por actividad, CDMX y nacional',
  enut_brecha_mujeres_cdmx: 'ENUT: brecha de las mujeres de la CDMX',
  enut_doble_jornada: 'ENUT: doble jornada',
  enut_cuidado_por_grupo: 'ENUT: qué mujeres cuidan más',
  enasic_cuidadoras: 'ENASIC: cuidadoras y servicios (nacional)',
};

export default {
  name: 'SeccionMetodologia',
  components: { Icono, Insignia, TablaDatos },
  props: { d: { type: Object, required: true } },
  setup(props) {
    const m = computed(() => props.d.metodologia);
    const estado = computed(() => props.d.estado);
    const tablas = computed(() => Object.entries(estado.value.tablas)
      .map(([nombre, filas]) => ({ nombre, filas, descripcion: DESCRIPCION_TABLAS[nombre] ?? '' })));
    const controles = computed(() => ({
      columnas: [
        { clave: 'etiqueta', etiqueta: 'Cifra de control' },
        { clave: 'esperado', etiqueta: 'Esperado', numerica: true, formato: (v) => (typeof v === 'number' ? v.toLocaleString('es-MX') : v) },
        { clave: 'obtenido', etiqueta: 'Obtenido', numerica: true, formato: (v) => (v === null ? '—' : typeof v === 'number' ? v.toLocaleString('es-MX') : v) },
        { clave: 'ok', etiqueta: 'Estado', formato: (v) => (v ? '✓ Cuadra' : '✗ No cuadra') },
      ],
      filas: estado.value.controles,
    }));
    const cuadran = computed(() => estado.value.controles.filter((c) => c.ok).length);
    return { m, estado, tablas, controles, cuadran, ent };
  },
  template: `<section class="seccion" id="metodologia" aria-labelledby="titulo-metodologia">
    <div class="contenedor">
      <header class="seccion__cabeza">
        <span class="seccion__numero" aria-hidden="true">05</span>
        <div>
          <p class="seccion__escala">Método</p>
          <h2 class="seccion__titulo" id="titulo-metodologia">Cómo leer (y cómo no leer) estos datos</h2>
          <p class="seccion__entrada">Cinco advertencias que respeta cada gráfica y cada texto de este observatorio.
            Vienen del diccionario de datos del proyecto (<code>docs/diccionario_datos.md</code>).</p>
        </div>
      </header>

      <div class="rejilla-3">
        <article v-for="(a, i) in m.advertencias" :key="a.titulo" class="tarjeta advertencia">
          <h4><span>{{ i + 1 }}.</span>{{ a.titulo }}</h4>
          <p>{{ a.texto }}</p>
          <div class="no-si">
            <div class="no"><b>No se puede decir</b>{{ a.no }}</div>
            <div class="si"><b>Sí se puede decir</b>{{ a.si }}</div>
          </div>
        </article>
      </div>

      <div class="subtitulo-bloque"><h3>Fuentes</h3><p>Todas del INEGI. Ninguna cifra se publica sin fuente, año y nivel geográfico.</p></div>
      <div class="rejilla-2">
        <article v-for="f in m.fuentes" :key="f.clave" class="tarjeta fuente-ficha">
          <p class="antetitulo">{{ f.clave }}</p>
          <h4>{{ f.nombre }}</h4>
          <p>{{ f.que_mide }}</p>
          <p>Niveles: <insignia :nivel="f.niveles" /></p>
          <ul><li v-for="n in f.notas" :key="n">{{ n }}</li></ul>
        </article>
      </div>

      <div class="subtitulo-bloque"><h3>Glosario</h3></div>
      <dl class="glosario">
        <div v-for="g in m.glosario" :key="g.termino"><dt>{{ g.termino }}</dt><dd>{{ g.definicion }}</dd></div>
      </dl>

      <div class="subtitulo-bloque">
        <h3>Descarga los datos</h3>
        <p>Las nueve tablas del esquema <code>indicadores</code>, que son las únicas que lee este observatorio. También
          están en la API, documentada en <a href="/api/docs">/api/docs</a>.</p>
      </div>
      <ul class="descargas">
        <li v-for="t in tablas" :key="t.nombre" class="tarjeta">
          <span><code>{{ t.nombre }}</code><small>{{ t.descripcion }} · {{ ent(t.filas) }} filas</small></span>
          <a class="boton-texto" :href="'/api/indicadores/' + t.nombre + '.csv'" download><icono nombre="descarga" />CSV</a>
        </li>
      </ul>

      <div class="subtitulo-bloque"><h3>Estado de los datos</h3></div>
      <div class="tarjeta estado-sistema">
        <div class="estado-sistema__fila">
          <span class="semaforo" :class="{ 'semaforo--mal': !estado.controles_ok }">
            {{ estado.controles_ok ? 'Todas las cifras de control cuadran' : 'Hay cifras de control que no cuadran' }}
            ({{ cuadran }} de {{ estado.controles.length }})</span>
        </div>
        <p class="hallazgo__texto"><strong>Fuente activa:</strong> {{ estado.fuente === 'postgres' ? 'PostgreSQL' : 'Respaldo local' }} —
          {{ estado.detalle }}.</p>
        <p v-if="estado.aviso" class="hallazgo__texto" style="color:var(--tinta-2);margin-top:4px">{{ estado.aviso }}</p>
        <p class="hallazgo__texto" style="color:var(--tinta-2);margin:4px 0 14px">Cargado el {{ new Date(estado.cargado_en).toLocaleString('es-MX') }}.</p>
        <tabla-datos :columnas="controles.columnas" :filas="controles.filas" titulo="Cifras de control" />
      </div>
    </div>
  </section>`,
};
