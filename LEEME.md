# PP7 · Observatorio de la Economía del Cuidado — paquete de exploración

**Fecha:** 1-oct-2026 · Detalle completo en Notion (WORKFLOW, RECURSOS, DOCUMENTACIÓN).

## Qué hay aquí

| Archivo | Qué es |
|---|---|
| `02_mujeres_cuidadoras_pp7.ipynb` | **Notebook principal.** Exploración enfocada en la mujer cuidadora. De aquí salen los 3 hallazgos candidatos. |
| `exploracion_fuentes_pp7.ipynb` | Anexo. Primera exploración general de las 4 fuentes (oferta, demanda, validaciones). Sirve de referencia, pero el enfoque del proyecto es el del notebook 02. |
| `data/curada/` | Tablas ya limpias que generan los notebooks (CSV). Sirven para revisar resultados sin correr nada. |
| `figuras/` | Gráficas generadas. |

Los datos crudos del INEGI **no vienen en el paquete** (pesan ~80 MB). La primera celda de cada notebook los descarga sola a `data/raw/`.

## Cómo correrlo

1. Python 3.10 o más reciente, con: `pip install pandas numpy matplotlib scikit-learn jupyter`
2. Abrir el notebook desde esta carpeta (para que encuentre `data/`) y ejecutar todo de arriba abajo.
3. La primera vez tarda unos minutos por la descarga.

## La regla del análisis

La unidad de análisis es **la mujer cuidadora**. Pregunta rectora: *¿dónde y cuánto trabajo de cuidado recae sobre las mujeres de la CDMX, y qué tanto lo alivia la oferta de cuidados que tienen cerca?*
Los hombres solo aparecen como referencia para dimensionar la brecha, nunca como tema.

## Hallazgos candidatos (todavía no validados)

- **A · Doble jornada (ENUT 2024, CDMX):** mujeres ocupadas 77 h/semana entre trabajo pagado y no pagado; hombres ocupados 73.5 h (referencia).
- **B · Mujeres que cuidan sin respaldo (Censo 2020 + DENUE 05/2026):** 88 AGEB con carga alta y ninguna guardería, residencia ni centro de día a 1 km; ≈125 mil mujeres de 15 a 59. Iztapalapa concentra la mayor cantidad.
- **C · No usan servicios formales y prefieren cuidado en casa (ENASIC 2022, nacional):** 3.2% buscó un servicio; 61.2% lo preferiría en casa; 44.4% trabajaría como cuidadora pagada.

## Qué le toca a cada quien

| Persona | Fuente | Tarea | Para cerrar |
|---|---|---|---|
| Fabián | DENUE + arquitectura | Ficha técnica del DENUE; pasar los notebooks a scripts que carguen PostgreSQL (capas cruda, curada, indicadores); demo de PySpark en Docker | Herramientas |
| Karen | Censo 2020 | Ficha técnica; sustituir los centroides aproximados por los polígonos del Marco Geoestadístico del INEGI y recalcular las zonas sin respaldo (hallazgo B) | Analítica |
| Edwin | ENUT 2024 | Ficha técnica; márgenes de error con el diseño muestral (`est_dis`, `upm_dis`, `fac_per`) para el hallazgo A; fichas de indicador estilo SICCDMX | Inteligencia de Negocios |
| Vilchis | ENASIC 2022 + marco legal | Ficha técnica; profundizar preferencias y disposición a cuidar (hallazgo C, insumo del programa); arrancar el dictamen jurídico | Leyes y Práctica Profesional |

**Ficha técnica mínima por fuente:** origen y liga de descarga, versión y fecha, nivel geográfico, tamaño de muestra o cobertura, variables que usamos, limitaciones, y cómo validamos (qué cifra oficial reproducimos).

## Cuidados al citar cifras

- Las zonas sin respaldo usan ubicaciones aproximadas hasta que se integre el Marco Geoestadístico.
- El DENUE cuenta establecimientos, no lugares disponibles: no hablar de "cobertura".
- ENASIC no permite separar la CDMX: sus cifras son nacionales.
- Algunas cifras de la ENUT para la CDMX salen de menos de 100 casos; el notebook las marca.
