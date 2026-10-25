// Mapa del territorio (Leaflet, global `L`): las AGEB como puntos coloreados por carga
// de cuidado, las zonas sin respaldo con un anillo y los establecimientos del DENUE.
//
// El punto de cada AGEB es APROXIMADO (mediana de los establecimientos del DENUE que
// caen dentro): por eso es un mapa de puntos y no de polígonos, y el hallazgo es
// exploratorio. Las coordenadas de los establecimientos sí son las reales del DENUE.

import { onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { ent, escapar, num, pct } from '../formato.js';
import { colorSecuencial } from '../tema.js';

// Mosaicos estándar de OpenStreetMap (sin clave). En css/estilos.css se pasan a escala
// de grises (y se invierten en tema oscuro) para que el mapa base no compita con los datos.
const TESELAS = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
const ATRIBUCION = '&copy; <a href="https://www.openstreetmap.org/copyright">colaboradores de OpenStreetMap</a>'
  + ' · Datos: INEGI';

/** Escala del mapa: recorta el extremo más claro para que ningún punto desaparezca. */
export function escalaMapa(t) {
  const p = t.oscuro ? [600, 550, 500, 450, 400, 350, 300, 250, 200, 150] : [200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700];
  return p.map((k) => t.violeta[k]);
}

function fila(etiqueta, valor) {
  return `<dt>${escapar(etiqueta)}</dt><dd>${escapar(valor)}</dd>`;
}

function popupAgeb(a) {
  const alerta = a.sin_respaldo
    ? '<p class="alerta">Alta carga y sin ningún servicio de respaldo a 1 km (exploratorio)</p>'
    : a.alta_carga ? '<p>AGEB de alta carga de cuidado</p>' : '';
  return `<div class="popup-ageb"><strong>AGEB ${escapar(a.cvegeo_ageb)}</strong><br>${escapar(a.alcaldia)}
    <dl>
      ${fila('Carga de cuidado directo', num(a.carga_directa_x100_mujeres))}
      ${fila('Mujeres de 15 a 59', ent(a.mujeres_15a59))}
      ${fila('Niñas y niños de 0 a 5', ent(a.pob_0a5))}
      ${fila('Discapacidad para el autocuidado', ent(a.pob_disc_autocuidado))}
      ${fila('Guarderías a 1 km', ent(a.guarderias_1km))}
      ${fila('Servicios de respaldo a 1 km', ent(a.respaldo_total_1km))}
      ${fila('Hogares con jefatura femenina', pct(a.pct_hog_jefa))}
    </dl>${alerta}
    <p style="margin-top:6px;color:var(--tinta-3);font-size:.76rem">Ubicación aproximada del AGEB.</p></div>`;
}

function popupEstablecimiento(e) {
  return `<div class="popup-ageb"><strong>${escapar(e.nom_estab || 'Sin nombre registrado')}</strong><br>
    ${escapar(e.tipo)} · ${escapar(e.sector)}
    <dl>
      ${fila('Alcaldía', e.alcaldia)}
      ${fila('Personal ocupado', e.per_ocu || '—')}
      ${fila('Cuenta como respaldo', e.es_respaldo ? 'Sí' : 'No')}
    </dl>
    <p style="margin-top:6px;color:var(--tinta-3);font-size:.76rem">El personal ocupado no es capacidad de atención.</p></div>`;
}

export default {
  name: 'MapaAgeb',
  props: {
    agebs: { type: Array, required: true },
    establecimientos: { type: Array, required: true },
    seleccion: { type: String, default: null },
    capas: { type: Object, required: true },
    tokens: { type: Object, required: true },
  },
  setup(props) {
    const el = ref(null);
    let mapa = null;
    let base = null;
    let lienzos = null; // un renderizador de canvas por panel, creado una sola vez
    const grupos = {};
    const marcas = { agebs: [], sinRespaldo: [], respaldo: [], otros: [] };
    let rango = { min: 0, max: 1 };

    function estiloAgeb(a) {
      const t = props.tokens;
      const fuera = props.seleccion && a.cve_mun !== props.seleccion;
      return {
        radius: 5,
        fillColor: colorSecuencial(a.carga_directa_x100_mujeres, rango.min, rango.max, escalaMapa(t)),
        fillOpacity: fuera ? 0.18 : 0.95,
        color: t.superficie,
        weight: 1,
        opacity: fuera ? 0.2 : 1,
      };
    }
    function estiloAnillo(a) {
      const fuera = props.seleccion && a.cve_mun !== props.seleccion;
      return { radius: 9, fill: false, color: props.tokens.critico, weight: 2.5, opacity: fuera ? 0.25 : 1 };
    }
    function estiloEstablecimiento(e) {
      const t = props.tokens;
      const fuera = props.seleccion && e.cve_mun !== props.seleccion;
      return e.es_respaldo
        ? { radius: 3.5, fillColor: t.tinta1, fillOpacity: fuera ? 0.25 : 0.9, color: t.superficie, weight: 1, opacity: fuera ? 0.25 : 1 }
        : { radius: 3.5, fill: false, color: t.tinta2, weight: 1.3, opacity: fuera ? 0.25 : 0.9 };
    }

    function construir() {
      Object.values(grupos).forEach((g) => g.clearLayers());
      Object.keys(marcas).forEach((k) => { marcas[k] = []; });
      const valores = props.agebs.map((a) => a.carga_directa_x100_mujeres).filter((v) => v !== null);
      rango = { min: Math.min(...valores), max: Math.max(...valores) };
      const { agebs: rAgebs, establecimientos: rEst, alertas: rAlertas } = lienzos;

      for (const a of props.agebs) {
        if (a.lat === null || a.lon === null) continue;
        const m = L.circleMarker([a.lat, a.lon], { ...estiloAgeb(a), renderer: rAgebs });
        m.bindTooltip(`${escapar(a.alcaldia)} · carga ${num(a.carga_directa_x100_mujeres)}`, { direction: 'top', offset: [0, -4] });
        m.bindPopup(() => popupAgeb(a), { maxWidth: 280 });
        m.datos = a;
        grupos.agebs.addLayer(m);
        marcas.agebs.push(m);
        if (a.sin_respaldo) {
          const r = L.circleMarker([a.lat, a.lon], { ...estiloAnillo(a), renderer: rAlertas });
          r.bindTooltip(`Sin respaldo a 1 km · ${escapar(a.alcaldia)}`, { direction: 'top', offset: [0, -6] });
          r.bindPopup(() => popupAgeb(a), { maxWidth: 280 });
          r.datos = a;
          grupos.sinRespaldo.addLayer(r);
          marcas.sinRespaldo.push(r);
        }
      }
      for (const e of props.establecimientos) {
        if (e.lat === null || e.lon === null) continue;
        const m = L.circleMarker([e.lat, e.lon], { ...estiloEstablecimiento(e), renderer: rEst });
        m.bindTooltip(`${escapar(e.tipo)} · ${escapar(e.sector)}`, { direction: 'top', offset: [0, -4] });
        m.bindPopup(() => popupEstablecimiento(e), { maxWidth: 280 });
        m.datos = e;
        (e.es_respaldo ? grupos.respaldo : grupos.otros).addLayer(m);
        marcas[e.es_respaldo ? 'respaldo' : 'otros'].push(m);
      }
    }

    function reestilizar() {
      marcas.agebs.forEach((m) => m.setStyle(estiloAgeb(m.datos)));
      marcas.sinRespaldo.forEach((m) => m.setStyle(estiloAnillo(m.datos)));
      [...marcas.respaldo, ...marcas.otros].forEach((m) => m.setStyle(estiloEstablecimiento(m.datos)));
    }

    function encuadrar() {
      const puntos = props.agebs
        .filter((a) => (!props.seleccion || a.cve_mun === props.seleccion) && a.lat !== null)
        .map((a) => [a.lat, a.lon]);
      if (puntos.length) mapa.fitBounds(L.latLngBounds(puntos), { padding: [24, 24], maxZoom: 14 });
    }

    function aplicarCapas() {
      const c = props.capas;
      const poner = (capa, visible) => {
        if (visible && !mapa.hasLayer(capa)) capa.addTo(mapa);
        if (!visible && mapa.hasLayer(capa)) mapa.removeLayer(capa);
      };
      poner(grupos.agebs, c.carga);
      poner(grupos.sinRespaldo, c.sinRespaldo);
      poner(grupos.respaldo, c.respaldo);
      poner(grupos.otros, c.otros);
      poner(base, c.base);
    }

    onMounted(() => {
      mapa = L.map(el.value, {
        center: [19.36, -99.13], zoom: 10, minZoom: 9, maxZoom: 17,
        scrollWheelZoom: false, zoomSnap: 0.5,
      });
      mapa.attributionControl.setPrefix('<a href="https://leafletjs.com">Leaflet</a>');
      // La rueda del ratón solo hace zoom después de hacer clic en el mapa, para que no
      // secuestre el desplazamiento de la página.
      mapa.on('click', () => mapa.scrollWheelZoom.enable());
      mapa.on('mouseout', () => mapa.scrollWheelZoom.disable());
      lienzos = {};
      for (const [nombre, z] of [['agebs', 410], ['establecimientos', 420], ['alertas', 430]]) {
        mapa.createPane(nombre).style.zIndex = z;
        lienzos[nombre] = L.canvas({ pane: nombre, padding: 0.3 });
      }
      base = L.tileLayer(TESELAS, { attribution: ATRIBUCION, maxZoom: 19 });
      grupos.agebs = L.layerGroup();
      grupos.sinRespaldo = L.layerGroup();
      grupos.respaldo = L.layerGroup();
      grupos.otros = L.layerGroup();
      construir();
      aplicarCapas();
      encuadrar();
    });

    watch(() => [props.agebs, props.establecimientos], () => { if (mapa) { construir(); aplicarCapas(); } });
    watch(() => props.seleccion, () => { if (mapa) { reestilizar(); encuadrar(); } });
    watch(() => props.tokens, () => { if (mapa) reestilizar(); });
    watch(() => ({ ...props.capas }), () => { if (mapa) aplicarCapas(); });

    onBeforeUnmount(() => { mapa?.remove(); mapa = null; });
    return { el };
  },
  template: `<div ref="el" class="mapa" role="region"
    aria-label="Mapa de las AGEB de la Ciudad de México por carga de cuidado y de los establecimientos de cuidado"></div>`,
};
