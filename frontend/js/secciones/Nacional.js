// 01 · México. Lo general: el cuidado en todo el país (ENUT 2024, nacional) y la
// relación de las cuidadoras con los servicios (ENASIC 2022, que SOLO es nacional).

import { computed } from 'vue';
import Grafica from '../componentes/Grafica.js';
import TarjetaGrafica from '../componentes/TarjetaGrafica.js';
import { Aviso, Hallazgo, Indicador, Insignia, Medidor, NotaFuente } from '../componentes/base.js';
import { ejeHoras, ejePct, horas, num, pct } from '../formato.js';
import { barrasComparadas } from '../graficas.js';
import { corta } from '../estado.js';

const TOTAL = 'Cuidado a integrantes del hogar (total)';

export default {
  name: 'SeccionNacional',
  components: { Grafica, TarjetaGrafica, Aviso, Hallazgo, Indicador, Insignia, Medidor, NotaFuente },
  props: { d: { type: Object, required: true }, t: { type: Object, required: true } },
  setup(props) {
    const nacional = computed(() => props.d.enutActividad.filas.filter((f) => f.ambito === 'Nacional'));
    const mujeres = computed(() => nacional.value.filter((f) => f.sexo === 'Mujeres'));
    const hombre = (actividad) => nacional.value.find((f) => f.sexo === 'Hombres' && f.actividad === actividad);
    const total = computed(() => mujeres.value.find((f) => f.actividad === TOTAL));
    const totalH = computed(() => hombre(TOTAL));

    const categorias = computed(() => mujeres.value.map((f) => corta(f.actividad)));
    const series = (campo) => [
      { nombre: 'Mujeres', valores: mujeres.value.map((f) => f[campo]), color: props.t.acento, etiquetar: true },
      { nombre: 'Hombres (referencia)', valores: mujeres.value.map((f) => hombre(f.actividad)?.[campo]), color: props.t.referencia },
    ];
    const opcionPct = computed(() => barrasComparadas(props.t, {
      categorias: categorias.value, series: series('pct_realiza'), formato: (v) => pct(v),
      formatoEje: ejePct, max: 100,
    }));
    const opcionHoras = computed(() => barrasComparadas(props.t, {
      categorias: categorias.value, series: series('horas_semana'), formato: (v) => horas(v),
      formatoEje: ejeHoras,
    }));
    const tablaEnut = computed(() => ({
      columnas: [
        { clave: 'actividad', etiqueta: 'Actividad' },
        { clave: 'pct_m', etiqueta: '% mujeres que lo realiza', numerica: true, formato: (v) => pct(v) },
        { clave: 'pct_h', etiqueta: '% hombres (ref.)', numerica: true, formato: (v) => pct(v) },
        { clave: 'h_m', etiqueta: 'h/semana mujeres', numerica: true, formato: (v) => horas(v) },
        { clave: 'h_h', etiqueta: 'h/semana hombres (ref.)', numerica: true, formato: (v) => horas(v) },
        { clave: 'n', etiqueta: 'Casos (mujeres)', numerica: true, formato: (v) => num(v, 0) },
      ],
      filas: mujeres.value.map((m) => {
        const h = hombre(m.actividad);
        return { actividad: m.actividad, pct_m: m.pct_realiza, pct_h: h?.pct_realiza,
          h_m: m.horas_semana, h_h: h?.horas_semana, n: m.n_muestral };
      }),
    }));

    // --- ENASIC: cada tema con su propia base (los % no se comparan entre temas).
    const temas = computed(() => Object.fromEntries(props.d.enasic.temas.map((x) => [x.tema, x])));
    const fuenteEnasic = computed(() => props.d.enasic.fuente);
    const busco = computed(() => temas.value['Búsqueda de servicios']?.filas
      .find((f) => f.categoria === 'Sí buscó')?.pct);
    const noBusco = computed(() => temas.value['Búsqueda de servicios']?.filas
      .find((f) => f.categoria === 'No buscó')?.pct);
    const casa = computed(() => temas.value['Preferencia de cuidado']?.filas
      .find((f) => f.categoria === 'En su casa')?.pct);

    const barrasTema = (tema) => {
      const filas = temas.value[tema]?.filas ?? [];
      return barrasComparadas(props.t, {
        categorias: filas.map((f) => f.categoria),
        series: [{ nombre: '% de mujeres cuidadoras', valores: filas.map((f) => f.pct), color: props.t.acento, etiquetar: true }],
        formato: (v) => pct(v),
        formatoEje: ejePct,
        anchoEtiqueta: 175,
      });
    };
    const tablaTema = (tema) => ({
      columnas: [
        { clave: 'categoria', etiqueta: 'Respuesta' },
        { clave: 'pct', etiqueta: '%', numerica: true, formato: (v) => pct(v) },
      ],
      filas: temas.value[tema]?.filas ?? [],
    });
    // Misma altura para las dos gráficas de la fila: las barras de la más corta respiran.
    const altoEnasic = computed(() => 40 + Math.max(...props.d.enasic.temas.map((x) => x.filas.length)) * 34);
    const opcionRazones = computed(() => barrasTema('Razones para no buscar'));
    const opcionPreferencia = computed(() => barrasTema('Preferencia de cuidado'));
    const tablaRazones = computed(() => tablaTema('Razones para no buscar'));
    const tablaPreferencia = computed(() => tablaTema('Preferencia de cuidado'));

    const hallazgos = computed(() => props.d.hallazgos.nacional.hallazgos);
    const hEnut = computed(() => hallazgos.value.filter((h) => h.fuente.includes('ENUT')));
    const hEnasic = computed(() => hallazgos.value.filter((h) => h.fuente.includes('ENASIC')));

    return {
      total, totalH, opcionPct, opcionHoras, tablaEnut, temas, fuenteEnasic, busco, noBusco, casa,
      opcionRazones, opcionPreferencia, tablaRazones, tablaPreferencia, altoEnasic, hEnut, hEnasic,
      pct, horas,
    };
  },
  template: `<section class="seccion" id="mexico" aria-labelledby="titulo-mexico">
    <div class="contenedor">
      <header class="seccion__cabeza">
        <span class="seccion__numero" aria-hidden="true">01</span>
        <div>
          <p class="seccion__escala">Escala nacional <insignia nivel="Nacional" /></p>
          <h2 class="seccion__titulo" id="titulo-mexico">México: el cuidado que sostienen las mujeres</h2>
          <p class="seccion__entrada">El trabajo de cuidado no remunerado —atender a niñas y niños, a personas
            mayores, enfermas o con discapacidad— es una parte de la economía que no se paga ni aparece en los
            salarios, y recae sobre todo en las mujeres. Así se ve en todo el país.</p>
          <p class="seccion__fuentes">Fuentes: INEGI, ENUT 2024 (nacional) · INEGI, ENASIC 2022 (nacional)</p>
        </div>
      </header>

      <div class="indicadores">
        <indicador etiqueta="Mujeres de 12 años y más que cuidan a integrantes de su hogar"
          :valor="pct(total?.pct_realiza)" :contexto="'Hombres (referencia): ' + pct(totalH?.pct_realiza)"
          nivel="Nacional" fuente="INEGI, ENUT 2024" />
        <indicador etiqueta="Horas a la semana que dedican las que cuidan"
          :valor="horas(total?.horas_semana)" :contexto="'Hombres que cuidan (referencia): ' + horas(totalH?.horas_semana)"
          nivel="Nacional" fuente="INEGI, ENUT 2024" />
        <indicador etiqueta="Mujeres cuidadoras que buscó un servicio de cuidado"
          :valor="pct(busco)" contexto="Guardería, casa de día o asilo."
          nivel="Nacional" fuente="INEGI, ENASIC 2022" />
        <indicador etiqueta="Mujeres cuidadoras que preferiría el cuidado en casa"
          :valor="pct(casa)" contexto="Si tuviera que contratar un servicio."
          nivel="Nacional" fuente="INEGI, ENASIC 2022" />
      </div>

      <div class="subtitulo-bloque">
        <h3>Quiénes cuidan y cuánto tiempo</h3>
        <p>Porcentaje de la población de 12 años y más que realiza cada tipo de cuidado, y horas a la semana que
          le dedica quien lo realiza. Los hombres aparecen solo como referencia para medir la brecha.</p>
      </div>
      <div class="leyenda" aria-hidden="true">
        <span class="leyenda__item"><span class="leyenda__muestra" :style="{ background: t.acento }"></span>Mujeres</span>
        <span class="leyenda__item"><span class="leyenda__muestra" :style="{ background: t.referencia }"></span>Hombres (referencia)</span>
      </div>
      <div class="rejilla-2">
        <tarjeta-grafica titulo="Qué porcentaje cuida, por tipo de cuidado"
          subtitulo="% de la población de 12 años y más que realiza la actividad."
          fuente="INEGI, ENUT 2024" nivel="Nacional" :tabla="tablaEnut">
          <grafica :opcion="opcionPct" :alto="300" etiqueta="Porcentaje de mujeres y hombres que realizan cada tipo de cuidado en México" />
        </tarjeta-grafica>
        <tarjeta-grafica titulo="Cuántas horas a la semana le dedican"
          subtitulo="Promedio entre quienes realizan la actividad (no entre toda la población)."
          fuente="INEGI, ENUT 2024" nivel="Nacional" :tabla="tablaEnut">
          <grafica :opcion="opcionHoras" :alto="300" etiqueta="Horas a la semana de cuidado por tipo, mujeres y hombres, México" />
        </tarjeta-grafica>
      </div>
      <div class="hallazgos separacion">
        <hallazgo v-for="h in hEnut" :key="h.clave" :h="h" />
      </div>

      <div class="subtitulo-bloque">
        <h3>Las cuidadoras y los servicios de cuidado</h3>
        <insignia nivel="Nacional" />
      </div>
      <aviso tipo="nacional">
        <strong>Cifras solo nacionales.</strong> Los microdatos públicos de la ENASIC 2022 no traen entidad ni
        municipio: estas cifras describen a las cuidadoras de todo el país y no se pueden atribuir a la Ciudad de
        México ni ponerse en un mapa. Cada gráfica indica su base, porque cambia entre preguntas.
      </aviso>

      <div class="rejilla-2 separacion">
        <div class="tarjeta tarjeta-grafica">
          <h4 class="tarjeta-grafica__titulo">¿Buscaron un servicio de cuidado?</h4>
          <p class="tarjeta-grafica__subtitulo">Base: {{ temas['Búsqueda de servicios']?.base }}
            ({{ temas['Búsqueda de servicios']?.variable_enasic }}).</p>
          <div class="pila" style="margin-top:16px">
            <medidor etiqueta="Buscó una guardería, casa de día o asilo" :valor="busco" :texto="pct(busco)" />
            <medidor etiqueta="No buscó" :valor="noBusco" :texto="pct(noBusco)" />
          </div>
          <nota-fuente :fuente="fuenteEnasic" nivel="Nacional" />
        </div>
        <div class="tarjeta tarjeta-grafica">
          <h4 class="tarjeta-grafica__titulo">¿Cuidarían a cambio de un pago?</h4>
          <p class="tarjeta-grafica__subtitulo">Base: {{ temas['Disposición a cuidar']?.base }}
            ({{ temas['Disposición a cuidar']?.variable_enasic }}).</p>
          <div class="pila" style="margin-top:16px">
            <medidor v-for="f in temas['Disposición a cuidar']?.filas ?? []" :key="f.categoria"
              :etiqueta="f.categoria" :valor="f.pct" :texto="pct(f.pct)" />
          </div>
          <nota-fuente :fuente="fuenteEnasic" nivel="Nacional" />
        </div>
      </div>

      <div class="rejilla-2 separacion">
        <tarjeta-grafica titulo="¿Por qué no buscaron un servicio?"
          :subtitulo="'Base: ' + temas['Razones para no buscar']?.base + '. Respuesta múltiple: los porcentajes no suman 100.'"
          :fuente="fuenteEnasic" nivel="Nacional" :tabla="tablaRazones">
          <grafica :opcion="opcionRazones" :alto="altoEnasic"
            etiqueta="Razones de las mujeres cuidadoras para no buscar servicios de cuidado, nacional" />
        </tarjeta-grafica>
        <tarjeta-grafica titulo="Si contrataran un servicio, ¿dónde lo preferirían?"
          :subtitulo="'Base: ' + temas['Preferencia de cuidado']?.base + '. Una sola respuesta: suma 100 %.'"
          :fuente="fuenteEnasic" nivel="Nacional" :tabla="tablaPreferencia">
          <grafica :opcion="opcionPreferencia" :alto="altoEnasic"
            etiqueta="Dónde preferirían las mujeres cuidadoras un servicio de cuidado, nacional" />
        </tarjeta-grafica>
      </div>
      <div class="hallazgos separacion">
        <hallazgo v-for="h in hEnasic" :key="h.clave" :h="h" />
      </div>
    </div>
  </section>`,
};
