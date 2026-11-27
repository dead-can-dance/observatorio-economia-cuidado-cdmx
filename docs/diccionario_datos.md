# Diccionario de datos — esquema `indicadores`

Estas quince tablas son **las únicas que debe leer el tablero**. Ya vienen agregadas,
cruzadas y con el contexto necesario para citar cualquier cifra. Las nueve primeras son el
diagnóstico descriptivo (notebook 02); las seis de la
[capa analítica](#capa-analítica-notebook-03) salen del notebook 03 (serie histórica,
pronóstico, modelo y escenarios del trabajo integrador). Los esquemas `cruda`
y `curada` existen para auditar y reconstruir, no para graficar.

Todas las tablas llevan dos columnas de contexto:

| Columna | Para qué |
|---|---|
| `nivel_geografico` | Territorio al que se refiere la fila: `AGEB`, `Alcaldía`, `CDMX` o `Nacional`. Impide presentar como cifra de la ciudad algo que es nacional. |
| `fuente` | Fuente citable con año. Valores actuales: `INEGI, ENUT 2024`, `INEGI, ENASIC 2022`, `INEGI, DENUE 05/2026`, `INEGI, Censo de Población y Vivienda 2020`, `INEGI, Censo 2020 + DENUE 05/2026`. |

Ninguna cifra se publica sin fuente, año y nivel geográfico.

---

## `indicadores.kpi_cdmx`

**Para qué sirve en el tablero.** Es la tira de KPIs de la portada: las cifras de
cabecera del Observatorio, listas para mostrar sin calcular nada. Sirve además como
prueba de regresión del ETL — si un valor cambia sin que nadie haya tocado el método,
algo se rompió.

**Filas esperadas:** 13 (una por cifra citable). Doce salen de
`data/curada/resumen_cifras_clave.csv`; la decimotercera, `ENUT · brecha de trabajo no
pagado, mujeres − hombres ocupados (h)` = **12.7**, la calcula el ETL a partir de la
columna sin redondear de la doble jornada (ver `indicadores.enut_doble_jornada`).

| Columna | Tipo | Descripción | Unidad |
|---|---|---|---|
| `clave` | `text` **PK** | Identificador estable, con el prefijo de la fuente (`ENUT · % mujeres CDMX que cuidan`). El tablero referencia por aquí, no por posición. | — |
| `etiqueta` | `text` | Texto legible para pantalla, ya sin el prefijo de la fuente. | — |
| `valor_num` | `numeric(12,1)` | Valor numérico. `NULL` cuando el KPI es cualitativo. | según `unidad` |
| `valor_texto` | `text` | Valor de texto, para los KPI que no son números (p. ej. `Milpa Alta`). `NULL` cuando el KPI es numérico. | — |
| `unidad` | `text` | Cómo formatear el valor: `%`, `horas por semana`, `AGEB`, `mujeres`, `personas por cada 100 mujeres`, `texto`. Sin esto, un 62.2 y un 77.0 se ven igual. | — |
| `nivel_geografico` | `text` | `CDMX` o `Nacional`. **Las cuatro filas de ENASIC son `Nacional`.** | — |
| `fuente` | `text` | Fuente citable con año. | — |

Hay una restricción que obliga a que `valor_num` o `valor_texto` tenga contenido: no
puede existir un KPI vacío.

> **La brecha de trabajo no pagado no se recalcula en el tablero.** Es 12.7 h y sale de
> los valores sin redondear (31.351… − 18.636…). Restar las columnas de
> `indicadores.enut_doble_jornada`, que van con un decimal, da 12.6 y contradice al
> propio KPI. Si hay que mostrarla, se lee de esta tabla.

---

## `indicadores.resumen_alcaldia`

**Para qué sirve en el tablero.** La vista territorial de alto nivel: tabla ordenable,
barras comparativas y mapa de coropletas por alcaldía. Ya trae el cruce de demanda de
cuidado, oferta formal y zonas sin respaldo, así que el tablero no necesita hacer joins.

**Filas esperadas:** 16 (las 16 alcaldías de la CDMX).

| Columna | Tipo | Descripción | Unidad |
|---|---|---|---|
| `cve_mun` | `text` **PK** | Clave de alcaldía, 3 caracteres con ceros a la izquierda (`002` a `017`). | — |
| `alcaldia` | `text` | Nombre oficial, con acentos. | — |
| `pob_total` | `integer` | Población total, Censo 2020. Incluye zona rural. | personas |
| `mujeres_15a59` | `integer` | Mujeres de 15 a 59: la población sobre la que recae el cuidado. | mujeres |
| `pct_60mas` | `numeric(5,1)` | Población de 60 años o más. | % |
| `carga_directa_x100_mujeres` | `numeric(5,1)` | Personas con necesidad de cuidado directo por cada 100 mujeres de 15 a 59. La CDMX en conjunto está en 21.6. | personas por cada 100 mujeres |
| `rango_carga` | `integer` | Posición por carga de cuidado; 1 es la más alta (Milpa Alta). | puesto |
| `pct_hog_jefa` | `numeric(5,1)` | Hogares con jefatura femenina. | % |
| `pct_mujeres_inactivas` | `numeric(5,1)` | Mujeres de 12+ fuera del mercado laboral. Incluye estudiantes y jubiladas. | % |
| `agebs` | `integer` | AGEB de la alcaldía incluidas en el análisis territorial. Suman 2,320 en la ciudad, **no 2,433**. | AGEB |
| `agebs_alta_carga` | `integer` | AGEB en el cuartil superior de carga de toda la ciudad (umbral 24.1). Suman 580. | AGEB |
| `agebs_sin_respaldo` | `integer` | AGEB de alta carga sin ninguna guardería, residencia ni centro de día a 1 km. Suman 88; Iztapalapa concentra 25. | AGEB |
| `mujeres_sin_respaldo` | `integer` | Mujeres de 15 a 59 que viven en esas AGEB. Suman 125,256. | mujeres |
| `pct_agebs_alta_carga_sin_respaldo` | `numeric(5,1)` | De las AGEB de alta carga de la alcaldía, cuántas no tienen respaldo. **`NULL` cuando la alcaldía no tiene ninguna AGEB de alta carga** (Benito Juárez): es "no aplica", no cero. | % |
| `guarderias` | `integer` | Guarderías del DENUE en la alcaldía. | establecimientos |
| `cuidado_mayores` | `integer` | Residencias, asilos y centros de día para personas mayores. | establecimientos |
| `ninos_0a5_por_guarderia` | `numeric(10,1)` | Niñas y niños de 0 a 5 por cada guardería. Presión sobre la oferta, **no cobertura**. | niñas y niños por establecimiento |
| `mayores_60_por_establecimiento` | `numeric(10,1)` | Personas de 60+ por cada establecimiento de cuidado de mayores. Misma advertencia. | personas por establecimiento |
| `pct_guarderias_publicas` | `numeric(5,1)` | Guarderías de la alcaldía que son del sector público. | % |
| `nivel_geografico` | `text` | Siempre `Alcaldía`. | — |
| `fuente` | `text` | `INEGI, Censo 2020 + DENUE 05/2026`. | — |

---

## `indicadores.carga_ageb`

**Para qué sirve en el tablero.** Es **la capa del mapa**: un punto (o un polígono, cuando
se integre el Marco Geoestadístico) por AGEB, coloreado por carga de cuidado y con las
zonas sin respaldo resaltadas. También alimenta los histogramas de desigualdad interna.

**Filas esperadas:** 2,320.

El embudo es: 2,433 AGEB urbanas → 2,326 con al menos 100 mujeres de 15 a 59 y carga no
nula → **2,320 con centroide**. Para porcentajes sobre el total de AGEB de la ciudad hay
que usar `curada.censo_ageb`, no esta tabla.

| Columna | Tipo | Descripción | Unidad |
|---|---|---|---|
| `cvegeo_ageb` | `text` **PK** | Llave territorial: entidad(2) + municipio(3) + localidad(4) + AGEB(4) = 13 caracteres. **Siempre texto**: 222 de las 2,433 AGEB terminan en letra (`003A`). | — |
| `cve_mun` | `text` | Clave de alcaldía, 3 caracteres. | — |
| `alcaldia` | `text` | Nombre de la alcaldía. | — |
| `mujeres_15a59` | `integer` | Mujeres de 15 a 59 en el AGEB. Mínimo 100 por construcción. | mujeres |
| `pob_0a5` | `integer` | Población de 0 a 5 años. Parte del numerador de la carga. Puede ser `NULL` por confidencialidad. | personas |
| `pob_disc_autocuidado` | `integer` | Personas con discapacidad para vestirse, bañarse o comer. La otra parte del numerador. Puede ser `NULL`. | personas |
| `carga_directa_x100_mujeres` | `numeric(5,1)` | `(pob_0a5 + pob_disc_autocuidado) / mujeres_15a59 × 100`. Es la variable que colorea el mapa. Rango observado: 1.1 a 37.5. | personas por cada 100 mujeres |
| `pct_hog_jefa` | `numeric(5,1)` | Hogares con jefatura femenina en el AGEB. | % |
| `pct_mujeres_inactivas` | `numeric(5,1)` | Mujeres de 12+ fuera del mercado laboral. | % |
| `guarderias_1km` | `integer` | Guarderías a menos de 1 km del punto de referencia (≈ 12 a 15 min a pie). | establecimientos |
| `respaldo_total_1km` | `integer` | Guarderías + residencias y asilos + centros de día a 1 km. Solo cuenta establecimientos con `es_respaldo = TRUE`. | establecimientos |
| `alta_carga` | `boolean` | AGEB en el cuartil superior de carga de la ciudad (≥ 24.1). Son 580. | — |
| `sin_guarderia` | `boolean` | De alta carga y sin ninguna guardería a 1 km. Son 131. | — |
| `sin_respaldo` | `boolean` | **Hallazgo B:** de alta carga y sin ningún respaldo a 1 km. Son 88, donde viven 125,256 mujeres de 15 a 59. | — |
| `lat` | `double precision` | Latitud del punto de referencia, WGS84. | grados decimales |
| `lon` | `double precision` | Longitud del punto de referencia, WGS84. | grados decimales |
| `centroide_es_aproximado` | `boolean` | **`TRUE` hoy.** Mientras valga `TRUE`, `lat`/`lon` son la mediana de los establecimientos del DENUE dentro del AGEB, no el centroide del polígono. Pasa a `FALSE` cuando se cargue `curada.ageb_centroide_oficial`. Si está en `TRUE`, el hallazgo B se reporta como exploratorio. | — |
| `nivel_geografico` | `text` | Siempre `AGEB`. | — |
| `fuente` | `text` | `INEGI, Censo 2020 + DENUE 05/2026`. | — |

---

## `indicadores.establecimientos_cuidado`

**Para qué sirve en el tablero.** La capa de puntos del mapa: dónde está la oferta formal
de cuidado, con filtros por grupo, tipo y sector.

**Filas esperadas:** 1,463.

> **Advertencia que hay que leer antes de usar esta tabla.** `COUNT(*)` da 1,463, pero
> solo **838** (`es_respaldo = TRUE`) entran en el cálculo de las zonas sin respaldo.
> Publicar "1,463 establecimientos de cuidado" junto al hallazgo B es contradictorio.

| Columna | Tipo | Descripción | Unidad |
|---|---|---|---|
| `id` | `text` **PK** | Clave del establecimiento en el DENUE. Texto aunque parezca número: es un identificador, no una cantidad. | — |
| `nom_estab` | `text` | Nombre comercial. Puede ser `NULL`. | — |
| `grupo` | `text` | Agrupación del proyecto, para la leyenda del mapa: `Infancia`, `Personas mayores`, `Personas mayores y discapacidad`, `Salud y discapacidad`, `Asistencia social`, `Apoyo comunitario`. | — |
| `tipo` | `text` | Subtipo: `Guardería`, `Residencia / asilo`, `Centro de día`, `Comedor comunitario`, `Orfanato / residencia asistencial`, `Residencia con enfermería`, `Residencia discapacidad intelectual`. | — |
| `sector` | `text` | `Público` o `Privado`. | — |
| `per_ocu` | `text` | Rango de personal ocupado (`0 a 5 personas`, `11 a 30 personas`...). **No es capacidad de atención.** | — |
| `codigo_act` | `text` | Código SCIAN de 6 dígitos, como texto. | — |
| `cve_mun` | `text` | Clave de alcaldía, 3 caracteres. | — |
| `alcaldia` | `text` | Nombre de la alcaldía. | — |
| `cvegeo_ageb` | `text` | AGEB donde cae el establecimiento. **`NULL` en 6 casos**, cuando la clave del DENUE no empata con ninguna AGEB urbana del Censo. | — |
| `es_respaldo` | `boolean` | `TRUE` para guarderías, residencias y asilos de personas mayores y centros de día: los que sustituyen horas de cuidado en el hogar. 838 de 1,463. El mapa debería distinguirlos visualmente. | — |
| `lat` | `double precision` | Latitud real publicada por el DENUE. A diferencia de `carga_ageb`, esta **no** es aproximada. | grados decimales |
| `lon` | `double precision` | Longitud real. | grados decimales |
| `nivel_geografico` | `text` | Siempre `AGEB`. | — |
| `fuente` | `text` | `INEGI, DENUE 05/2026`. | — |

---

## `indicadores.enut_carga_actividad`

**Para qué sirve en el tablero.** Comparar a la CDMX contra el total nacional y a mujeres
contra hombres, por actividad de cuidado. Barras agrupadas o tabla de contraste.

**Filas esperadas:** 16 (2 ámbitos × 2 sexos × 4 actividades).

Las horas se promedian **entre quienes realizan la actividad**, que es el método con el
que se reproducen las cifras publicadas por el INEGI.

| Columna | Tipo | Descripción | Unidad |
|---|---|---|---|
| `ambito` | `text` **PK** | `CDMX` o `Nacional`. En la CDMX la muestra es de 2,107 personas de 12+ (1,144 mujeres). | — |
| `sexo` | `text` **PK** | `Mujeres` u `Hombres`. Los hombres son referencia para medir la brecha, nunca tema. | — |
| `actividad` | `text` **PK** | `Cuidado a integrantes del hogar (total)`, `Cuidado a niñas/os de 0 a 5`, `Cuidado a personas de 60+`, `Cuidados especiales (enfermedad o discapacidad)`. Variables sin cuidados pasivos. | — |
| `pct_realiza` | `numeric(5,1)` | Población de 12+ del ámbito y sexo que realiza la actividad. | % |
| `horas_semana` | `numeric(5,1)` | Horas que dedica quien la realiza. **No** es un promedio sobre toda la población. | horas por semana |
| `n_muestral` | `integer` | Personas de la muestra que sostienen la cifra. | casos |
| `precision_baja` | `boolean` | `TRUE` cuando `n_muestral < 100`. Hoy son 3 filas: cuidados especiales en CDMX (77 mujeres, 55 hombres) y cuidado de 0 a 5 de hombres en CDMX (82). Es un semáforo, no el coeficiente de variación formal. | — |
| `nivel_geografico` | `text` | `CDMX` o `Nacional`, igual que `ambito`. | — |
| `fuente` | `text` | `INEGI, ENUT 2024`. | — |

> Las etiquetas de `actividad` **no son idénticas** a las de `enut_brecha_mujeres_cdmx`
> (`niñas/os` contra `niñas y niños`). No unir las dos tablas por este texto.

---

## `indicadores.enut_brecha_mujeres_cdmx`

**Para qué sirve en el tablero.** La vista de brecha: cuánto cuidan las mujeres de la CDMX
y cuántas veces más que los hombres. Barras con etiqueta de razón.

**Filas esperadas:** 6.

Cubre dos actividades que no están en `enut_carga_actividad`: cuidado de 6 a 14 años y
trabajo doméstico no remunerado.

| Columna | Tipo | Descripción | Unidad |
|---|---|---|---|
| `actividad` | `text` **PK** | Actividad de cuidado o trabajo doméstico, en variables sin cuidados pasivos. | — |
| `pct_realiza_mujeres` | `numeric(5,1)` | Mujeres de 12+ de la CDMX que realizan la actividad. El **62.2** del cuidado total es cifra de control del proyecto. | % |
| `horas_mujeres` | `numeric(5,1)` | Horas entre las mujeres que la realizan. | horas por semana |
| `n_mujeres` | `integer` | Mujeres de la muestra que la realizan. Debajo de 100 la cifra es frágil. | casos |
| `horas_hombres_ref` | `numeric(5,1)` | Horas de los hombres que la realizan. Referencia, no tema. | horas por semana |
| `razon_mujeres_hombres` | `numeric(4,2)` | `horas_mujeres / horas_hombres_ref`. **Único campo con dos decimales**: la razón vale entre 0.98 y 2.12, y un decimal borraría la diferencia entre 1.51 y 1.53. | veces |
| `nivel_geografico` | `text` | Siempre `CDMX`. | — |
| `fuente` | `text` | `INEGI, ENUT 2024`. | — |

---

## `indicadores.enut_doble_jornada`

**Para qué sirve en el tablero.** El hallazgo A: la barra apilada de la doble jornada.
Trabajo pagado, doméstico y de cuidado, mujeres contra hombres ocupados.

**Filas esperadas:** 2 (`Mujeres ocupadas` y `Hombres ocupados (ref.)`).

A diferencia de las otras tablas de ENUT, aquí el promedio es sobre **toda** la población
ocupada del grupo, incluyendo a quien no realiza la actividad. Por eso los componentes
suman la jornada total.

| Columna | Tipo | Descripción | Unidad |
|---|---|---|---|
| `grupo` | `text` **PK** | `Mujeres ocupadas` u `Hombres ocupados (ref.)`. Solo personas con condición de actividad = ocupada. | — |
| `horas_trabajo_mercado` | `numeric(5,1)` | Trabajo para el mercado (trabajo pagado). | horas por semana |
| `horas_trabajo_domestico` | `numeric(5,1)` | Trabajo doméstico no remunerado del propio hogar. | horas por semana |
| `horas_cuidado` | `numeric(5,1)` | Cuidado no remunerado a integrantes del hogar. | horas por semana |
| `horas_jornada_total` | `numeric(5,1)` | Suma de los tres componentes. Mujeres **77.0**, hombres 73.5. Cifra de control. | horas por semana |
| `n_muestral` | `integer` | Personas ocupadas de la muestra CDMX (639 mujeres, 689 hombres). | casos |
| `nivel_geografico` | `text` | Siempre `CDMX`. | — |
| `fuente` | `text` | `INEGI, ENUT 2024`. | — |

> **Cómo encabezar este hallazgo.** La brecha en jornada total (+3.5 h) es
> estadísticamente distinta de cero pero frágil; la de trabajo no pagado (+12.7 h) es
> sólida. El equipo acordó encabezar con el trabajo no pagado y usar las 77 h como dato
> de apoyo.

> **La brecha de +12.7 h ya está calculada** en `indicadores.kpi_cdmx`, con la clave
> `ENUT · brecha de trabajo no pagado, mujeres − hombres ocupados (h)`. No se obtiene
> restando las columnas de esta tabla: con un decimal, `(23.3 + 8.0) − (13.1 + 5.6)` da
> 12.6. El ETL la calcula desde `cruda.mujeres_doble_jornada_cdmx.trabajo_no_pagado_sin_redondear`,
> la columna del CSV que conserva toda la precisión.

---

## `indicadores.enut_cuidado_por_grupo`

**Para qué sirve en el tablero.** Responder "¿qué mujeres cuidan más?": dos gráficas de
barras, una por condición de actividad y otra por grupo de edad.

**Filas esperadas:** 11 (6 de condición de actividad + 5 de grupo de edad).

| Columna | Tipo | Descripción | Unidad |
|---|---|---|---|
| `tipo_grupo` | `text` **PK** | `Condición de actividad` o `Grupo de edad`. **El tablero debe filtrar por esta columna antes de graficar**: mezclar las dos da un total sin sentido, porque son la misma población partida de dos maneras. | — |
| `grupo` | `text` **PK** | Categoría. Para condición: `Ocupada`, `Dedicada al hogar o al cuidado`, `Estudiante`, `Jubilada o pensionada`, `Desocupada`, `Otra situación`. Para edad: `12–17`, `18–29`, `30–44`, `45–59`, `60+`. | — |
| `horas_cuidado` | `numeric(5,1)` | Horas de cuidado promedio **por mujer del grupo, incluyendo a las que no cuidan**. Por eso es menor que en `enut_brecha_mujeres_cdmx`, que promedia solo entre quienes cuidan. | horas por semana |
| `pct_que_cuida` | `numeric(5,1)` | Mujeres del grupo que realizan trabajo de cuidado no remunerado. | % |
| `n_muestral` | `integer` | Mujeres de la muestra en el grupo. | casos |
| `confiable` | `boolean` | `FALSE` cuando `n_muestral < 60`. Hoy: `Desocupada` (4 casos) y `Otra situación` (20). Esas filas no se citan como cifra, solo como indicio. | — |
| `nivel_geografico` | `text` | Siempre `CDMX`. | — |
| `fuente` | `text` | `INEGI, ENUT 2024`. | — |

El pico está en las mujeres de 30 a 44 años (14.3 h) y en las dedicadas al hogar o al
cuidado (9.7 h).

---

## `indicadores.enasic_cuidadoras`

**Para qué sirve en el tablero.** El hallazgo C y el insumo del programa de vinculación:
la relación de las mujeres cuidadoras con los servicios formales. Cuatro gráficas,
filtrando por `tema`.

**Filas esperadas:** 19 (2 + 10 + 5 + 2).

> **Todo lo de esta tabla es NACIONAL.** Los microdatos públicos de la ENASIC no traen
> ninguna variable geográfica: ni entidad, ni municipio, ni tamaño de localidad. Estas
> cifras no se pueden presentar como de la CDMX ni poner en un mapa. Además es edición
> única: no hay serie de tiempo.

Base: mujeres cuidadoras de 15+, ponderadas con `FAC_CUI` (4,173 registros, 23.8 millones
de mujeres).

| Columna | Tipo | Descripción | Unidad |
|---|---|---|---|
| `tema` | `text` **PK** | `Búsqueda de servicios`, `Razones para no buscar`, `Preferencia de cuidado`, `Disposición a cuidar`. El tablero filtra por aquí. | — |
| `categoria` | `text` **PK** | Respuesta concreta dentro del tema (`En su casa`, `No contrataría`, `Son caros`...). | — |
| `pct` | `numeric(5,1)` | Porcentaje de la base que da esa respuesta. | % |
| `base` | `text` | Denominador exacto. **No es el mismo en todos los temas:** las razones para no buscar se calculan solo sobre las mujeres que NO buscaron. Sin esta columna los porcentajes no son comparables entre temas. | — |
| `respuesta_multiple` | `boolean` | `TRUE` cuando la pregunta admite varias respuestas y los porcentajes del tema **no suman 100**. Es el caso de `Razones para no buscar`. | — |
| `variable_enasic` | `text` | Variable en la tabla `tpob_cui` (`P6_42`, `P6_45_01 a P6_45_10`, `P6_46`, `P6_47 / P6_48`), para rastrear la cifra hasta el microdato. | — |
| `nivel_geografico` | `text` | Siempre `Nacional`. | — |
| `fuente` | `text` | `INEGI, ENASIC 2022`. | — |

Cifras de referencia: 3.2 % buscó un servicio, 61.2 % preferiría el cuidado en casa,
32.2 % no contrataría nada, 44.4 % trabajaría como cuidadora pagada, 42.8 % se
capacitaría.

---

# Capa analítica (notebook 03)

Seis tablas del trabajo integrador de Analítica para Negocios. Las produce
`notebooks/03_del_dato_a_la_decision_pp7.ipynb`; el ETL las carga sin recalcular nada.
Dos de ellas **no son mediciones**: `horas_cuidado_ageb` es una estimación de un modelo y
`escenarios_programa` es un escenario simulado (ver advertencias 6 y 7).

## `indicadores.oferta_historica`

**Para qué sirve en el tablero.** La serie de la oferta formal de respaldo en la CDMX:
guarderías, residencias y asilos de personas mayores y centros de día, en 19 ediciones del
DENUE (01/2016 a 05/2026). Mismas claves SCIAN que el notebook 02.

**Filas esperadas:** 114 (19 ediciones × 3 tipos × 2 sectores). La edición `2026-05` suma
**838**, igual que `establecimientos_cuidado WHERE es_respaldo` (es cifra de control).

| Columna | Tipo | Descripción | Unidad |
|---|---|---|---|
| `edicion` | `text` **PK** | Edición del DENUE, `AAAA-MM`. Faltan 05/2023 y 11/2025. | — |
| `periodo` | `text` | Semestre de la edición: `AAAA-S1` (enero a junio) o `AAAA-S2`. | — |
| `tipo` | `text` **PK** | `Guardería`, `Residencia / asilo` o `Centro de día`. | — |
| `sector` | `text` **PK** | `Privado` o `Público`, según la clave SCIAN. | — |
| `establecimientos` | `integer` | Establecimientos registrados. Conteo de directorio, no de lugares. | establecimientos |
| `nivel_geografico` | `text` | Siempre `CDMX`. | — |
| `fuente` | `text` | `INEGI, DENUE (19 ediciones, 01/2016 a 05/2026)`. | — |

> **Las caídas son escalones, no tendencias.** La serie baja en 2019-2020 y en 11/2024,
> cuando el DENUE incorpora los Censos Económicos 2019 y 2024. Un escalón junta cierres de
> varios años. No se dice «cerraron 172 guarderías en un semestre».

## `indicadores.pronostico_oferta`

**Para qué sirve en el tablero.** El pronóstico de la oferta de respaldo a 1, 2 y 3
semestres (2026-S2 a 2027-S2) con cinco métodos. El elegido (`elegido = TRUE`) es el
**ingenuo**, que ganó el backtesting; solo él trae intervalos.

**Filas esperadas:** 60 (4 series × 5 métodos × 3 semestres).

| Columna | Tipo | Descripción | Unidad |
|---|---|---|---|
| `serie` | `text` **PK** | `Total de respaldo`, `Guardería`, `Residencia / asilo` o `Centro de día`. | — |
| `metodo` | `text` **PK** | `Ingenuo`, `Suavizamiento simple`, `Holt amortiguado`, `Deriva` o `ARIMA(0,1,1)`. | — |
| `periodo` | `text` **PK** | Semestre pronosticado. | — |
| `horizonte` | `integer` | Semestres adelante del último dato (1 a 3). | semestres |
| `pronostico` | `numeric(8,1)` | Establecimientos pronosticados. | establecimientos |
| `li_80`, `ls_80` | `numeric(8,1)` | Intervalo empírico de 80 %: último valor + cuantiles 10 % y 90 % de los cambios históricos a h semestres. `NULL` fuera del método elegido. | establecimientos |
| `li_95`, `ls_95` | `numeric(8,1)` | Igual, con cuantiles 2.5 % y 97.5 %. | establecimientos |
| `elegido` | `boolean` | `TRUE` en el método ingenuo. | — |
| `nivel_geografico` | `text` | Siempre `CDMX`. | — |
| `fuente` | `text` | La del DENUE histórico. | — |

> Los intervalos son **asimétricos a propósito**: la serie nunca ha subido de forma
> relevante, así que el riesgo es solo a la baja. El pronóstico no anticipa los 300 Centros
> de Cuidado Infantil anunciados en 09/2026 ni los Censos Económicos 2029.

## `indicadores.validacion_modelos`

**Para qué sirve en el tablero.** Justificar por qué se eligió cada modelo. Dos tareas:
el pronóstico de la oferta (MAPE, RMSE y MAE con origen móvil) y el modelo de horas de
cuidado (RMSE, MAE y R² con mujeres individuales; MAPE, RMSE, MAE y R² al predecir el
promedio de una entidad que el modelo no vio).

**Filas esperadas:** 56.

| Columna | Tipo | Descripción | Unidad |
|---|---|---|---|
| `modelo` | `text` **PK** | Modelo evaluado. | — |
| `tarea` | `text` **PK** | Qué se predice. | — |
| `conjunto` | `text` **PK** | Esquema de validación: `Origen móvil`, `Prueba (20 %)`, `Validación cruzada (5 pliegues)`, `Dejando fuera una entidad (32)`. | — |
| `metrica` | `text` **PK** | `MAPE` (en %), `RMSE`, `MAE` o `R2`. | — |
| `valor` | `numeric(12,3)` | Valor de la métrica, en las unidades de la tarea. | según `metrica` |
| `n_evaluaciones` | `integer` | Pronósticos, pliegues o casos que sostienen la métrica. | — |
| `elegido` | `boolean` | `TRUE` en el modelo elegido de cada tarea. | — |
| `nivel_geografico` | `text` | `CDMX` (pronóstico) o `Nacional` (modelo de horas). | — |
| `fuente` | `text` | Fuente de los datos validados. | — |

## `indicadores.modelo_horas_coeficientes`

**Para qué sirve en el tablero.** Explicar el modelo: cuántas horas semanales de cuidado
suma o resta cada característica del hogar de una mujer de 15 a 59 (regresión lineal
ponderada con `fac_per`, ENUT 2024, 30,301 mujeres de todo el país).

**Filas esperadas:** 12 (constante + 11 variables).

| Columna | Tipo | Descripción | Unidad |
|---|---|---|---|
| `variable` | `text` **PK** | Nombre en el notebook 03 (`n_0a5`, `ocupada`...). | — |
| `descripcion` | `text` | Qué mide. | — |
| `coeficiente` | `numeric(8,3)` | Horas semanales por unidad de la variable, con las demás fijas. | horas por semana |
| `variable_censo` | `text` | Cómo se construye con el Censo 2020 por AGEB. | — |
| `nivel_geografico` | `text` | Siempre `Nacional`. | — |
| `fuente` | `text` | `Modelo PP7 con INEGI, ENUT 2024`. | — |

## `indicadores.horas_cuidado_ageb`

**Para qué sirve en el tablero.** Las horas de cuidado no remunerado estimadas en cada una
de las 2,320 AGEB de `carga_ageb` (estimación en áreas pequeñas), calibradas para que la
CDMX dé el promedio de la ENUT (9.37 h por mujer de 15 a 59). Se une a `carga_ageb` por
`cvegeo_ageb` para tener coordenadas.

**Filas esperadas:** 2,320.

| Columna | Tipo | Descripción | Unidad |
|---|---|---|---|
| `cvegeo_ageb` | `text` **PK** | Llave territorial de 13 caracteres. | — |
| `cve_mun` | `text` | Clave de alcaldía. | — |
| `alcaldia` | `text` | Nombre de la alcaldía. | — |
| `mujeres_15a59` | `integer` | Mujeres de 15 a 59 (Censo 2020). | mujeres |
| `horas_mujer_semana` | `numeric(5,1)` | Horas semanales estimadas por mujer, incluyendo a las que no cuidan. | horas por semana |
| `horas_semana_total` | `integer` | `horas_mujer_semana` (sin redondear) × `mujeres_15a59`. Para sumar. | horas por semana |
| `alta_carga`, `sin_respaldo` | `boolean` | Iguales que en `carga_ageb`. | — |
| `variables_imputadas` | `boolean` | `TRUE` en 7 AGEB con alguna celda reservada, llenada con la mediana de su alcaldía. | — |
| `nivel_geografico` | `text` | Siempre `AGEB`. | — |
| `fuente` | `text` | `Modelo PP7 con INEGI, ENUT 2024 + Censo 2020`. | — |

## `indicadores.escenarios_programa`

**Para qué sirve en el tablero.** La factibilidad de la Red de Cuidado a Domicilio «Manos
que Cuidan» en las 25 AGEB de Iztapalapa sin respaldo: supuestos e indicadores (VAN, TIR,
payback, punto de equilibrio, requerimiento de capital) de los escenarios pesimista,
realista y optimista, más el valor esperado. Las reglas están en
`backend/observatorio/factibilidad.py`; el repositorio verifica al arrancar que el VAN
realista de la tabla coincida con ese módulo.

**Filas esperadas:** 74.

| Columna | Tipo | Descripción | Unidad |
|---|---|---|---|
| `escenario` | `text` **PK** | `Pesimista`, `Realista`, `Optimista`, `Valor esperado` o `Zona del programa`. | — |
| `indicador` | `text` **PK** | Indicador, o supuesto si empieza con `Supuesto:`. | — |
| `valor` | `numeric(14,2)` | Valor. `NULL` cuando no existe (TIR o payback de un flujo que no se recupera). Pesos constantes de 2026. | según `unidad` |
| `unidad` | `text` | Cómo leer el valor. | — |
| `nivel_geografico` | `text` | Siempre `AGEB`. | — |
| `fuente` | `text` | `Escenario simulado PP7 (backend/observatorio/factibilidad.py)`. | — |

---

# Cómo NO leer estos datos

Siete advertencias que hay que respetar en cualquier gráfica, texto o presentación que
salga de este repositorio. Las cinco primeras son del diagnóstico; la 6 y la 7, de la capa
analítica.

### 1. El DENUE cuenta establecimientos, no lugares disponibles

El DENUE es un **directorio**: registra que un establecimiento existe, no a cuántas
personas puede atender. Lo más cercano a un tamaño que publica es `per_ocu`, un rango de
personal ocupado, que no es capacidad.

**No se puede decir:** "la cobertura de guarderías en Iztapalapa es de X %".
**Sí se puede decir:** "en Iztapalapa hay N guarderías registradas en el DENUE" o "hay N
niñas y niños de 0 a 5 por cada guardería registrada".

Las columnas `ninos_0a5_por_guarderia` y `mayores_60_por_establecimiento` son razones de
**presión sobre la oferta**, no de cobertura. Y `COUNT(*)` sobre
`establecimientos_cuidado` da 1,463, pero solo 838 cuentan como respaldo: usa siempre
`WHERE es_respaldo`.

### 2. La ENASIC es nacional: no se puede atribuir a la CDMX

Los microdatos públicos de la ENASIC 2022 **no traen ninguna variable geográfica**. No
hay entidad, ni municipio, ni tamaño de localidad, ni en los datos abiertos ni en los
microdatos. Es la limitación más importante de esa fuente.

**No se puede decir:** "61.2 % de las cuidadoras de la CDMX prefiere el cuidado en casa".
**Sí se puede decir:** "61.2 % de las mujeres cuidadoras del país prefiere el cuidado en
casa (INEGI, ENASIC 2022, nacional)".

Tampoco se puede poner en un mapa de la ciudad ni mezclarse en un KPI junto a cifras de
la CDMX sin marcar la diferencia. Para eso está `nivel_geografico`.

### 3. Las zonas sin respaldo usan ubicaciones aproximadas

Hasta que se integre el **Marco Geoestadístico del INEGI**, el punto de referencia de cada
AGEB no es el centroide de su polígono: es la **mediana de las coordenadas de los
establecimientos del DENUE** que caen dentro. Eso sesga el punto hacia las zonas
comerciales y deja fuera las AGEB sin ningún establecimiento.

Mientras `carga_ageb.centroide_es_aproximado` valga `TRUE`, el hallazgo B (88 AGEB,
125,256 mujeres) se reporta como **exploratorio**, con esa salvedad escrita. Cuando se
carguen los polígonos en `curada.ageb_centroide_oficial` hay que recalcular y volver a
contar; el número puede cambiar, y un resultado distinto también es un resultado.

También conviene recordar que las AGEB urbanas no cubren la zona rural: en Milpa Alta
queda fuera el 16 % de la población. Los totales de `resumen_alcaldia` sí son completos.

### 4. Algunas cifras de la ENUT para la CDMX salen de menos de 100 casos

La ENUT es representativa por entidad, pero al bajar a la CDMX y partir por sexo y
actividad, la muestra se adelgaza rápido. Tres filas de `enut_carga_actividad` tienen
menos de 100 casos (marcadas con `precision_baja = TRUE`), y en
`enut_cuidado_por_grupo` hay dos grupos con menos de 60 (`confiable = FALSE`): mujeres
desocupadas (4 casos) y "otra situación" (20).

Esas cifras **no se citan como dato**, solo como indicio, y nunca sin la advertencia.
Las banderas son un semáforo simple por tamaño de muestra; el coeficiente de variación
formal, calculado con el diseño muestral (`est_dis`, `upm_dis`, `fac_per`), es trabajo
aparte sobre el microdato, y el criterio del INEGI es: CV menor a 15 % precisión alta,
de 15 a 30 % moderada, mayor a 30 % no publicable sin advertencia.

### 5. La unidad de análisis es la mujer cuidadora

La pregunta rectora del Observatorio es: *¿dónde y cuánto trabajo de cuidado recae sobre
las mujeres de la CDMX, y qué tanto lo alivia la oferta de cuidados que tienen cerca?*

Los datos de hombres (`enut_carga_actividad` con `sexo = 'Hombres'`,
`enut_brecha_mujeres_cdmx.horas_hombres_ref`, la fila `Hombres ocupados (ref.)` de
`enut_doble_jornada`) existen **únicamente para dimensionar la brecha**. No son un tema
del Observatorio y no deben encabezar una gráfica, un título ni una conclusión. El
sufijo `_ref` y la etiqueta `(ref.)` están puestos justamente para recordarlo.

### 6. Las horas por AGEB son una estimación, no una medición

`horas_cuidado_ageb` aplica un modelo de la ENUT a las variables del Censo. Su error al
predecir el promedio de una entidad es de ~8 % (MAPE); en una AGEB será mayor. Ordena bien
las zonas, pero no da una cifra exacta para ninguna.

**No se puede decir:** «en la AGEB X las mujeres cuidan 10.4 horas a la semana».
**Sí se puede decir:** «el modelo estima que en las 88 AGEB sin respaldo las mujeres cuidan
alrededor de 10 horas a la semana cada una, más que el promedio de la ciudad».

### 7. Los escenarios del programa son simulados

El programa, su operador y su convenio de subsidio no existen: son el escenario simulado que
el equipo acordó al no tener institución de partida. Los supuestos tienen fuente, pero el VAN
y la TIR son resultados de un modelo, no de una operación real.

**No se puede decir:** «la red de cuidado tiene un VAN de $0.49 millones».
**Sí se puede decir:** «en el escenario realista simulado, con un subsidio de $40 por hora, la
red tendría un VAN de $0.49 millones a 60 meses».
