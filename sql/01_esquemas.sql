-- =============================================================================
-- Observatorio de la Economía del Cuidado — PP7 UNRC
-- Esquemas y tablas de las capas `curada` e indicadores.
--
-- Se ejecuta solo, al levantar el contenedor de PostgreSQL por primera vez
-- (va montado en /docker-entrypoint-initdb.d/). Es idempotente: se puede volver
-- a correr sin borrar nada.
--
-- Las tablas del esquema `cruda` NO se definen aquí: las crea el trabajo de
-- Spark al cargar los CSV, con todas las columnas TEXT y 1:1 con el archivo.
--
-- Convenciones de tipos, iguales en todo el archivo:
--   * Claves geográficas (cvegeo_ageb, cve_ent, cve_mun, cve_loc, ageb) -> TEXT.
--     NUNCA numéricas: '09' se volvería 9 y se perdería el cero a la izquierda,
--     y 222 de las 2,433 AGEB de la CDMX son alfanuméricas (p. ej. '003A').
--   * Porcentajes y tasas -> NUMERIC(_,1), un decimal.
--   * Conteos -> INTEGER, nulos permitidos (ver nota sobre confidencialidad).
--   * Coordenadas -> DOUBLE PRECISION.
--
-- Sobre los nulos: el Censo 2020 reserva por confidencialidad algunas celdas y
-- las publica como '*'. Entran como NULL, nunca como 0. Si entraran como 0, los
-- indicadores de carga de cuidado bajarían sin que nadie lo notara.
--
-- Sobre las llaves foráneas: a propósito no hay ninguna. El trabajo de Spark
-- escribe con TRUNCATE + append, y PostgreSQL no deja truncar una tabla
-- referenciada por un FOREIGN KEY. Las relaciones entre tablas quedan
-- documentadas en los COMMENT de cada columna.
-- =============================================================================


-- =============================================================================
-- 1. ESQUEMAS
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS cruda;
CREATE SCHEMA IF NOT EXISTS curada;
CREATE SCHEMA IF NOT EXISTS indicadores;

COMMENT ON SCHEMA cruda IS
    'Carga 1:1 de los CSV de data/curada/. Todas las columnas TEXT, sin limpiar. '
    'Sirve para auditar: cualquier cifra del tablero se puede rastrear hasta aquí. '
    'Estas tablas las crea Spark, no este archivo.';

COMMENT ON SCHEMA curada IS
    'Entidades con tipos correctos y llave primaria: establecimientos del DENUE, '
    'AGEB y alcaldías del Censo. Una fila por entidad del mundo real.';

COMMENT ON SCHEMA indicadores IS
    'Tablas listas para el tablero: ya agregadas, ya cruzadas y con el contexto '
    'necesario para citar cada cifra (nivel_geografico y fuente). El tablero lee '
    'de aquí y de ningún otro esquema.';


-- =============================================================================
-- 2. CAPA CURADA
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 2.1 Establecimientos de cuidado del DENUE
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS curada.denue_cuidado (
    id              TEXT PRIMARY KEY,
    nom_estab       TEXT,
    codigo_act      TEXT NOT NULL,
    nombre_act      TEXT NOT NULL,
    grupo           TEXT NOT NULL,
    tipo            TEXT NOT NULL,
    sector          TEXT NOT NULL,
    per_ocu         TEXT,
    cve_ent         TEXT NOT NULL,
    cve_mun         TEXT NOT NULL,
    municipio       TEXT NOT NULL,
    cvegeo_ageb     TEXT NOT NULL,
    cvegeo_valido   BOOLEAN NOT NULL,
    es_respaldo     BOOLEAN NOT NULL,
    lat             DOUBLE PRECISION NOT NULL,
    lon             DOUBLE PRECISION NOT NULL,
    fecha_alta      DATE
);

COMMENT ON TABLE curada.denue_cuidado IS
    'Establecimientos de cuidado de la CDMX según el DENUE 05/2026 (1,463 filas). '
    'Es un directorio de establecimientos, NO de capacidad: el DENUE no publica '
    'lugares disponibles. Por eso nunca se debe hablar de "cobertura" con esta tabla.';

COMMENT ON COLUMN curada.denue_cuidado.id IS
    'Clave única del establecimiento en el DENUE. TEXT aunque parezca número: es un '
    'identificador de registro, no una cantidad.';
COMMENT ON COLUMN curada.denue_cuidado.nom_estab IS
    'Nombre comercial. Puede ser NULL: hay establecimientos sin nombre registrado.';
COMMENT ON COLUMN curada.denue_cuidado.codigo_act IS
    'Código SCIAN de 6 dígitos. TEXT para no perder ceros a la izquierda. '
    'En estos datos hay 14 códigos distintos.';
COMMENT ON COLUMN curada.denue_cuidado.nombre_act IS
    'Descripción oficial del código SCIAN, tal como la publica el INEGI.';
COMMENT ON COLUMN curada.denue_cuidado.grupo IS
    'Agrupación propia del proyecto: Infancia, Personas mayores, Personas mayores y '
    'discapacidad, Salud y discapacidad, Asistencia social, Apoyo comunitario.';
COMMENT ON COLUMN curada.denue_cuidado.tipo IS
    'Subtipo dentro del grupo: Guardería, Residencia / asilo, Centro de día, '
    'Comedor comunitario, Orfanato / residencia asistencial, etc.';
COMMENT ON COLUMN curada.denue_cuidado.sector IS
    'Público o Privado, según el código SCIAN (los códigos pares son públicos).';
COMMENT ON COLUMN curada.denue_cuidado.per_ocu IS
    'Rango de personal ocupado, en texto ("0 a 5 personas", "11 a 30 personas"...). '
    'Es lo más cercano a un tamaño que publica el DENUE; NO es capacidad de atención.';
COMMENT ON COLUMN curada.denue_cuidado.cve_ent IS
    'Clave de entidad federativa, 2 caracteres. Siempre 09 (CDMX).';
COMMENT ON COLUMN curada.denue_cuidado.cve_mun IS
    'Clave de alcaldía, 3 caracteres con ceros a la izquierda. Relaciona con '
    'curada.censo_alcaldia.cve_mun.';
COMMENT ON COLUMN curada.denue_cuidado.municipio IS
    'Nombre de la alcaldía. Redundante con cve_mun, se conserva para leer la tabla '
    'sin hacer join.';
COMMENT ON COLUMN curada.denue_cuidado.cvegeo_ageb IS
    'CVEGEO del AGEB donde cae el establecimiento: entidad(2) + municipio(3) + '
    'localidad(4) + AGEB(4) = 13 caracteres. Relaciona con curada.censo_ageb.';
COMMENT ON COLUMN curada.denue_cuidado.cvegeo_valido IS
    'FALSE cuando el cvegeo_ageb no empata con ningún AGEB urbana del Censo 2020 '
    '(6 claves de 978). Suelen ser AGEB rurales o claves mal capturadas. Los cruces '
    'contra el Censo deben usar LEFT JOIN y filtrar por esta bandera.';
COMMENT ON COLUMN curada.denue_cuidado.es_respaldo IS
    'TRUE si el establecimiento cuenta como respaldo de cuidado para el hallazgo B: '
    'guarderías (624411, 624412), residencias y asilos de personas mayores (623311, '
    '623312) y centros de día (624121, 624122). Son 838 de los 1,463. '
    'IMPORTANTE: contar la tabla completa da 1,463 y contradice el hallazgo. '
    'Los comedores comunitarios, orfanatos y residencias de enfermería están en la '
    'tabla pero NO sustituyen horas de cuidado en el hogar.';
COMMENT ON COLUMN curada.denue_cuidado.lat IS 'Latitud en grados decimales, WGS84.';
COMMENT ON COLUMN curada.denue_cuidado.lon IS 'Longitud en grados decimales, WGS84.';
COMMENT ON COLUMN curada.denue_cuidado.fecha_alta IS
    'Fecha de alta del establecimiento EN EL DIRECTORIO, no de apertura del negocio. '
    'El DENUE la publica como AAAA-MM; aquí se guarda con día 01.';

CREATE INDEX IF NOT EXISTS ix_denue_cuidado_ageb     ON curada.denue_cuidado (cvegeo_ageb);
CREATE INDEX IF NOT EXISTS ix_denue_cuidado_mun      ON curada.denue_cuidado (cve_mun);
CREATE INDEX IF NOT EXISTS ix_denue_cuidado_respaldo ON curada.denue_cuidado (es_respaldo) WHERE es_respaldo;


-- -----------------------------------------------------------------------------
-- 2.2 Censo 2020 por AGEB — bloque general
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS curada.censo_ageb (
    cvegeo_ageb             TEXT PRIMARY KEY,
    cve_ent                 TEXT NOT NULL,
    cve_mun                 TEXT NOT NULL,
    nom_mun                 TEXT NOT NULL,
    cve_loc                 TEXT NOT NULL,
    ageb                    TEXT NOT NULL,
    pob_total               INTEGER,
    pob_0a2                 INTEGER,
    pob_3a5                 INTEGER,
    pob_0a5                 INTEGER,
    pob_60mas               INTEGER,
    pob_65mas               INTEGER,
    pob_discapacidad        INTEGER,
    pob_disc_autocuidado    INTEGER,
    pob_3a5_no_escuela      INTEGER,
    pob_sin_serv_salud      INTEGER,
    hogares                 INTEGER,
    hogares_jefa            INTEGER,
    tiene_centroide         BOOLEAN NOT NULL
);

COMMENT ON TABLE curada.censo_ageb IS
    'Las 2,433 AGEB urbanas de la CDMX según el Censo de Población y Vivienda 2020. '
    'Es el universo canónico de AGEB del proyecto: cualquier porcentaje a nivel AGEB '
    'debe tener esta tabla como denominador. '
    'OJO: las AGEB urbanas no cubren las zonas rurales. En Milpa Alta queda fuera el '
    '16% de la población. Los totales por alcaldía (curada.censo_alcaldia) sí son completos.';

COMMENT ON COLUMN curada.censo_ageb.cvegeo_ageb IS
    'Llave territorial del proyecto: entidad(2) + municipio(3) + localidad(4) + '
    'AGEB(4) = exactamente 13 caracteres. TEXT siempre.';
COMMENT ON COLUMN curada.censo_ageb.cve_ent IS 'Clave de entidad, 2 caracteres. Siempre 09.';
COMMENT ON COLUMN curada.censo_ageb.cve_mun IS
    'Clave de alcaldía, 3 caracteres. Relaciona con curada.censo_alcaldia.cve_mun.';
COMMENT ON COLUMN curada.censo_ageb.nom_mun IS 'Nombre de la alcaldía, con acentos.';
COMMENT ON COLUMN curada.censo_ageb.cve_loc IS 'Clave de localidad, 4 caracteres.';
COMMENT ON COLUMN curada.censo_ageb.ageb IS
    'Clave del AGEB dentro de la localidad, 4 caracteres. Es ALFANUMÉRICA: 222 de '
    'las 2,433 terminan en letra (p. ej. 003A). Leerla como número las destruye.';
COMMENT ON COLUMN curada.censo_ageb.pob_total IS 'Población total del AGEB (POBTOT).';
COMMENT ON COLUMN curada.censo_ageb.pob_0a2 IS 'Población de 0 a 2 años (P_0A2).';
COMMENT ON COLUMN curada.censo_ageb.pob_3a5 IS 'Población de 3 a 5 años (P_3A5).';
COMMENT ON COLUMN curada.censo_ageb.pob_0a5 IS
    'Población de 0 a 5 años, suma de P_0A2 y P_3A5. Es NULL si cualquiera de los '
    'dos sumandos viene reservado por confidencialidad.';
COMMENT ON COLUMN curada.censo_ageb.pob_60mas IS 'Población de 60 años y más.';
COMMENT ON COLUMN curada.censo_ageb.pob_65mas IS 'Población de 65 años y más.';
COMMENT ON COLUMN curada.censo_ageb.pob_discapacidad IS
    'Población con alguna discapacidad, cualquier tipo.';
COMMENT ON COLUMN curada.censo_ageb.pob_disc_autocuidado IS
    'Población con discapacidad para vestirse, bañarse o comer (PCDISC_MOT2). Es la '
    'variable que aproxima la necesidad de cuidado directo. 48 AGEB la traen '
    'reservada por confidencialidad y quedan en NULL.';
COMMENT ON COLUMN curada.censo_ageb.pob_3a5_no_escuela IS
    'Población de 3 a 5 años que no asiste a la escuela. 105 AGEB en NULL.';
COMMENT ON COLUMN curada.censo_ageb.pob_sin_serv_salud IS
    'Población sin afiliación a servicios de salud.';
COMMENT ON COLUMN curada.censo_ageb.hogares IS 'Total de hogares censales (TOTHOG).';
COMMENT ON COLUMN curada.censo_ageb.hogares_jefa IS
    'Hogares con jefatura femenina (HOGJEF_F).';
COMMENT ON COLUMN curada.censo_ageb.tiene_centroide IS
    'TRUE si el AGEB entra en el análisis territorial (2,320 de 2,433), es decir, si '
    'aparece en curada.censo_ageb_mujeres y en indicadores.carga_ageb. '
    'El embudo completo del notebook es 2,433 AGEB urbanas -> 2,326 con al menos 100 '
    'mujeres de 15 a 59 y carga no nula -> 2,320 con centroide. El paso intermedio de '
    '2,326 NO se puede reconstruir desde los CSV de data/curada/, porque las variables '
    'de mujeres solo vienen en la tabla ya filtrada a 2,320; habría que volver al '
    'microdato del Censo. Por eso aquí solo se distingue 2,433 contra 2,320.';

CREATE INDEX IF NOT EXISTS ix_censo_ageb_mun ON curada.censo_ageb (cve_mun);


-- -----------------------------------------------------------------------------
-- 2.3 Censo 2020 por AGEB — bloque de mujeres
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS curada.censo_ageb_mujeres (
    cvegeo_ageb                 TEXT PRIMARY KEY,
    cve_mun                     TEXT NOT NULL,
    nom_mun                     TEXT NOT NULL,
    pob_total                   INTEGER,
    pob_femenina                INTEGER,
    p_0a2                       INTEGER,
    p_3a5                       INTEGER,
    pob_0a5                     INTEGER,
    p_15ymas_f                  INTEGER,
    p_60ymas_f                  INTEGER,
    p_12ymas_f                  INTEGER,
    pcdisc_mot2                 INTEGER,
    pe_inac_f                   INTEGER,
    pea_f                       INTEGER,
    tothog                      INTEGER,
    hogjef_f                    INTEGER,
    mujeres_15a59               INTEGER,
    carga_directa_x100_mujeres  NUMERIC(5,1),
    pct_hog_jefa                NUMERIC(5,1),
    pct_mujeres_inactivas       NUMERIC(5,1),
    lat_aprox                   DOUBLE PRECISION,
    lon_aprox                   DOUBLE PRECISION
);

COMMENT ON TABLE curada.censo_ageb_mujeres IS
    'Variables del Censo 2020 centradas en la mujer, para las 2,320 AGEB con '
    'centroide. Es un subconjunto de curada.censo_ageb: no sirve para calcular '
    'totales de la CDMX, solo para rankings y mapas.';

COMMENT ON COLUMN curada.censo_ageb_mujeres.cvegeo_ageb IS
    'Llave de 13 caracteres. Relaciona con curada.censo_ageb.cvegeo_ageb.';
COMMENT ON COLUMN curada.censo_ageb_mujeres.cve_mun IS 'Clave de alcaldía, 3 caracteres.';
COMMENT ON COLUMN curada.censo_ageb_mujeres.nom_mun IS 'Nombre de la alcaldía.';
COMMENT ON COLUMN curada.censo_ageb_mujeres.pob_total IS 'Población total (POBTOT).';
COMMENT ON COLUMN curada.censo_ageb_mujeres.pob_femenina IS 'Población femenina total (POBFEM).';
COMMENT ON COLUMN curada.censo_ageb_mujeres.p_0a2 IS 'Población de 0 a 2 años.';
COMMENT ON COLUMN curada.censo_ageb_mujeres.p_3a5 IS 'Población de 3 a 5 años.';
COMMENT ON COLUMN curada.censo_ageb_mujeres.pob_0a5 IS
    'Población de 0 a 5 años. Numerador, junto con pcdisc_mot2, de la carga de cuidado.';
COMMENT ON COLUMN curada.censo_ageb_mujeres.p_15ymas_f IS 'Mujeres de 15 años y más.';
COMMENT ON COLUMN curada.censo_ageb_mujeres.p_60ymas_f IS 'Mujeres de 60 años y más.';
COMMENT ON COLUMN curada.censo_ageb_mujeres.p_12ymas_f IS
    'Mujeres de 12 años y más. Denominador de pct_mujeres_inactivas.';
COMMENT ON COLUMN curada.censo_ageb_mujeres.pcdisc_mot2 IS
    'Personas con discapacidad para vestirse, bañarse o comer. Aproxima la necesidad '
    'de cuidado directo de las personas mayores y con discapacidad.';
COMMENT ON COLUMN curada.censo_ageb_mujeres.pe_inac_f IS
    'Mujeres económicamente NO activas (PE_INAC_F).';
COMMENT ON COLUMN curada.censo_ageb_mujeres.pea_f IS
    'Mujeres económicamente activas (PEA_F).';
COMMENT ON COLUMN curada.censo_ageb_mujeres.tothog IS 'Total de hogares.';
COMMENT ON COLUMN curada.censo_ageb_mujeres.hogjef_f IS 'Hogares con jefatura femenina.';
COMMENT ON COLUMN curada.censo_ageb_mujeres.mujeres_15a59 IS
    'Mujeres de 15 a 59 años, calculado como P_15YMAS_F menos P_60YMAS_F. Es la '
    'población en edad de cuidar y el denominador del indicador de carga.';
COMMENT ON COLUMN curada.censo_ageb_mujeres.carga_directa_x100_mujeres IS
    'Personas que necesitan cuidado directo por cada 100 mujeres de 15 a 59: '
    '(pob_0a5 + pcdisc_mot2) / mujeres_15a59 * 100. Rango observado: 1.1 a 37.5. '
    'No incluye a toda la población de 60+, porque la mayoría es autónoma.';
COMMENT ON COLUMN curada.censo_ageb_mujeres.pct_hog_jefa IS
    '% de hogares con jefatura femenina: hogjef_f / tothog * 100.';
COMMENT ON COLUMN curada.censo_ageb_mujeres.pct_mujeres_inactivas IS
    '% de mujeres de 12+ fuera del mercado laboral: pe_inac_f / p_12ymas_f * 100. '
    'Leer con cuidado: incluye estudiantes y jubiladas.';
COMMENT ON COLUMN curada.censo_ageb_mujeres.lat_aprox IS
    'Latitud APROXIMADA del AGEB: mediana de las coordenadas de los establecimientos '
    'del DENUE que caen dentro. NO es el centroide del polígono. Sesga el punto hacia '
    'las zonas comerciales. Se sustituye con curada.ageb_centroide_oficial cuando '
    'esté cargado el Marco Geoestadístico.';
COMMENT ON COLUMN curada.censo_ageb_mujeres.lon_aprox IS
    'Longitud aproximada. Misma advertencia que lat_aprox.';

CREATE INDEX IF NOT EXISTS ix_censo_ageb_mujeres_mun ON curada.censo_ageb_mujeres (cve_mun);


-- -----------------------------------------------------------------------------
-- 2.4 Censo 2020 por alcaldía
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS curada.censo_alcaldia (
    cve_mun                 TEXT PRIMARY KEY,
    cve_ent                 TEXT NOT NULL,
    alcaldia                TEXT NOT NULL UNIQUE,
    pob_total               INTEGER NOT NULL,
    pob_0a2                 INTEGER,
    pob_3a5                 INTEGER,
    pob_0a5                 INTEGER,
    pob_60mas               INTEGER,
    pob_65mas               INTEGER,
    pob_discapacidad        INTEGER,
    pob_disc_autocuidado    INTEGER,
    pob_3a5_no_escuela      INTEGER,
    pob_sin_serv_salud      INTEGER,
    hogares                 INTEGER,
    hogares_jefa            INTEGER
);

COMMENT ON TABLE curada.censo_alcaldia IS
    'Totales del Censo 2020 para las 16 alcaldías de la CDMX. A diferencia de '
    'curada.censo_ageb, estos totales SÍ incluyen la población rural, así que son '
    'los correctos para cualquier cifra por alcaldía o del conjunto de la ciudad.';

COMMENT ON COLUMN curada.censo_alcaldia.cve_mun IS
    'Clave de alcaldía, 3 caracteres con ceros a la izquierda (002 a 017). Es la '
    'llave con la que se unen todas las tablas por alcaldía.';
COMMENT ON COLUMN curada.censo_alcaldia.cve_ent IS 'Clave de entidad, 2 caracteres. Siempre 09.';
COMMENT ON COLUMN curada.censo_alcaldia.alcaldia IS
    'Nombre oficial de la alcaldía, con acentos (p. ej. Álvaro Obregón, Tláhuac). '
    'UNIQUE porque varias tablas de origen solo traen el nombre y se unen por él; '
    'por eso la base debe estar en UTF-8.';
COMMENT ON COLUMN curada.censo_alcaldia.pob_total IS 'Población total de la alcaldía.';
COMMENT ON COLUMN curada.censo_alcaldia.pob_0a2 IS 'Población de 0 a 2 años.';
COMMENT ON COLUMN curada.censo_alcaldia.pob_3a5 IS 'Población de 3 a 5 años.';
COMMENT ON COLUMN curada.censo_alcaldia.pob_0a5 IS 'Población de 0 a 5 años.';
COMMENT ON COLUMN curada.censo_alcaldia.pob_60mas IS 'Población de 60 años y más.';
COMMENT ON COLUMN curada.censo_alcaldia.pob_65mas IS 'Población de 65 años y más.';
COMMENT ON COLUMN curada.censo_alcaldia.pob_discapacidad IS
    'Población con alguna discapacidad.';
COMMENT ON COLUMN curada.censo_alcaldia.pob_disc_autocuidado IS
    'Población con discapacidad para vestirse, bañarse o comer.';
COMMENT ON COLUMN curada.censo_alcaldia.pob_3a5_no_escuela IS
    'Población de 3 a 5 años que no asiste a la escuela.';
COMMENT ON COLUMN curada.censo_alcaldia.pob_sin_serv_salud IS
    'Población sin afiliación a servicios de salud.';
COMMENT ON COLUMN curada.censo_alcaldia.hogares IS 'Total de hogares.';
COMMENT ON COLUMN curada.censo_alcaldia.hogares_jefa IS 'Hogares con jefatura femenina.';


-- -----------------------------------------------------------------------------
-- 2.5 Centroides oficiales de AGEB (pendiente de cargar)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS curada.ageb_centroide_oficial (
    cvegeo_ageb     TEXT PRIMARY KEY,
    lat             DOUBLE PRECISION NOT NULL,
    lon             DOUBLE PRECISION NOT NULL,
    fuente_capa     TEXT
);

COMMENT ON TABLE curada.ageb_centroide_oficial IS
    'Centroides reales de las AGEB, calculados sobre los polígonos del Marco '
    'Geoestadístico del INEGI (capa 09a). SE CREA VACÍA a propósito (pendiente: '
    'integración del Marco Geoestadístico). Mientras esté vacía, los conteos a 1 km '
    'usan los centroides aproximados de curada.censo_ageb_mujeres.lat_aprox, que son '
    'exploratorios. '
    'Cuando se llene hay que recalcular el hallazgo B y volver a contar las 88 AGEB.';

COMMENT ON COLUMN curada.ageb_centroide_oficial.cvegeo_ageb IS
    'Llave de 13 caracteres. Debe empatar con curada.censo_ageb.cvegeo_ageb; hay que '
    'reportar cuántas AGEB empatan y cuántas no.';
COMMENT ON COLUMN curada.ageb_centroide_oficial.lat IS
    'Latitud del centroide del polígono, en grados decimales WGS84. El cálculo se '
    'hace proyectando a EPSG:6372 (México ITRF2008 / LCC) y se reproyecta de vuelta.';
COMMENT ON COLUMN curada.ageb_centroide_oficial.lon IS 'Longitud del centroide, WGS84.';
COMMENT ON COLUMN curada.ageb_centroide_oficial.fuente_capa IS
    'Nombre y versión del archivo del Marco Geoestadístico del que salió la geometría.';


-- =============================================================================
-- 3. CAPA INDICADORES
--
-- Todas las tablas llevan nivel_geografico y fuente. No son decorativas: impiden
-- que alguien ponga en un mapa de la CDMX una cifra que es nacional. La ENASIC
-- no trae NINGUNA variable geográfica en sus microdatos públicos, así que todo
-- lo suyo es nacional y nunca se puede desagregar por alcaldía.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 3.1 KPIs generales de la CDMX
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS indicadores.kpi_cdmx (
    clave               TEXT PRIMARY KEY,
    etiqueta            TEXT NOT NULL,
    valor_num           NUMERIC(12,1),
    valor_texto         TEXT,
    unidad              TEXT NOT NULL,
    nivel_geografico    TEXT NOT NULL
        CHECK (nivel_geografico IN ('AGEB', 'Alcaldía', 'CDMX', 'Nacional')),
    fuente              TEXT NOT NULL,
    CONSTRAINT kpi_cdmx_tiene_valor CHECK (valor_num IS NOT NULL OR valor_texto IS NOT NULL)
);

COMMENT ON TABLE indicadores.kpi_cdmx IS
    'Las cifras de cabecera del Observatorio: la tira de KPIs del tablero. Trece '
    'filas, una por cifra citable: doce salen de data/curada/resumen_cifras_clave.csv '
    'y la decimotercera, la brecha de trabajo no pagado, la calcula el ETL desde la '
    'columna sin redondear de la doble jornada. Sirve también como prueba de '
    'regresión del ETL: si cambia un valor sin que nadie haya tocado el método, algo '
    'se rompió. Valores de control: 62.2% de mujeres que cuidan, 77.0 h de jornada de '
    'las mujeres ocupadas, 12.7 h de brecha de trabajo no pagado, 88 AGEB sin '
    'respaldo, 61.2% que prefiere cuidado en casa.';

COMMENT ON COLUMN indicadores.kpi_cdmx.clave IS
    'Identificador estable de la cifra, con el prefijo de la fuente '
    '(p. ej. "ENUT · % mujeres CDMX que cuidan"). El tablero referencia por aquí.';
COMMENT ON COLUMN indicadores.kpi_cdmx.etiqueta IS
    'Texto legible para mostrar en pantalla, sin el prefijo de la fuente.';
COMMENT ON COLUMN indicadores.kpi_cdmx.valor_num IS
    'Valor numérico de la cifra. NULL cuando el KPI es cualitativo.';
COMMENT ON COLUMN indicadores.kpi_cdmx.valor_texto IS
    'Valor de texto, para los KPI que no son números (p. ej. "Milpa Alta" como la '
    'alcaldía con mayor carga). NULL cuando el KPI es numérico.';
COMMENT ON COLUMN indicadores.kpi_cdmx.unidad IS
    'Unidad en la que se expresa el valor: "%", "horas por semana", "AGEB", '
    '"mujeres", "personas por cada 100 mujeres" o "texto". El tablero la usa para '
    'formatear; sin ella un 62.2 y un 77.0 se ven igual.';
COMMENT ON COLUMN indicadores.kpi_cdmx.nivel_geografico IS
    'Territorio al que se refiere la cifra. Las de ENUT y Censo son CDMX; las de '
    'ENASIC son Nacional y NO se pueden presentar como cifras de la ciudad.';
COMMENT ON COLUMN indicadores.kpi_cdmx.fuente IS
    'Fuente citable, con año (p. ej. "INEGI, ENUT 2024"). Ninguna cifra se publica '
    'sin fuente, año y nivel geográfico.';


-- -----------------------------------------------------------------------------
-- 3.2 Resumen por alcaldía
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS indicadores.resumen_alcaldia (
    cve_mun                             TEXT PRIMARY KEY,
    alcaldia                            TEXT NOT NULL,
    pob_total                           INTEGER NOT NULL,
    mujeres_15a59                       INTEGER,
    pct_60mas                           NUMERIC(5,1),
    carga_directa_x100_mujeres          NUMERIC(5,1),
    rango_carga                         INTEGER,
    pct_hog_jefa                        NUMERIC(5,1),
    pct_mujeres_inactivas               NUMERIC(5,1),
    agebs                               INTEGER,
    agebs_alta_carga                    INTEGER,
    agebs_sin_respaldo                  INTEGER,
    mujeres_sin_respaldo                INTEGER,
    pct_agebs_alta_carga_sin_respaldo   NUMERIC(5,1),
    guarderias                          INTEGER,
    cuidado_mayores                     INTEGER,
    ninos_0a5_por_guarderia             NUMERIC(10,1),
    mayores_60_por_establecimiento      NUMERIC(10,1),
    pct_guarderias_publicas             NUMERIC(5,1),
    nivel_geografico                    TEXT NOT NULL
        CHECK (nivel_geografico IN ('AGEB', 'Alcaldía', 'CDMX', 'Nacional')),
    fuente                              TEXT NOT NULL
);

COMMENT ON TABLE indicadores.resumen_alcaldia IS
    'Una fila por alcaldía (16) con todo lo que el tablero necesita para la vista '
    'territorial: demanda de cuidado, oferta formal y zonas sin respaldo. Es el '
    'cruce de cuatro tablas de origen; evita que el tablero tenga que hacer joins.';

COMMENT ON COLUMN indicadores.resumen_alcaldia.cve_mun IS
    'Clave de alcaldía, 3 caracteres. Relaciona con curada.censo_alcaldia.';
COMMENT ON COLUMN indicadores.resumen_alcaldia.alcaldia IS 'Nombre de la alcaldía.';
COMMENT ON COLUMN indicadores.resumen_alcaldia.pob_total IS
    'Población total de la alcaldía, Censo 2020. Incluye zona rural.';
COMMENT ON COLUMN indicadores.resumen_alcaldia.mujeres_15a59 IS
    'Mujeres de 15 a 59 años: la población sobre la que recae el trabajo de cuidado.';
COMMENT ON COLUMN indicadores.resumen_alcaldia.pct_60mas IS
    '% de la población que tiene 60 años o más.';
COMMENT ON COLUMN indicadores.resumen_alcaldia.carga_directa_x100_mujeres IS
    'Personas con necesidad de cuidado directo por cada 100 mujeres de 15 a 59, '
    'calculado sobre los totales de la alcaldía. La CDMX en conjunto está en 21.6.';
COMMENT ON COLUMN indicadores.resumen_alcaldia.rango_carga IS
    'Posición de la alcaldía por carga de cuidado: 1 es la más alta (Milpa Alta).';
COMMENT ON COLUMN indicadores.resumen_alcaldia.pct_hog_jefa IS
    '% de hogares con jefatura femenina.';
COMMENT ON COLUMN indicadores.resumen_alcaldia.pct_mujeres_inactivas IS
    '% de mujeres de 12+ fuera del mercado laboral.';
COMMENT ON COLUMN indicadores.resumen_alcaldia.agebs IS
    'AGEB de la alcaldía incluidas en el análisis territorial (las que tienen '
    'centroide). Suman 2,320 en toda la ciudad, no 2,433.';
COMMENT ON COLUMN indicadores.resumen_alcaldia.agebs_alta_carga IS
    'AGEB en el cuartil superior de carga de cuidado de toda la ciudad (umbral: 24.1 '
    'personas por cada 100 mujeres). Suman 580.';
COMMENT ON COLUMN indicadores.resumen_alcaldia.agebs_sin_respaldo IS
    'AGEB de alta carga y sin ninguna guardería, residencia ni centro de día a 1 km. '
    'Suman 88 en la ciudad; Iztapalapa concentra 25.';
COMMENT ON COLUMN indicadores.resumen_alcaldia.mujeres_sin_respaldo IS
    'Mujeres de 15 a 59 que viven en esas AGEB. Suman 125,256 en la ciudad.';
COMMENT ON COLUMN indicadores.resumen_alcaldia.pct_agebs_alta_carga_sin_respaldo IS
    '% de las AGEB de alta carga de la alcaldía que no tienen respaldo a 1 km. '
    'Es NULL, no 0, cuando la alcaldía no tiene ninguna AGEB de alta carga '
    '(es el caso de Benito Juárez): ahí el indicador no aplica.';
COMMENT ON COLUMN indicadores.resumen_alcaldia.guarderias IS
    'Guarderías del DENUE en la alcaldía (códigos 624411 y 624412).';
COMMENT ON COLUMN indicadores.resumen_alcaldia.cuidado_mayores IS
    'Residencias, asilos y centros de día para personas mayores en la alcaldía.';
COMMENT ON COLUMN indicadores.resumen_alcaldia.ninos_0a5_por_guarderia IS
    'Niñas y niños de 0 a 5 años por cada guardería. Es una razón de presión sobre '
    'la oferta, NO una medida de cobertura: el DENUE no publica capacidad.';
COMMENT ON COLUMN indicadores.resumen_alcaldia.mayores_60_por_establecimiento IS
    'Personas de 60+ por cada establecimiento de cuidado de personas mayores. '
    'Misma advertencia: es presión sobre la oferta, no cobertura.';
COMMENT ON COLUMN indicadores.resumen_alcaldia.pct_guarderias_publicas IS
    '% de las guarderías de la alcaldía que son del sector público.';
COMMENT ON COLUMN indicadores.resumen_alcaldia.nivel_geografico IS
    'Siempre "Alcaldía": cada fila describe una alcaldía de la CDMX.';
COMMENT ON COLUMN indicadores.resumen_alcaldia.fuente IS
    'Fuentes cruzadas en la fila, p. ej. "INEGI, Censo 2020 + DENUE 05/2026".';


-- -----------------------------------------------------------------------------
-- 3.3 Carga y acceso por AGEB (capa del mapa)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS indicadores.carga_ageb (
    cvegeo_ageb                 TEXT PRIMARY KEY,
    cve_mun                     TEXT NOT NULL,
    alcaldia                    TEXT NOT NULL,
    mujeres_15a59               INTEGER NOT NULL,
    pob_0a5                     INTEGER,
    pob_disc_autocuidado        INTEGER,
    carga_directa_x100_mujeres  NUMERIC(5,1) NOT NULL,
    pct_hog_jefa                NUMERIC(5,1),
    pct_mujeres_inactivas       NUMERIC(5,1),
    guarderias_1km              INTEGER NOT NULL,
    respaldo_total_1km          INTEGER NOT NULL,
    alta_carga                  BOOLEAN NOT NULL,
    sin_guarderia               BOOLEAN NOT NULL,
    sin_respaldo                BOOLEAN NOT NULL,
    lat                         DOUBLE PRECISION NOT NULL,
    lon                         DOUBLE PRECISION NOT NULL,
    centroide_es_aproximado     BOOLEAN NOT NULL,
    nivel_geografico            TEXT NOT NULL
        CHECK (nivel_geografico IN ('AGEB', 'Alcaldía', 'CDMX', 'Nacional')),
    fuente                      TEXT NOT NULL
);

COMMENT ON TABLE indicadores.carga_ageb IS
    'Una fila por AGEB (2,320) con carga de cuidado, oferta cercana y las banderas '
    'del hallazgo B. Es la capa que pinta el mapa del tablero. '
    'Son 2,320 y no 2,433 porque el embudo es: 2,433 AGEB urbanas -> 2,326 con al '
    'menos 100 mujeres de 15 a 59 y carga no nula -> 2,320 con centroide. '
    'Para porcentajes sobre el total de AGEB de la ciudad, usar curada.censo_ageb.';

COMMENT ON COLUMN indicadores.carga_ageb.cvegeo_ageb IS
    'Llave de 13 caracteres. Relaciona con curada.censo_ageb.';
COMMENT ON COLUMN indicadores.carga_ageb.cve_mun IS 'Clave de alcaldía, 3 caracteres.';
COMMENT ON COLUMN indicadores.carga_ageb.alcaldia IS 'Nombre de la alcaldía.';
COMMENT ON COLUMN indicadores.carga_ageb.mujeres_15a59 IS
    'Mujeres de 15 a 59 que viven en el AGEB. Mínimo 100 por construcción.';
COMMENT ON COLUMN indicadores.carga_ageb.pob_0a5 IS
    'Población de 0 a 5 años. Parte del numerador de la carga.';
COMMENT ON COLUMN indicadores.carga_ageb.pob_disc_autocuidado IS
    'Personas con discapacidad para vestirse, bañarse o comer. La otra parte del '
    'numerador de la carga.';
COMMENT ON COLUMN indicadores.carga_ageb.carga_directa_x100_mujeres IS
    'Personas con necesidad de cuidado directo por cada 100 mujeres de 15 a 59. '
    'Es la variable que colorea el mapa.';
COMMENT ON COLUMN indicadores.carga_ageb.pct_hog_jefa IS
    '% de hogares con jefatura femenina en el AGEB.';
COMMENT ON COLUMN indicadores.carga_ageb.pct_mujeres_inactivas IS
    '% de mujeres de 12+ fuera del mercado laboral en el AGEB.';
COMMENT ON COLUMN indicadores.carga_ageb.guarderias_1km IS
    'Guarderías del DENUE a menos de 1 km del centroide (≈ 12 a 15 min a pie).';
COMMENT ON COLUMN indicadores.carga_ageb.respaldo_total_1km IS
    'Guarderías + residencias y asilos + centros de día a menos de 1 km. Cuenta solo '
    'los establecimientos con curada.denue_cuidado.es_respaldo = TRUE.';
COMMENT ON COLUMN indicadores.carga_ageb.alta_carga IS
    'TRUE si el AGEB está en el cuartil superior de carga de la ciudad (>= 24.1 '
    'personas con necesidad de cuidado por cada 100 mujeres). Son 580.';
COMMENT ON COLUMN indicadores.carga_ageb.sin_guarderia IS
    'TRUE si es de alta carga y no tiene ninguna guardería a 1 km. Son 131.';
COMMENT ON COLUMN indicadores.carga_ageb.sin_respaldo IS
    'Hallazgo B: TRUE si es de alta carga y no tiene ningún respaldo a 1 km. '
    'Son 88 AGEB, donde viven 125,256 mujeres de 15 a 59.';
COMMENT ON COLUMN indicadores.carga_ageb.lat IS
    'Latitud del punto de referencia del AGEB, grados decimales WGS84.';
COMMENT ON COLUMN indicadores.carga_ageb.lon IS 'Longitud del punto de referencia.';
COMMENT ON COLUMN indicadores.carga_ageb.centroide_es_aproximado IS
    'TRUE mientras lat/lon vengan de la mediana de los establecimientos del DENUE en '
    'el AGEB, que es el método exploratorio. Pasa a FALSE cuando el punto venga de '
    'curada.ageb_centroide_oficial. Si está en TRUE, el hallazgo B se reporta como '
    'exploratorio.';
COMMENT ON COLUMN indicadores.carga_ageb.nivel_geografico IS
    'Siempre "AGEB": cada fila describe un área geoestadística básica urbana.';
COMMENT ON COLUMN indicadores.carga_ageb.fuente IS
    'Fuentes cruzadas, p. ej. "INEGI, Censo 2020 + DENUE 05/2026".';

CREATE INDEX IF NOT EXISTS ix_carga_ageb_mun          ON indicadores.carga_ageb (cve_mun);
CREATE INDEX IF NOT EXISTS ix_carga_ageb_sin_respaldo ON indicadores.carga_ageb (sin_respaldo) WHERE sin_respaldo;


-- -----------------------------------------------------------------------------
-- 3.4 Establecimientos de cuidado (capa de puntos del mapa)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS indicadores.establecimientos_cuidado (
    id                  TEXT PRIMARY KEY,
    nom_estab           TEXT,
    grupo               TEXT NOT NULL,
    tipo                TEXT NOT NULL,
    sector              TEXT NOT NULL,
    per_ocu             TEXT,
    codigo_act          TEXT NOT NULL,
    cve_mun             TEXT NOT NULL,
    alcaldia            TEXT NOT NULL,
    cvegeo_ageb         TEXT,
    es_respaldo         BOOLEAN NOT NULL,
    lat                 DOUBLE PRECISION NOT NULL,
    lon                 DOUBLE PRECISION NOT NULL,
    nivel_geografico    TEXT NOT NULL
        CHECK (nivel_geografico IN ('AGEB', 'Alcaldía', 'CDMX', 'Nacional')),
    fuente              TEXT NOT NULL
);

COMMENT ON TABLE indicadores.establecimientos_cuidado IS
    'Los 1,463 establecimientos de cuidado de la CDMX como capa de puntos del mapa. '
    'ADVERTENCIA PARA EL TABLERO: contar la tabla completa da 1,463, pero solo 838 '
    '(es_respaldo = TRUE) entran en el cálculo de las zonas sin respaldo. Publicar '
    '"1,463 establecimientos de cuidado" junto al hallazgo B es contradictorio. '
    'El DENUE cuenta establecimientos, nunca lugares disponibles: no decir "cobertura".';

COMMENT ON COLUMN indicadores.establecimientos_cuidado.id IS
    'Clave del establecimiento en el DENUE. Relaciona con curada.denue_cuidado.id.';
COMMENT ON COLUMN indicadores.establecimientos_cuidado.nom_estab IS
    'Nombre comercial; puede ser NULL.';
COMMENT ON COLUMN indicadores.establecimientos_cuidado.grupo IS
    'Agrupación del proyecto: Infancia, Personas mayores, etc. Sirve para la leyenda '
    'y el filtro del mapa.';
COMMENT ON COLUMN indicadores.establecimientos_cuidado.tipo IS
    'Subtipo: Guardería, Residencia / asilo, Centro de día, Comedor comunitario, etc.';
COMMENT ON COLUMN indicadores.establecimientos_cuidado.sector IS 'Público o Privado.';
COMMENT ON COLUMN indicadores.establecimientos_cuidado.per_ocu IS
    'Rango de personal ocupado, en texto. No es capacidad de atención.';
COMMENT ON COLUMN indicadores.establecimientos_cuidado.codigo_act IS
    'Código SCIAN de 6 dígitos, como texto.';
COMMENT ON COLUMN indicadores.establecimientos_cuidado.cve_mun IS
    'Clave de alcaldía, 3 caracteres.';
COMMENT ON COLUMN indicadores.establecimientos_cuidado.alcaldia IS 'Nombre de la alcaldía.';
COMMENT ON COLUMN indicadores.establecimientos_cuidado.cvegeo_ageb IS
    'AGEB donde cae el establecimiento. NULL cuando la clave del DENUE no empata con '
    'ninguna AGEB urbana del Censo (6 casos).';
COMMENT ON COLUMN indicadores.establecimientos_cuidado.es_respaldo IS
    'TRUE para guarderías, residencias y asilos de personas mayores y centros de día: '
    'los que sustituyen horas de cuidado en el hogar. 838 de 1,463. El mapa debería '
    'distinguirlos visualmente de los demás.';
COMMENT ON COLUMN indicadores.establecimientos_cuidado.lat IS
    'Latitud del establecimiento, WGS84. Esta sí es la ubicación real que publica el '
    'DENUE, no una aproximación.';
COMMENT ON COLUMN indicadores.establecimientos_cuidado.lon IS 'Longitud, WGS84.';
COMMENT ON COLUMN indicadores.establecimientos_cuidado.nivel_geografico IS
    'Siempre "AGEB": es el nivel más fino al que se puede ubicar el punto dentro de '
    'la geografía del proyecto.';
COMMENT ON COLUMN indicadores.establecimientos_cuidado.fuente IS
    'Siempre "INEGI, DENUE 05/2026".';

CREATE INDEX IF NOT EXISTS ix_estab_cuidado_mun      ON indicadores.establecimientos_cuidado (cve_mun);
CREATE INDEX IF NOT EXISTS ix_estab_cuidado_ageb     ON indicadores.establecimientos_cuidado (cvegeo_ageb);
CREATE INDEX IF NOT EXISTS ix_estab_cuidado_respaldo ON indicadores.establecimientos_cuidado (es_respaldo) WHERE es_respaldo;


-- -----------------------------------------------------------------------------
-- 3.5 ENUT 2024 — carga de cuidado por actividad, CDMX contra nacional
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS indicadores.enut_carga_actividad (
    ambito              TEXT NOT NULL,
    sexo                TEXT NOT NULL,
    actividad           TEXT NOT NULL,
    pct_realiza         NUMERIC(5,1),
    horas_semana        NUMERIC(5,1),
    n_muestral          INTEGER,
    precision_baja      BOOLEAN NOT NULL,
    nivel_geografico    TEXT NOT NULL
        CHECK (nivel_geografico IN ('AGEB', 'Alcaldía', 'CDMX', 'Nacional')),
    fuente              TEXT NOT NULL,
    PRIMARY KEY (ambito, sexo, actividad)
);

COMMENT ON TABLE indicadores.enut_carga_actividad IS
    'ENUT 2024: cuánto cuidan las personas, por actividad, comparando CDMX contra el '
    'total nacional y mujeres contra hombres (16 filas). Los hombres aparecen solo '
    'como referencia para dimensionar la brecha, nunca como tema. '
    'Las horas se promedian ENTRE QUIENES REALIZAN la actividad, que es el método con '
    'el que se reproducen las cifras publicadas por el INEGI.';

COMMENT ON COLUMN indicadores.enut_carga_actividad.ambito IS
    'CDMX o Nacional. En la CDMX la muestra es de 2,107 personas de 12+ (1,144 mujeres).';
COMMENT ON COLUMN indicadores.enut_carga_actividad.sexo IS 'Mujeres u Hombres.';
COMMENT ON COLUMN indicadores.enut_carga_actividad.actividad IS
    'Actividad de cuidado. Se usan las variables SIN cuidados pasivos (sufijo _sin_cp). '
    'OJO: las etiquetas de esta tabla no son idénticas a las de '
    'indicadores.enut_brecha_mujeres_cdmx; no unir las dos tablas por este texto.';
COMMENT ON COLUMN indicadores.enut_carga_actividad.pct_realiza IS
    '% de la población de 12+ del ámbito y sexo que realiza la actividad.';
COMMENT ON COLUMN indicadores.enut_carga_actividad.horas_semana IS
    'Horas por semana que dedica a la actividad quien la realiza. No es un promedio '
    'sobre toda la población.';
COMMENT ON COLUMN indicadores.enut_carga_actividad.n_muestral IS
    'Personas de la muestra que sostienen la cifra. Es el dato que permite juzgar si '
    'se puede citar.';
COMMENT ON COLUMN indicadores.enut_carga_actividad.precision_baja IS
    'TRUE cuando n_muestral < 100. Esas cifras se publican con advertencia o no se '
    'publican. El cálculo formal del coeficiente de variación, con est_dis, upm_dis y '
    'fac_per, es tarea aparte: esta bandera es solo un semáforo.';
COMMENT ON COLUMN indicadores.enut_carga_actividad.nivel_geografico IS
    'CDMX o Nacional, igual que ambito. La ENUT es representativa por entidad federativa.';
COMMENT ON COLUMN indicadores.enut_carga_actividad.fuente IS 'Siempre "INEGI, ENUT 2024".';


-- -----------------------------------------------------------------------------
-- 3.6 ENUT 2024 — brecha de cuidado de las mujeres de la CDMX
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS indicadores.enut_brecha_mujeres_cdmx (
    actividad               TEXT PRIMARY KEY,
    pct_realiza_mujeres     NUMERIC(5,1),
    horas_mujeres           NUMERIC(5,1),
    n_mujeres               INTEGER,
    horas_hombres_ref       NUMERIC(5,1),
    razon_mujeres_hombres   NUMERIC(4,2),
    nivel_geografico        TEXT NOT NULL
        CHECK (nivel_geografico IN ('AGEB', 'Alcaldía', 'CDMX', 'Nacional')),
    fuente                  TEXT NOT NULL
);

COMMENT ON TABLE indicadores.enut_brecha_mujeres_cdmx IS
    'ENUT 2024, CDMX: las seis actividades de cuidado y trabajo doméstico de las '
    'mujeres, con las horas de los hombres como referencia y la razón entre ambas. '
    'Cubre dos actividades que no están en indicadores.enut_carga_actividad '
    '(cuidado de 6 a 14 años y trabajo doméstico no remunerado).';

COMMENT ON COLUMN indicadores.enut_brecha_mujeres_cdmx.actividad IS
    'Actividad de cuidado o trabajo doméstico, en variables sin cuidados pasivos.';
COMMENT ON COLUMN indicadores.enut_brecha_mujeres_cdmx.pct_realiza_mujeres IS
    '% de las mujeres de 12+ de la CDMX que realiza la actividad. El 62.2 del cuidado '
    'total es una de las cifras de control del proyecto.';
COMMENT ON COLUMN indicadores.enut_brecha_mujeres_cdmx.horas_mujeres IS
    'Horas por semana entre las mujeres que realizan la actividad.';
COMMENT ON COLUMN indicadores.enut_brecha_mujeres_cdmx.n_mujeres IS
    'Mujeres de la muestra que realizan la actividad. Debajo de 100 la cifra es frágil.';
COMMENT ON COLUMN indicadores.enut_brecha_mujeres_cdmx.horas_hombres_ref IS
    'Horas por semana de los hombres que realizan la actividad. Es referencia para '
    'medir la brecha, no un tema del Observatorio.';
COMMENT ON COLUMN indicadores.enut_brecha_mujeres_cdmx.razon_mujeres_hombres IS
    'horas_mujeres / horas_hombres_ref. Único campo con DOS decimales en vez de uno: '
    'la razón vale entre 0.98 y 2.12, y redondearla a un decimal borraría la '
    'diferencia entre 1.51 y 1.53.';
COMMENT ON COLUMN indicadores.enut_brecha_mujeres_cdmx.nivel_geografico IS 'Siempre "CDMX".';
COMMENT ON COLUMN indicadores.enut_brecha_mujeres_cdmx.fuente IS 'Siempre "INEGI, ENUT 2024".';


-- -----------------------------------------------------------------------------
-- 3.7 ENUT 2024 — doble jornada
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS indicadores.enut_doble_jornada (
    grupo                       TEXT PRIMARY KEY,
    horas_trabajo_mercado       NUMERIC(5,1) NOT NULL,
    horas_trabajo_domestico     NUMERIC(5,1) NOT NULL,
    horas_cuidado               NUMERIC(5,1) NOT NULL,
    horas_jornada_total         NUMERIC(5,1) NOT NULL,
    n_muestral                  INTEGER NOT NULL,
    nivel_geografico            TEXT NOT NULL
        CHECK (nivel_geografico IN ('AGEB', 'Alcaldía', 'CDMX', 'Nacional')),
    fuente                      TEXT NOT NULL
);

COMMENT ON TABLE indicadores.enut_doble_jornada IS
    'Hallazgo A. Jornada semanal de las personas OCUPADAS de la CDMX, descompuesta en '
    'trabajo pagado, doméstico y de cuidado (2 filas: mujeres y hombres de referencia). '
    'A diferencia de las otras tablas de ENUT, aquí el promedio es sobre TODA la '
    'población ocupada del grupo, incluyendo a quien no realiza la actividad: por eso '
    'los componentes suman la jornada total. '
    'Nota del equipo: la brecha en jornada total (+3.5 h) es estadísticamente '
    'significativa pero frágil; la de trabajo no pagado (+12.7 h) es sólida. Se '
    'recomienda encabezar el hallazgo con el trabajo no pagado y usar las 77 h como '
    'dato de apoyo.';

COMMENT ON COLUMN indicadores.enut_doble_jornada.grupo IS
    '"Mujeres ocupadas" u "Hombres ocupados (ref.)". Solo personas con condición de '
    'actividad = ocupada.';
COMMENT ON COLUMN indicadores.enut_doble_jornada.horas_trabajo_mercado IS
    'Horas semanales de trabajo para el mercado (trabajo pagado).';
COMMENT ON COLUMN indicadores.enut_doble_jornada.horas_trabajo_domestico IS
    'Horas semanales de trabajo doméstico no remunerado del propio hogar.';
COMMENT ON COLUMN indicadores.enut_doble_jornada.horas_cuidado IS
    'Horas semanales de cuidado no remunerado a integrantes del hogar.';
COMMENT ON COLUMN indicadores.enut_doble_jornada.horas_jornada_total IS
    'Suma de los tres componentes. Mujeres ocupadas: 77.0 h; hombres ocupados: 73.5 h. '
    'Es una de las cifras de control del proyecto.';
COMMENT ON COLUMN indicadores.enut_doble_jornada.n_muestral IS
    'Personas ocupadas de la muestra de la CDMX en el grupo (639 mujeres, 689 hombres).';
COMMENT ON COLUMN indicadores.enut_doble_jornada.nivel_geografico IS 'Siempre "CDMX".';
COMMENT ON COLUMN indicadores.enut_doble_jornada.fuente IS 'Siempre "INEGI, ENUT 2024".';


-- -----------------------------------------------------------------------------
-- 3.8 ENUT 2024 — qué mujeres cuidan más
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS indicadores.enut_cuidado_por_grupo (
    tipo_grupo          TEXT NOT NULL,
    grupo               TEXT NOT NULL,
    horas_cuidado       NUMERIC(5,1),
    pct_que_cuida       NUMERIC(5,1),
    n_muestral          INTEGER NOT NULL,
    confiable           BOOLEAN NOT NULL,
    nivel_geografico    TEXT NOT NULL
        CHECK (nivel_geografico IN ('AGEB', 'Alcaldía', 'CDMX', 'Nacional')),
    fuente              TEXT NOT NULL,
    PRIMARY KEY (tipo_grupo, grupo)
);

COMMENT ON TABLE indicadores.enut_cuidado_por_grupo IS
    'ENUT 2024, CDMX: qué mujeres cuidan más, desagregado por condición de actividad '
    '(6 filas) y por grupo de edad (5 filas). Las dos desagregaciones viven en la '
    'misma tabla porque tienen las mismas columnas; se separan con tipo_grupo. '
    'El pico está en las mujeres de 30 a 44 años (14.3 h) y en las dedicadas al hogar '
    'o al cuidado (9.7 h).';

COMMENT ON COLUMN indicadores.enut_cuidado_por_grupo.tipo_grupo IS
    'Qué desagregación es la fila: "Condición de actividad" o "Grupo de edad". '
    'El tablero debe filtrar por esta columna antes de graficar; mezclar las dos da '
    'un total sin sentido, porque son la misma población partida de dos maneras.';
COMMENT ON COLUMN indicadores.enut_cuidado_por_grupo.grupo IS
    'Categoría dentro de la desagregación: "Ocupada", "Dedicada al hogar o al cuidado", '
    '"30–44", "60+", etc.';
COMMENT ON COLUMN indicadores.enut_cuidado_por_grupo.horas_cuidado IS
    'Horas semanales de cuidado promedio POR MUJER del grupo, incluyendo a las que no '
    'cuidan. Por eso es menor que las horas de indicadores.enut_brecha_mujeres_cdmx, '
    'que promedia solo entre quienes cuidan.';
COMMENT ON COLUMN indicadores.enut_cuidado_por_grupo.pct_que_cuida IS
    '% de las mujeres del grupo que realiza trabajo de cuidado no remunerado.';
COMMENT ON COLUMN indicadores.enut_cuidado_por_grupo.n_muestral IS
    'Mujeres de la muestra en el grupo.';
COMMENT ON COLUMN indicadores.enut_cuidado_por_grupo.confiable IS
    'FALSE cuando n_muestral < 60. Es el caso de "Desocupada" (4 casos) y "Otra '
    'situación" (20). Esas filas no se citan como cifra, solo como indicio.';
COMMENT ON COLUMN indicadores.enut_cuidado_por_grupo.nivel_geografico IS 'Siempre "CDMX".';
COMMENT ON COLUMN indicadores.enut_cuidado_por_grupo.fuente IS 'Siempre "INEGI, ENUT 2024".';


-- -----------------------------------------------------------------------------
-- 3.9 ENASIC 2022 — las cuidadoras y los servicios de cuidado
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS indicadores.enasic_cuidadoras (
    tema                    TEXT NOT NULL,
    categoria               TEXT NOT NULL,
    pct                     NUMERIC(5,1) NOT NULL,
    base                    TEXT NOT NULL,
    respuesta_multiple      BOOLEAN NOT NULL,
    variable_enasic         TEXT,
    nivel_geografico        TEXT NOT NULL
        CHECK (nivel_geografico IN ('AGEB', 'Alcaldía', 'CDMX', 'Nacional')),
    fuente                  TEXT NOT NULL,
    PRIMARY KEY (tema, categoria)
);

COMMENT ON TABLE indicadores.enasic_cuidadoras IS
    'Hallazgo C. Relación de las mujeres cuidadoras con los servicios formales de '
    'cuidado, según la ENASIC 2022 (19 filas en cuatro temas). Es el insumo del '
    'programa de vinculación. '
    'LIMITACIÓN MÁS IMPORTANTE: los microdatos públicos de la ENASIC no traen NINGUNA '
    'variable geográfica, ni entidad ni municipio ni tamaño de localidad. Todas estas '
    'cifras son NACIONALES y no se pueden presentar como cifras de la CDMX ni poner en '
    'un mapa. Además es edición única: no hay serie de tiempo. '
    'Base de cálculo: mujeres cuidadoras de 15+, ponderadas con FAC_CUI (4,173 '
    'registros, 23.8 millones de mujeres).';

COMMENT ON COLUMN indicadores.enasic_cuidadoras.tema IS
    'Pregunta que agrupa la fila: "Búsqueda de servicios", "Razones para no buscar", '
    '"Preferencia de cuidado" o "Disposición a cuidar". El tablero filtra por aquí.';
COMMENT ON COLUMN indicadores.enasic_cuidadoras.categoria IS
    'Respuesta concreta dentro del tema, p. ej. "En su casa", "No contrataría", '
    '"Son caros".';
COMMENT ON COLUMN indicadores.enasic_cuidadoras.pct IS
    '% de la base que da esa respuesta. Cifras de referencia: 3.2% buscó un servicio, '
    '61.2% preferiría el cuidado en casa, 32.2% no contrataría nada (este último es un '
    'riesgo de adopción del programa y hay que decirlo), 44.4% trabajaría como '
    'cuidadora pagada.';
COMMENT ON COLUMN indicadores.enasic_cuidadoras.base IS
    'Denominador exacto del porcentaje. No es el mismo en todos los temas: las razones '
    'para no buscar se calculan solo sobre las mujeres que NO buscaron. Sin esta '
    'columna los porcentajes no son comparables entre temas.';
COMMENT ON COLUMN indicadores.enasic_cuidadoras.respuesta_multiple IS
    'TRUE cuando la pregunta admite varias respuestas y los porcentajes del tema NO '
    'suman 100. Es el caso de las razones para no buscar servicios.';
COMMENT ON COLUMN indicadores.enasic_cuidadoras.variable_enasic IS
    'Nombre de la variable en la tabla tpob_cui (P6_42, P6_45_01, P6_46, P6_47, '
    'P6_48...), para poder rastrear la cifra hasta el microdato.';
COMMENT ON COLUMN indicadores.enasic_cuidadoras.nivel_geografico IS
    'Siempre "Nacional". No existe forma de desagregarlo con los datos públicos.';
COMMENT ON COLUMN indicadores.enasic_cuidadoras.fuente IS 'Siempre "INEGI, ENASIC 2022".';
