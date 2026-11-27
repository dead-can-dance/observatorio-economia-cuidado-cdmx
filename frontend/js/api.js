// Cliente de la API del backend (FastAPI). Cada ruta se pide una sola vez por sesión.

const cache = new Map();

export function obtener(ruta) {
  if (!cache.has(ruta)) {
    const promesa = fetch(`/api${ruta}`, { headers: { Accept: 'application/json' } })
      .then(async (r) => {
        if (!r.ok) {
          let detalle = r.statusText;
          try { detalle = (await r.json()).detail ?? detalle; } catch { /* sin cuerpo JSON */ }
          throw new Error(`${r.status} en /api${ruta}: ${typeof detalle === 'string' ? detalle : JSON.stringify(detalle)}`);
        }
        return r.json();
      });
    // Un fallo no se queda en caché: el siguiente intento vuelve a pedirlo.
    promesa.catch(() => cache.delete(ruta));
    cache.set(ruta, promesa);
  }
  return cache.get(ruta);
}

const q = encodeURIComponent;

export const api = {
  estado: () => obtener('/estado'),
  metodologia: () => obtener('/metodologia'),
  kpis: () => obtener('/kpis'),
  hallazgos: (nivel) => obtener(`/hallazgos/${nivel}`),
  enutActividad: () => obtener('/enut/carga-actividad'),
  enutBrecha: () => obtener('/enut/brecha'),
  dobleJornada: () => obtener('/enut/doble-jornada'),
  porGrupo: (tipo) => obtener(`/enut/cuidado-por-grupo?tipo_grupo=${q(tipo)}`),
  enasic: () => obtener('/enasic'),
  alcaldias: () => obtener('/alcaldias'),
  alcaldia: (cve) => obtener(`/alcaldias/${q(cve)}`),
  agebs: () => obtener('/agebs'),
  establecimientos: () => obtener('/establecimientos'),
  territorio: (cve) => obtener(cve ? `/territorio?cve_mun=${q(cve)}` : '/territorio'),
};
