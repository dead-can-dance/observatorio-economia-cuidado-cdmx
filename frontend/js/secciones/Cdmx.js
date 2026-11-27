// 02 · Ciudad de México. La doble jornada (hallazgo A), la ciudad frente al país, la
// brecha por actividad y qué mujeres cuidan más (ENUT 2024, nivel CDMX).

import { computed, ref } from 'vue';
import Grafica from '../componentes/Grafica.js';
import TarjetaGrafica from '../componentes/TarjetaGrafica.js';
import { Hallazgo, Indicador, Insignia, NotaFuente } from '../componentes/base.js';
import { corta } from '../estado.js';
import { ejeHoras, ejePct, horas, num, pct } from '../formato.js';
import { barraApilada, barrasComparadas, barrasConReferencia, columnas } from '../graficas.js';

export default {
  name: 'SeccionCdmx',
  components: { Grafica, TarjetaGrafica, Hallazgo, Indicador, Insignia, NotaFuente },
  props: { d: { type: Object, required: true }, t: { type: Object, required: true } },
  setup(props) {
    const kpi = (clave) => props.d.kpis.filas.find((f) => f.clave === clave)?.valor_num;

    // --- Hallazgo A: la doble jornada -----------------------------------------
    const jornada = computed(() => props.d.dobleJornada.filas);
    const muj = computed(() => jornada.value.find((f) => f.grupo === 'Mujeres ocupadas'));
    const hom = computed(() => jornada.value.find((f) => f.grupo !== 'Mujeres ocupadas'));
    const componentes = computed(() => [
      { clave: 'horas_trabajo_mercado', nombre: 'Trabajo para el mercado (pagado)', color: props.t.mercado },
      { clave: 'horas_trabajo_domestico', nombre: 'Trabajo doméstico no remunerado', color: props.t.domestico },
      { clave: 'horas_cuidado', nombre: 'Cuidado no remunerado', color: props.t.cuidado },
    ]);
    const anchoJornada = ref(0);
    const opcionJornada = computed(() => barraApilada(props.t, {
      ancho: anchoJornada.value,
      categorias: jornada.value.map((f) => f.grupo),
      categoriasCortas: jornada.value.map((f) => (f.grupo === 'Mujeres ocupadas' ? 'Mujeres' : 'Hombres (ref.)')),
      segmentos: componentes.value.map((c) => ({
        nombre: c.nombre, color: c.color, valores: jornada.value.map((f) => f[c.clave]),
      })),
      totales: jornada.value.map((f) => f.horas_jornada_total),
      formato: (v) => horas(v),
      formatoEje: ejeHoras,
    }));

    // --- La ciudad frente al país (mujeres) -------------------------------------
    const enut = computed(() => props.d.enutActividad.filas.filter((f) => f.sexo === 'Mujeres'));
    const cdmx = computed(() => enut.value.filter((f) => f.ambito === 'CDMX'));
    const nacional = (actividad) => enut.value.find((f) => f.ambito === 'Nacional' && f.actividad === actividad);
    const categoriasPais = computed(() => cdmx.value.map((f) => corta(f.actividad) + (f.precision_baja ? ' *' : '')));
    const notasPais = computed(() => cdmx.value.map((f) => (f.precision_baja
      ? `En la CDMX la cifra sale de ${f.n_muestral} casos: es frágil, solo un indicio.` : '')));
    const seriesPais = (campo) => [
      { nombre: 'Ciudad de México', color: props.t.acento, etiquetar: true,
        valores: cdmx.value.map((f) => f[campo]), fragiles: cdmx.value.map((f) => f.precision_baja) },
      { nombre: 'Nacional (contexto)', color: props.t.referencia,
        valores: cdmx.value.map((f) => nacional(f.actividad)?.[campo]) },
    ];
    const opcionPaisPct = computed(() => barrasComparadas(props.t, {
      categorias: categoriasPais.value, series: seriesPais('pct_realiza'),
      formato: (v) => pct(v), formatoEje: ejePct, max: 100, notas: notasPais.value,
    }));
    const opcionPaisHoras = computed(() => barrasComparadas(props.t, {
      categorias: categoriasPais.value, series: seriesPais('horas_semana'),
      formato: (v) => horas(v), formatoEje: ejeHoras, notas: notasPais.value,
    }));
    const tablaPais = computed(() => ({
      columnas: [
        { clave: 'actividad', etiqueta: 'Actividad (mujeres)' },
        { clave: 'pct_c', etiqueta: '% CDMX', numerica: true, formato: (v) => pct(v) },
        { clave: 'pct_n', etiqueta: '% nacional', numerica: true, formato: (v) => pct(v) },
        { clave: 'h_c', etiqueta: 'h/semana CDMX', numerica: true, formato: (v) => horas(v) },
        { clave: 'h_n', etiqueta: 'h/semana nacional', numerica: true, formato: (v) => horas(v) },
        { clave: 'n', etiqueta: 'Casos CDMX', numerica: true, formato: (v, f) => num(v, 0) + (f.fragil ? ' *' : '') },
      ],
      filas: cdmx.value.map((f) => {
        const n = nacional(f.actividad);
        return { actividad: f.actividad, pct_c: f.pct_realiza, pct_n: n?.pct_realiza, h_c: f.horas_semana,
          h_n: n?.horas_semana, n: f.n_muestral, fragil: f.precision_baja };
      }),
    }));

    // --- Brecha por actividad -----------------------------------------------------
    const brecha = computed(() => props.d.brecha.filas);
    const opcionBrecha = computed(() => barrasConReferencia(props.t, {
      categorias: brecha.value.map((f) => corta(f.actividad) + (f.n_mujeres < 100 ? ' *' : '')),
      valores: brecha.value.map((f) => f.horas_mujeres),
      referencias: brecha.value.map((f) => f.horas_hombres_ref),
      etiquetas: brecha.value.map((f) => `${horas(f.horas_mujeres)} · ${num(f.razon_mujeres_hombres, 2)}×`),
      fragiles: brecha.value.map((f) => f.n_mujeres < 100),
      notas: brecha.value.map((f) => `${pct(f.pct_realiza_mujeres)} de las mujeres lo realiza · razón ${num(f.razon_mujeres_hombres, 2)}`
        + (f.n_mujeres < 100 ? ` · solo ${f.n_mujeres} casos: cifra frágil` : '')),
      formato: (v) => horas(v),
      formatoEje: ejeHoras,
      nombrePrincipal: 'Mujeres que lo realizan',
      nombreReferencia: 'Hombres que lo realizan (referencia)',
    }));
    const tablaBrecha = computed(() => ({
      columnas: [
        { clave: 'actividad', etiqueta: 'Actividad' },
        { clave: 'pct_realiza_mujeres', etiqueta: '% de mujeres que lo realiza', numerica: true, formato: (v) => pct(v) },
        { clave: 'horas_mujeres', etiqueta: 'h/semana mujeres', numerica: true, formato: (v) => horas(v) },
        { clave: 'horas_hombres_ref', etiqueta: 'h/semana hombres (ref.)', numerica: true, formato: (v) => horas(v) },
        { clave: 'razon_mujeres_hombres', etiqueta: 'Mujeres / hombres', numerica: true, formato: (v) => num(v, 2) },
        { clave: 'n_mujeres', etiqueta: 'Casos (mujeres)', numerica: true, formato: (v) => num(v, 0) + (v < 100 ? ' *' : '') },
      ],
      filas: brecha.value,
    }));

    // --- ¿Qué mujeres cuidan más? Dos gráficas separadas: la misma población partida
    // de dos maneras, que nunca se mezclan ni se suman (diccionario de datos).
    const notaGrupo = (f) => `${pct(f.pct_que_cuida)} de las mujeres del grupo cuida · ${num(f.n_muestral, 0)} casos`
      + (f.confiable ? '' : ' · muestra chica: solo indicio');
    const marca = (f) => f.grupo + (f.confiable ? '' : ' †');
    const opcionEdad = computed(() => {
      const filas = props.d.porEdad.filas;
      return columnas(props.t, {
        categorias: filas.map(marca),
        valores: filas.map((f) => f.horas_cuidado),
        colores: props.t.ordinal,
        fragiles: filas.map((f) => !f.confiable),
        notas: filas.map(notaGrupo),
        formato: (v) => horas(v),
        formatoEje: ejeHoras,
        nombre: 'Horas de cuidado por mujer',
      });
    });
    // La condición de actividad no tiene orden propio: de más a menos horas.
    const condiciones = computed(() => [...props.d.porCondicion.filas]
      .sort((a, b) => b.horas_cuidado - a.horas_cuidado));
    const opcionCondicion = computed(() => barrasComparadas(props.t, {
      categorias: condiciones.value.map(marca),
      series: [{ nombre: 'Horas de cuidado por mujer', color: props.t.acento, etiquetar: true,
        valores: condiciones.value.map((f) => f.horas_cuidado),
        fragiles: condiciones.value.map((f) => !f.confiable) }],
      formato: (v) => horas(v),
      formatoEje: ejeHoras,
      notas: condiciones.value.map(notaGrupo),
      anchoEtiqueta: 150,
    }));
    const tablaGrupo = (titulo, filas) => ({
      columnas: [
        { clave: 'grupo', etiqueta: titulo },
        { clave: 'horas_cuidado', etiqueta: 'h/semana (promedio por mujer)', numerica: true, formato: (v) => horas(v) },
        { clave: 'pct_que_cuida', etiqueta: '% que cuida', numerica: true, formato: (v) => pct(v) },
        { clave: 'n_muestral', etiqueta: 'Casos', numerica: true, formato: (v, f) => num(v, 0) + (f.confiable ? '' : ' †') },
      ],
      filas,
    });
    const tablaEdad = computed(() => tablaGrupo('Grupo de edad', props.d.porEdad.filas));
    const tablaCondicion = computed(() => tablaGrupo('Condición de actividad', condiciones.value));
    const fragilesEdad = computed(() => props.d.porEdad.filas.some((f) => !f.confiable));
    const fragilesCondicion = computed(() => props.d.porCondicion.filas.some((f) => !f.confiable));

    const hallazgos = computed(() => props.d.hallazgos.cdmx.hallazgos);

    return {
      kpi, muj, hom, componentes, anchoJornada, opcionJornada, opcionPaisPct, opcionPaisHoras, tablaPais,
      opcionBrecha, tablaBrecha, opcionEdad, opcionCondicion, tablaEdad, tablaCondicion,
      fragilesEdad, fragilesCondicion, hallazgos, horas, pct, num,
    };
  },
  template: `<section class="seccion seccion--hundida" id="cdmx" aria-labelledby="titulo-cdmx">
    <div class="contenedor">
      <header class="seccion__cabeza">
        <span class="seccion__numero" aria-hidden="true">02</span>
        <div>
          <p class="seccion__escala">Escala de ciudad <insignia nivel="CDMX" /></p>
          <h2 class="seccion__titulo" id="titulo-cdmx">Ciudad de México: la doble jornada</h2>
          <p class="seccion__entrada">En la capital, la mayoría de las mujeres cuida y, cuando además tiene un empleo,
            su semana se alarga: al trabajo pagado se suman el trabajo doméstico y el cuidado de su propio hogar.</p>
          <p class="seccion__fuentes">Fuentes: INEGI, ENUT 2024 (representativa para la CDMX) · INEGI, Censo de Población y Vivienda 2020</p>
        </div>
      </header>

      <div class="indicadores">
        <indicador etiqueta="Mujeres de 12 años y más que cuidan a integrantes de su hogar"
          :valor="pct(kpi('ENUT · % mujeres CDMX que cuidan'))" nivel="CDMX" fuente="INEGI, ENUT 2024" />
        <indicador etiqueta="Horas a la semana que dedican las que cuidan"
          :valor="horas(kpi('ENUT · h/semana mujeres que cuidan'))"
          :contexto="'Hombres que cuidan (referencia): ' + horas(kpi('ENUT · ref. h/semana hombres que cuidan'))"
          nivel="CDMX" fuente="INEGI, ENUT 2024" />
        <indicador etiqueta="Jornada total de las mujeres ocupadas"
          :valor="horas(kpi('ENUT · jornada total mujeres ocupadas (h)'))"
          :contexto="'Hombres ocupados (referencia): ' + horas(kpi('ENUT · jornada total hombres ocupados (h, ref.)'))"
          nivel="CDMX" fuente="INEGI, ENUT 2024" />
        <indicador etiqueta="Personas que necesitan cuidado directo por cada 100 mujeres de 15 a 59"
          :valor="num(kpi('Censo · carga directa x100 mujeres, CDMX'))"
          contexto="Niñas y niños de 0 a 5 y personas con discapacidad para su autocuidado."
          nivel="CDMX" fuente="INEGI, Censo 2020" />
      </div>

      <div class="subtitulo-bloque">
        <h3>Hallazgo A · La doble jornada</h3>
        <p>Horas a la semana de las personas ocupadas, por tipo de trabajo. Promedio sobre todo el grupo, incluso
          quien no realiza la actividad: por eso los componentes suman la jornada total.</p>
      </div>
      <div class="rejilla-1-2">
        <div class="tarjeta tarjeta-grafica">
          <p class="indicador__etiqueta">Brecha de trabajo no pagado</p>
          <p class="indicador__valor" style="margin:6px 0">+{{ num(d.dobleJornada.brecha_trabajo_no_pagado_h) }}<span class="indicador__unidad">h a la semana</span></p>
          <p class="hallazgo__texto">Es lo que trabajan sin pago, de más, las mujeres ocupadas frente a los hombres
            ocupados (referencia): trabajo doméstico y cuidado de su propio hogar.</p>
          <p class="hallazgo__texto" style="margin-top:10px;color:var(--tinta-2)">Con el trabajo pagado, su semana suma
            <strong>{{ horas(muj?.horas_jornada_total) }}</strong>. La diferencia en la jornada total es menor y más
            frágil que la del trabajo no pagado, que es la cifra sólida.</p>
          <nota-fuente fuente="INEGI, ENUT 2024" nivel="CDMX" />
        </div>
        <tarjeta-grafica titulo="Jornada semanal de las personas ocupadas"
          :subtitulo="'Muestra: ' + num(muj?.n_muestral, 0) + ' mujeres y ' + num(hom?.n_muestral, 0) + ' hombres ocupados de la CDMX.'"
          fuente="INEGI, ENUT 2024" nivel="CDMX">
          <grafica :opcion="opcionJornada" :alto="170" @ancho="anchoJornada = $event"
            etiqueta="Doble jornada: horas de trabajo pagado, doméstico y de cuidado, mujeres y hombres ocupados de la CDMX" />
          <table class="tabla-leyenda">
            <thead><tr><th scope="col">Componente</th><th scope="col">Mujeres ocupadas</th><th scope="col">Hombres ocupados (ref.)</th></tr></thead>
            <tbody>
              <tr v-for="c in componentes" :key="c.clave">
                <th scope="row" style="font-weight:500"><span class="leyenda__item"><span class="leyenda__muestra" :style="{ background: c.color }"></span>{{ c.nombre }}</span></th>
                <td>{{ horas(muj?.[c.clave]) }}</td><td>{{ horas(hom?.[c.clave]) }}</td>
              </tr>
            </tbody>
            <tfoot><tr><td>Jornada total</td><td>{{ horas(muj?.horas_jornada_total) }}</td><td>{{ horas(hom?.horas_jornada_total) }}</td></tr></tfoot>
          </table>
          <template #notas>
            <span>La brecha de {{ num(d.dobleJornada.brecha_trabajo_no_pagado_h) }} h se calcula con los valores sin
              redondear; restar las cifras de un decimal de esta tabla da una décima menos.</span>
          </template>
        </tarjeta-grafica>
      </div>

      <div class="subtitulo-bloque">
        <h3>La ciudad frente al país</h3>
        <p>Mujeres de 12 años y más. El nivel nacional se muestra en gris, como contexto.</p>
      </div>
      <div class="leyenda" aria-hidden="true">
        <span class="leyenda__item"><span class="leyenda__muestra" :style="{ background: t.acento }"></span>Ciudad de México</span>
        <span class="leyenda__item"><span class="leyenda__muestra" :style="{ background: t.referencia }"></span>Nacional (contexto)</span>
      </div>
      <div class="rejilla-2">
        <tarjeta-grafica titulo="Qué porcentaje de las mujeres cuida" subtitulo="% de las mujeres de 12 años y más."
          fuente="INEGI, ENUT 2024" :nivel="['CDMX', 'Nacional']" :tabla="tablaPais">
          <grafica :opcion="opcionPaisPct" :alto="300" etiqueta="Porcentaje de mujeres que cuidan, CDMX y nacional" />
          <template #notas><span>* Cifra de la CDMX con menos de 100 casos: frágil, se muestra atenuada.</span></template>
        </tarjeta-grafica>
        <tarjeta-grafica titulo="Cuántas horas a la semana le dedican" subtitulo="Promedio entre las mujeres que realizan la actividad."
          fuente="INEGI, ENUT 2024" :nivel="['CDMX', 'Nacional']" :tabla="tablaPais">
          <grafica :opcion="opcionPaisHoras" :alto="300" etiqueta="Horas de cuidado a la semana de las mujeres, CDMX y nacional" />
          <template #notas><span>* Cifra de la CDMX con menos de 100 casos: frágil, se muestra atenuada.</span></template>
        </tarjeta-grafica>
      </div>

      <div class="subtitulo-bloque">
        <h3>Cuánto más cuidan las mujeres</h3>
        <p>Horas a la semana entre quienes realizan cada actividad. La barra es de las mujeres y el punto gris, de
          los hombres (referencia); la etiqueta dice cuántas veces las horas de ellas equivalen a las de ellos.</p>
      </div>
      <tarjeta-grafica titulo="Brecha de horas por actividad, Ciudad de México"
        subtitulo="Mujeres que realizan la actividad frente a hombres que la realizan (referencia)."
        fuente="INEGI, ENUT 2024" nivel="CDMX" :tabla="tablaBrecha">
        <div class="leyenda" aria-hidden="true">
          <span class="leyenda__item"><span class="leyenda__muestra" :style="{ background: t.acento }"></span>Mujeres que lo realizan</span>
          <span class="leyenda__item"><span class="leyenda__muestra leyenda__muestra--punto" :style="{ background: t.referencia }"></span>Hombres que lo realizan (referencia)</span>
        </div>
        <grafica :opcion="opcionBrecha" :alto="360" etiqueta="Horas de las mujeres y de los hombres por actividad de cuidado en la CDMX" />
        <template #notas><span>* Menos de 100 casos en la muestra: la cifra es frágil y se lee solo como indicio.</span></template>
      </tarjeta-grafica>

      <div class="subtitulo-bloque">
        <h3>¿Qué mujeres cuidan más?</h3>
        <p>Horas de cuidado a la semana, promedio por mujer del grupo, contando también a las que no cuidan (por eso
          son menores que en la brecha). Las dos vistas son la misma población partida de dos maneras: no se suman.</p>
      </div>
      <div class="rejilla-2">
        <tarjeta-grafica titulo="Por grupo de edad" subtitulo="Mujeres de 12 años y más de la CDMX."
          fuente="INEGI, ENUT 2024" nivel="CDMX" :tabla="tablaEdad">
          <grafica :opcion="opcionEdad" :alto="300" etiqueta="Horas de cuidado a la semana por grupo de edad, mujeres de la CDMX" />
          <template #notas v-if="fragilesEdad">
            <span>† Menos de 60 casos: la cifra no se cita como dato, solo como indicio. Se muestra atenuada.</span>
          </template>
        </tarjeta-grafica>
        <tarjeta-grafica titulo="Por condición de actividad" subtitulo="Mujeres de 12 años y más de la CDMX."
          fuente="INEGI, ENUT 2024" nivel="CDMX" :tabla="tablaCondicion">
          <grafica :opcion="opcionCondicion" :alto="300" etiqueta="Horas de cuidado a la semana por condición de actividad, mujeres de la CDMX" />
          <template #notas v-if="fragilesCondicion">
            <span>† Menos de 60 casos: la cifra no se cita como dato, solo como indicio. Se muestra atenuada.</span>
          </template>
        </tarjeta-grafica>
      </div>

      <div class="subtitulo-bloque"><h3>Lo que dicen los datos de la ciudad</h3></div>
      <div class="hallazgos">
        <hallazgo v-for="h in hallazgos" :key="h.clave" :h="h" />
      </div>
    </div>
  </section>`,
};
