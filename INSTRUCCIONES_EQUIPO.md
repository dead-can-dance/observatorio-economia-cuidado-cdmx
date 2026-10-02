# PP7 · Instrucciones por persona — semana del 1 al 8 de octubre de 2026

**Entrega:** jueves 8 de octubre, en la reunión de las 19:00. Todo lo que produzcan se sube a Notion (detalle al final de cada sección).
**Material:** `pp7_paquete_equipo.zip` (notebooks 01 y 02, tablas curadas, figuras y `LEEME.md`). Leer primero el `LEEME.md`.

---

## Antes de empezar (todos)

**1. Corran el notebook 02 completo una vez.** Abran `02_mujeres_cuidadoras_pp7.ipynb` desde la carpeta descomprimida y ejecuten todo. La primera celda descarga los datos del INEGI a `data/raw/` (unos minutos). Al final deben ver exactamente estas cifras; si alguna no coincide, avisen antes de seguir:

| Cifra de control | Valor esperado |
|---|---|
| % de mujeres de la CDMX que cuidan (ENUT) | 62.2 |
| Jornada total de mujeres ocupadas (ENUT) | 77.0 h |
| AGEB con carga alta y sin respaldo | 88 |
| % de cuidadoras que prefiere cuidado en casa (ENASIC) | 61.2 |

**2. No editen los notebooks 01 y 02.** Hagan una copia con su fuente y nombre: `03_denue_fabian.ipynb`, `03_censo_karen.ipynb`, `03_enut_edwin.ipynb`, `03_enasic_vilchis.ipynb`. Así nadie pisa el trabajo de otro.

**3. La regla del análisis.** La unidad de análisis es **la mujer cuidadora**. Todo responde a: *¿dónde y cuánto trabajo de cuidado recae sobre las mujeres de la CDMX, y qué tanto lo alivia la oferta de cuidados cercana?* Los hombres solo aparecen como referencia para medir la brecha, nunca como tema.

**4. Ficha técnica: plantilla común.** Cada quien entrega una ficha de su fuente con estos campos, en este orden:

| Campo | Qué poner |
|---|---|
| Nombre oficial y siglas | Como lo publica el INEGI |
| Institución productora | |
| Liga de descarga | La URL exacta del archivo que usamos (está en la primera celda del notebook) |
| Versión y fecha de levantamiento o corte | |
| Periodicidad | Anual, quinquenal, edición única, etc. |
| Población objetivo y unidad de observación | Personas, hogares, viviendas, establecimientos |
| Diseño y tamaño de muestra | Si es censo o registro, decirlo. Si es encuesta: muestra total, muestra en CDMX, estratos, UPM |
| Nivel geográfico real | El nivel más fino que **de verdad** se puede usar, no el que dice la publicidad |
| Variables que usamos | Nombre en la base, descripción y para qué la usamos |
| Limitaciones | Todo lo que no se puede afirmar con esta fuente |
| Validación | Qué cifra oficial publicada reprodujimos y con qué resultado |
| Uso en el proyecto | Qué hallazgo, indicador o entregable alimenta |

**5. Cómo reportar una cifra.** Siempre con fuente, año y nivel geográfico. Ejemplo: *"62.2% de las mujeres de 12 años y más de la CDMX realiza trabajo de cuidado no remunerado (INEGI, ENUT 2024)"*. Nunca una cifra suelta.

---

## Fabián — DENUE y arquitectura de datos

**Objetivo de la semana:** que los datos dejen de vivir en notebooks y pasen a una base de datos reproducible, que es lo que el resto del equipo va a usar para el tablero.
**Entregables para:** Herramientas y Técnicas Avanzadas (pasos 1.1 a 1.4 del WORKFLOW).

### Tarea 1 · Ficha técnica del DENUE
- Versión usada: **DENUE 05/2026**, archivo `denue_09_csv.zip` (CDMX, 462,732 establecimientos).
- Documentar la clasificación de cuidado que usamos y su justificación:
  - **Incluidos para el análisis de mujeres:** guarderías (`624411`, `624412`), residencias y asilos para personas mayores (`623311`, `623312`), centros de día para personas mayores y con discapacidad (`624121`, `624122`).
  - **Excluidos, con el porqué:** grupos de autoayuda para adicciones (`624191`), residencias para adicciones, orfanatos y residencias asistenciales, servicios de orientación. No sustituyen horas de cuidado en el hogar.
- Limitación principal: el DENUE **no trae capacidad** (lugares disponibles), solo rango de personal ocupado. Por eso hablamos de establecimientos y nunca de "cobertura".

### Tarea 2 · Estructura del proyecto
```
pp7/
├── data/raw/          ← descargas del INEGI, nunca se editan
├── data/curada/       ← tablas limpias
├── etl/               ← scripts .py numerados
│   ├── 01_descarga.py
│   ├── 02_denue.py
│   ├── 03_censo.py
│   ├── 04_enut.py
│   ├── 05_enasic.py
│   └── 06_indicadores.py
├── sql/               ← creación de esquemas y tablas
└── notebooks/
```
Cada script hace una sola cosa, se puede correr solo y deja su resultado en `data/curada/` y en PostgreSQL.

### Tarea 3 · PostgreSQL por capas
- Activar **PostGIS** (`CREATE EXTENSION postgis;`). Con eso el conteo "a 1 km" se hace en SQL con `ST_DWithin` en lugar del BallTree de Python.
- Tres esquemas: `cruda`, `curada`, `indicadores`.
- Tablas mínimas:

| Esquema | Tabla | Contenido |
|---|---|---|
| `curada` | `denue_cuidado` | id, codigo_act, tipo, sector, per_ocu, cvegeo_ageb, cve_mun, geom (punto) |
| `curada` | `censo_ageb_mujeres` | cvegeo_ageb, alcaldía y las variables del notebook 02 (mujeres de 15 a 59, población de 0 a 5, discapacidad para el autocuidado, jefatura femenina, PE_INAC_F) |
| `curada` | `ageb_poligonos` | cvegeo_ageb, geom (polígono). **La carga Karen** |
| `curada` | `enut_personas` | microdatos de la ENUT con `fac_per`, `est_dis` y `upm_dis` |
| `curada` | `enasic_cuidadoras` | tabla `tpob_cui` con `FAC_CUI`, `UPM_DIS` y `EST_DIS` |
| `indicadores` | `carga_ageb` | carga por mujer, guarderías y respaldo total a 1 km, bandera de zona sin respaldo |
| `indicadores` | `resumen_alcaldia` | los indicadores agregados por alcaldía |

- Llave territorial única: **CVEGEO** (entidad + municipio + localidad + AGEB = 13 caracteres).
- Criterio de terminado: borrar la base, correr los scripts en orden y que `indicadores.carga_ageb` vuelva a dar las mismas 88 zonas sin respaldo (o el número nuevo, cuando Karen meta los polígonos).

### Tarea 4 · Diagrama de arquitectura (paso 1.2)
Un diagrama con las fuentes → `data/raw` → scripts ETL → esquemas `cruda` / `curada` / `indicadores` → tablero (Fase 4) y programa (Fase 6). Indicar dónde entra la demo de PySpark.

### Tarea 5 · Demo de PySpark en Docker
- Imagen: `quay.io/jupyter/pyspark-notebook` o `apache/spark`. Evitar Alpine: da problemas con PySpark y sus dependencias.
- Qué demostrar: el mismo cruce DENUE × AGEB a 1 km hecho en Spark, con el mismo resultado que en Python/SQL.
- Documentar en una página: qué cambiaría si el volumen fuera nacional (todos los estados del DENUE y del Censo) y por qué hoy no hace falta.
- Esto es respaldo, no prioridad. Si la semana no alcanza, se mueve a la siguiente.

### Dónde subirlo
Notion → RECURSOS: ficha técnica del DENUE. WORKFLOW: actualizar los pasos 1.2, 1.3 y 1.4 con el diagrama y una explicación corta de cada script.

---

## Karen — Censo 2020 y mapas oficiales

**Objetivo de la semana:** convertir el hallazgo B (mujeres que cuidan sin respaldo) de exploratorio a validado, cambiando las ubicaciones aproximadas por los mapas oficiales del INEGI.
**Entregables para:** Analítica para los Negocios (pasos 3.2 y 3.3 del WORKFLOW).

### Tarea 1 · Ficha técnica del Censo 2020
- Archivo usado: `ageb_mza_urbana_09_cpv2020_csv.zip`, resultados por AGEB y manzana urbana de la CDMX.
- Puntos que **deben** aparecer:
  - Es censo, no muestra: no hay margen de error muestral.
  - **2,433 AGEB urbanas** en la CDMX.
  - Algunas AGEB tienen datos reservados por confidencialidad, marcados con `*` (por ejemplo, 48 AGEB en la variable de discapacidad para el autocuidado). Nosotros los tratamos como faltantes.
  - Las AGEB urbanas no cubren las zonas rurales: en **Milpa Alta queda fuera 16% de la población**. Los totales por alcaldía sí son completos.
  - Antigüedad: 2020. Es el dato más viejo del proyecto, pero es la única fuente a nivel AGEB.
- Variables que usamos (nombre en la base):
  - `P_15YMAS_F` y `P_60YMAS_F` (para obtener las mujeres de 15 a 59 años)
  - `P_0A2` y `P_3A5` (población de 0 a 5 años)
  - `PCDISC_MOT2` (discapacidad para vestirse, bañarse o comer)
  - `HOGJEF_F` y `TOTHOG` (jefatura femenina)
  - `PE_INAC_F` y `P_12YMAS_F` (mujeres fuera del mercado laboral)

### Tarea 2 · Conseguir los polígonos de las AGEB
- Fuente: **Marco Geoestadístico** del INEGI correspondiente al Censo 2020, archivo de la CDMX (se busca en inegi.org.mx, en la sección de Marco Geoestadístico).
- Dentro del paquete de la CDMX viene una capa por nivel; la de AGEB urbanas suele llamarse `09a.shp`. **Confirmar con el diccionario que trae el paquete.**
- Verificar que el campo `CVEGEO` de la capa empate con el `CVEGEO_AGEB` del notebook. Reportar cuántas AGEB empatan y cuántas no.

### Tarea 3 · Recalcular las zonas sin respaldo con geometría oficial
Con `geopandas`:
1. Leer la capa de AGEB y pasarla a un sistema en metros: **EPSG:6372** (México ITRF2008 / LCC).
2. Calcular el centroide oficial de cada AGEB.
3. Pasar los establecimientos del DENUE (tabla `denue_cuidado_cdmx.csv` del paquete, columnas `lat`/`lon`) al mismo sistema.
4. Contar guarderías, residencias y centros de día a 1,000 m de cada centroide.
5. Volver a aplicar la regla: AGEB en el cuartil más alto de carga por mujer **y** sin ningún respaldo a 1 km.

### Tarea 4 · Comparar con la versión exploratoria
- ¿Cuántas de las 88 AGEB originales siguen saliendo? ¿Cuántas nuevas aparecen?
- ¿Iztapalapa sigue siendo la alcaldía con más mujeres en zonas sin respaldo?
- **Prueba de sensibilidad:** repetir con radios de 800 m y 1,500 m. Si la conclusión cambia mucho con el radio, hay que decirlo en el informe.
- Si el hallazgo cambia, se reporta como salió. Un resultado distinto también es un resultado.

### Tarea 5 · Mapa para el informe
Un mapa de coropletas con los polígonos: color = carga por cada 100 mujeres, contorno marcado = zona sin respaldo. Con título, leyenda y fuente.

### Dónde subirlo
Notion → RECURSOS: ficha técnica del Censo. WORKFLOW, paso 3.2: resultado de la comparación y el mapa. Pasarle a Fabián la capa de polígonos para la tabla `curada.ageb_poligonos`.

---

## Edwin — ENUT 2024 e indicadores

**Objetivo de la semana:** validar el hallazgo A (doble jornada) con márgenes de error formales y empezar las fichas de indicador del Observatorio.
**Entregables para:** Inteligencia de Negocios (pasos 4.1 y 4.2 del WORKFLOW).

### Tarea 1 · Ficha técnica de la ENUT 2024
- Archivo usado: `conjunto_de_datos_enut_2024_csv.zip`, tabla de variables construidas (`tvar_crea`).
- Puntos que **deben** aparecer:
  - Levantamiento del 7 de octubre al 29 de noviembre de 2024; publicada el 28 de agosto de 2025.
  - Quinquenal; declarada Información de Interés Nacional. Ediciones comparables: 2014, 2019 y 2024.
  - Representativa por entidad federativa. **CDMX: 2,107 personas de 12 años y más (1,144 mujeres), 185 UPM y 5 estratos.**
  - Horas por semana; usamos las variables **sin cuidados pasivos** (`_sin_cp`).
  - Método: los promedios de horas se calculan **entre quienes realizan la actividad**.
- Validación: con ese método se reproducen exactamente las cifras publicadas por el INEGI: 59.6 h de trabajo total (61.1 mujeres, 58.0 hombres).

### Tarea 2 · Márgenes de error con el diseño muestral
Esto es lo más importante de tu semana. Las variables del diseño están en la misma tabla: `est_dis` (estrato), `upm_dis` (unidad primaria de muestreo) y `fac_per` (factor de expansión).

**Opción recomendada, R con el paquete `survey`:**
```r
library(survey)
options(survey.lonely.psu = "adjust")
d <- svydesign(ids = ~upm_dis, strata = ~est_dis, weights = ~fac_per,
               data = enut, nest = TRUE)
# Ojo: el subconjunto se hace DESPUÉS de definir el diseño, nunca filtrando antes
cdmx_ocupadas <- subset(d, cve_ent == "09" & cond_aee == "1")
svyby(~jornada_total, ~sexo, cdmx_ocupadas, svymean)
```
En Python, la alternativa es la librería `samplics`. Lo importante en cualquier caso:
- **No filtren los datos antes de definir el diseño.** Filtrar primero subestima los errores.
- Para cada cifra reporten: estimación, error estándar, intervalo de confianza al 95% y **coeficiente de variación (CV)**.
- Criterio del INEGI para calificar la precisión: CV menor a 15% = alta; de 15% a 30% = moderada; mayor a 30% = baja (no publicable sin advertencia).

### Tarea 3 · Validar el hallazgo A
Ya hice una prueba rápida con remuestreo (bootstrap por UPM dentro de cada estrato). Tu trabajo es confirmarla con el método formal:

| Brecha entre personas ocupadas de la CDMX (mujeres − hombres) | Estimación | IC 95% (bootstrap rápido) |
|---|---|---|
| Jornada total (pagado + doméstico + cuidado) | +3.5 h | 0.7 a 6.6 h |
| Trabajo no pagado (doméstico + cuidado) | +12.7 h | 10.7 a 14.6 h |

**Qué significa:** la brecha en jornada total es estadísticamente distinta de cero, pero frágil. La brecha en trabajo no pagado es sólida. **Propuesta:** que el hallazgo A se encabece con el trabajo no pagado (*"las mujeres ocupadas de la CDMX hacen 12.7 horas más de trabajo no pagado a la semana que los hombres ocupados"*) y que la jornada total de 77 h vaya como dato de apoyo.

Además, calcular el CV de cada fila de la tabla 1.1 del notebook 02 y marcar las que salgan con precisión baja.

### Tarea 4 · Fichas de indicador
Usar el formato del Sistema de Indicadores de Cuidados de la CDMX (SICCDMX) como modelo. Revisar también las definiciones del MACU (mapadecuidados.inmujeres.gob.mx, sección de definiciones). Campos de cada ficha:

| Campo | Ejemplo |
|---|---|
| Nombre | Horas semanales de cuidado no remunerado de las mujeres |
| Definición | Promedio de horas a la semana que dedican al cuidado de integrantes del hogar las mujeres de 12+ que realizan esta actividad |
| Fórmula | Σ(horas × factor) / Σ(factor), entre mujeres con horas > 0 |
| Fuente y variable | ENUT 2024, `trab_no_rem_cuid_hog` |
| Desagregación posible | Entidad; por edad y condición de actividad |
| Periodicidad | Quinquenal |
| Unidad | Horas por semana |
| Categoría | Demanda / oferta / contexto |
| Actor | Hogares / Estado / mercado / comunidad |
| Precisión | CV y clasificación |
| Limitaciones | |
| Interpretación | Qué significa un valor alto |

**Primeras seis fichas:**
1. Horas semanales de cuidado de las mujeres (ENUT)
2. Brecha de trabajo no pagado entre mujeres y hombres ocupados (ENUT)
3. Personas con necesidad de cuidado directo por cada 100 mujeres de 15 a 59 (Censo)
4. Número de AGEB con carga alta y sin respaldo a 1 km (Censo + DENUE; usar el número final de Karen)
5. Mujeres de 15 a 59 que viven en zonas sin respaldo (Censo + DENUE)
6. Porcentaje de mujeres cuidadoras que prefiere el cuidado en casa (ENASIC; marcar que es nacional)

### Dónde subirlo
Notion → RECURSOS: ficha técnica de la ENUT. WORKFLOW: tabla de márgenes de error junto al hallazgo A (compuerta de la Fase 3) y las seis fichas en el paso 4.2.

---

## Vilchis — ENASIC 2022 y marco legal

**Objetivo de la semana:** profundizar el hallazgo C, que es la base del programa social, y arrancar el dictamen jurídico.
**Entregables para:** Leyes para la Protección de Datos (paso 2.1) y Práctica Profesional I (insumo del paso 6.2).

### Tarea 1 · Ficha técnica de la ENASIC 2022
- Archivo usado: `conjunto_de_datos_enasic_2022_csv.zip`, tabla de población cuidadora (`tpob_cui`).
- Puntos que **deben** aparecer:
  - Levantamiento del 24 de octubre al 16 de diciembre de 2022. **Edición única**: no hay serie de tiempo.
  - Muestra de 7,021 viviendas a nivel nacional (6,423 efectivas).
  - **Los microdatos públicos no traen ninguna variable geográfica** (ni entidad, ni municipio, ni tamaño de localidad), ni en la versión de datos abiertos ni en la de microdatos. Por eso todo lo que digamos con ENASIC es **nacional**. Es la limitación más importante y hay que escribirla tal cual.
  - Seis tablas; la nuestra es `tpob_cui` (5,677 registros de personas cuidadoras de 15 años y más). Trae `SEXO`, `EDAD`, el factor `FAC_CUI` y las variables del diseño `UPM_DIS` y `EST_DIS`.
- Validación: se reproducen las cifras oficiales: 31.7 millones de personas cuidadoras, 75.1% mujeres (23.8 millones).

### Tarea 2 · Profundizar el hallazgo C (insumo del programa)
Siempre filtrando a mujeres (`SEXO == "2"`) y ponderando con `FAC_CUI`. Variables:

| Variable | Pregunta |
|---|---|
| `P6_42` | ¿Buscó guardería, casa de día o asilo desde octubre de 2021? |
| `P6_44_01` a `P6_44_11` | Si buscó: por qué no le cumplieron (costo, lejanía, lista de espera, horarios, etc.) |
| `P6_45_01` a `P6_45_10` | Si no buscó: por qué no |
| `P6_46` | Si contratara un servicio de cuidado, ¿dónde lo preferiría? |
| `P6_47` | ¿Le gustaría ser cuidadora profesional si le pagaran? |
| `P6_48` | ¿Estaría dispuesta a capacitarse para ser cuidadora? |
| `P5_6` | Condición de actividad la semana pasada |

Preguntas a responder:
1. **Perfil de "Puedo cuidar":** de las mujeres que trabajarían como cuidadoras pagadas (`P6_47 == "1"`): ¿qué edad tienen?, ¿trabajan hoy fuera de casa (`P5_6`)?, ¿qué porcentaje estaría dispuesta a capacitarse (`P6_48`)? Esto define la oferta de la plataforma.
2. **Perfil de "Necesito cuidado":** ¿quiénes prefieren el cuidado en casa (`P6_46 == "1"`) y quiénes no contratarían nada (`P6_46 == "5"`)? Comparar por edad y condición de actividad. Ojo: el 32% que "no contrataría" es un riesgo de adopción del programa y hay que decirlo.
3. **Barreras:** de las pocas que sí buscaron un servicio (3.2%, solo 142 mujeres en la muestra), ¿por qué no les cumplió? **Muestra chica: presentarlo solo como indicativo.**
4. Márgenes de error con el diseño (`UPM_DIS`, `EST_DIS`, `FAC_CUI`), igual que Edwin. Pueden resolverlo juntos.

Entregable: una página con los dos perfiles y las barreras, redactada como insumo para el diseño del programa (paso 6.2).

### Tarea 3 · Dictamen jurídico, primer borrador (paso 2.1)
Estructura sugerida:
1. **Marco vigente.** LFPDPPP publicada en el DOF el 20 de marzo de 2025, en vigor desde el 21 de marzo de 2025; abroga la ley de 2010. Autoridad: **Secretaría Anticorrupción y Buen Gobierno** (el INAI se extinguió). El PP cita una guía del INAI de 2016: se puede usar como referencia técnica, pero no como autoridad vigente.
2. **Artefacto 1, Observatorio.** Solo usa datos públicos agregados del INEGI. No trata datos personales. Argumentarlo: el INEGI ya aplica confidencialidad (por eso hay valores `*` en el Censo) y nosotros no intentamos reidentificar a nadie.
3. **Artefacto 2, Programa de vinculación.** Sí trata datos personales y **sensibles** (salud, discapacidad, dependencia de la persona cuidada; domicilio). Aunque en el proyecto usemos datos sintéticos, el dictamen se hace como si el programa fuera real. Cubrir: consentimiento (expreso y por escrito para datos sensibles), aviso de privacidad, finalidades, minimización, seudonimización, conservación y eliminación, derechos ARCO.
4. **Tabla finalidad–dato–base jurídica–riesgo–medida.** Una fila por cada dato del programa (nombre, domicilio, teléfono, tipo de cuidado requerido, nivel de dependencia, disponibilidad de la cuidadora, etc.).
5. **Artículos aplicables.** Citar los números de artículo **directamente del texto publicado en el DOF**, no de resúmenes de internet: la numeración cambió respecto a la ley de 2010.

### Dónde subirlo
Notion → RECURSOS: ficha técnica de la ENASIC. WORKFLOW: los perfiles junto al hallazgo C (compuerta de la Fase 3) y el borrador del dictamen en el paso 2.1.

---

## Agenda de la reunión del 8 de octubre

1. Cifras de control: ¿a todos les corrió el notebook igual? (5 min)
2. Fichas técnicas, una por persona (20 min)
3. Validación de los hallazgos: márgenes de error del A (Edwin), comparación con mapas oficiales del B (Karen), perfiles del C (Vilchis) (30 min)
4. Decisión: ¿se cierra la compuerta de la Fase 3 con los tres hallazgos? (10 min)
5. Avance de la arquitectura y la base de datos (Fabián) (10 min)
6. Siguiente semana: si se cierra la compuerta, arrancan los KPI y el tablero (Fase 4) y el diseño del programa (Fase 6)
