// Portada: la pregunta rectora, la cifra con la que el equipo acordó encabezar
// (la brecha de trabajo no pagado, con la jornada total como apoyo) y la escalera
// de escalas que ordena el resto de la página, de lo general a lo particular.

import { computed } from 'vue';
import { Icono, Insignia, NotaFuente } from '../componentes/base.js';
import { ent, horas, num, pct } from '../formato.js';

export default {
  name: 'Portada',
  components: { Icono, Insignia, NotaFuente },
  props: { d: { type: Object, required: true } },
  setup(props) {
    const kpi = (clave) => props.d.kpis.filas.find((f) => f.clave === clave);
    const brecha = computed(() => props.d.dobleJornada.brecha_trabajo_no_pagado_h);
    const jornada = computed(() => props.d.dobleJornada.filas
      .find((f) => f.grupo === 'Mujeres ocupadas')?.horas_jornada_total);

    const escalas = computed(() => {
      const enut = props.d.enutActividad.filas;
      const nac = enut.find((f) => f.ambito === 'Nacional' && f.sexo === 'Mujeres'
        && f.actividad === 'Cuidado a integrantes del hogar (total)');
      const cdmx = kpi('ENUT · % mujeres CDMX que cuidan');
      const horasCdmx = kpi('ENUT · h/semana mujeres que cuidan');
      const cargaCdmx = kpi('Censo · carga directa x100 mujeres, CDMX');
      const alc = [...props.d.alcaldias.filas]
        .sort((a, b) => b.carga_directa_x100_mujeres - a.carga_directa_x100_mujeres)[0];
      const embudo = props.d.territorio.embudo;
      const sin = embudo[embudo.length - 1];
      return [
        {
          numero: '01', escala: 'México', ancla: 'mexico', valor: pct(nac?.pct_realiza),
          texto: 'de las mujeres de 12 años y más del país cuida a integrantes de su hogar.',
          nivel: 'Nacional', fuente: 'ENUT 2024',
        },
        {
          numero: '02', escala: 'Ciudad de México', ancla: 'cdmx', valor: pct(cdmx?.valor_num),
          texto: `de las mujeres de la ciudad cuida; las que cuidan le dedican ${horas(horasCdmx?.valor_num)} a la semana.`,
          nivel: 'CDMX', fuente: 'ENUT 2024',
        },
        {
          numero: '03', escala: 'Alcaldías', ancla: 'alcaldias', valor: num(alc?.carga_directa_x100_mujeres),
          texto: `personas que necesitan cuidado directo por cada 100 mujeres de 15 a 59 en ${alc?.alcaldia}, la carga más alta (ciudad: ${num(cargaCdmx?.valor_num)}).`,
          nivel: 'Alcaldía', fuente: 'Censo 2020',
        },
        {
          numero: '04', escala: 'AGEB', ancla: 'territorio', valor: ent(sin?.mujeres_15a59),
          texto: `mujeres de 15 a 59 viven en ${ent(sin?.agebs)} AGEB de alta carga sin guardería, residencia ni centro de día a 1 km.`,
          nivel: 'AGEB', fuente: 'Censo 2020 + DENUE', exploratorio: true,
        },
      ];
    });

    return { brecha, jornada, escalas, num };
  },
  template: `<section class="portada" id="inicio" aria-labelledby="titulo-portada">
    <div class="contenedor portada__rejilla">
      <div>
        <p class="antetitulo">Economía del cuidado · México y Ciudad de México</p>
        <h1 id="titulo-portada">Cuidar también es trabajo</h1>
        <p class="portada__entrada">Este observatorio mide dónde y cuánto trabajo de cuidado no remunerado
          recae sobre las mujeres —del país a la Ciudad de México, de la ciudad a cada alcaldía y de ahí a cada
          AGEB— y qué tanto lo alivia la oferta de cuidados que tienen cerca.</p>
        <p class="portada__pregunta"><span>Pregunta rectora</span>{{ d.metodologia.pregunta_rectora }}</p>
      </div>
      <aside class="cifra-heroe tarjeta" aria-label="Cifra principal del observatorio">
        <p class="cifra-heroe__antes">Las mujeres ocupadas de la Ciudad de México hacen</p>
        <p class="cifra-heroe__valor">+{{ num(brecha) }}<span>h</span></p>
        <p class="cifra-heroe__despues">más de trabajo no pagado <strong>cada semana</strong> que los hombres
          ocupados (referencia): trabajo doméstico y cuidado de su propio hogar.</p>
        <p class="cifra-heroe__apoyo">Sumando el trabajo pagado, su jornada total llega a
          <strong>{{ num(jornada) }} horas</strong> a la semana.</p>
        <nota-fuente fuente="INEGI, ENUT 2024" nivel="CDMX" />
      </aside>
    </div>
    <div class="contenedor">
      <h2 class="escalera__titulo">De lo general a lo particular</h2>
      <ol class="escalera">
        <li v-for="e in escalas" :key="e.ancla">
          <a :href="'#' + e.ancla" class="escalon tarjeta">
            <icono nombre="abajo" class="escalon__flecha" />
            <span class="escalon__nivel">{{ e.numero }} · {{ e.escala }}</span>
            <span class="escalon__valor">{{ e.valor }}</span>
            <span class="escalon__texto">{{ e.texto }}</span>
            <span class="escalon__pie">
              <insignia :nivel="e.nivel" />
              <span v-if="e.exploratorio" class="insignia insignia--exploratorio">Exploratorio</span>
              {{ e.fuente }}
            </span>
          </a>
        </li>
      </ol>
    </div>
  </section>`,
};
