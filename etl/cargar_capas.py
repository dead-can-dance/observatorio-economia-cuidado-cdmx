"""Carga las tres capas del Observatorio de la Economía del Cuidado en PostgreSQL.

Trabajo de PySpark en modo local (`local[*]`): un solo proceso, sin clúster. El
volumen es de ~8,000 filas en total, así que Spark aquí no se usa por necesidad
de escala sino porque es la herramienta que pide la materia y porque el mismo
código escalaría sin cambios si mañana cargáramos los 32 estados del DENUE.

Las tres capas:

  cruda       Copia 1:1 de cada CSV de data/curada/. Todas las columnas string.
              Spark CREA estas tablas (modo overwrite). Sirve para auditar:
              cualquier cifra del tablero se puede rastrear hasta aquí.

  curada      Entidades con tipos correctos y llave primaria. Las tablas YA
              existen, las creó sql/01_esquemas.sql; aquí se truncan y se
              rellenan (modo append).

  indicadores Tablas listas para el tablero, ya agregadas y cruzadas. Mismo
              mecanismo: truncar y append sobre el DDL existente.

Uso:

    export POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=cuidados \\
           POSTGRES_USER=observatorio POSTGRES_PASSWORD=...
    python etl/cargar_capas.py

Termina con código 0 si el reporte de control cuadra, y con 1 si no.
"""

from pathlib import Path
import os
import sys
import unicodedata
import re

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType, BooleanType, DoubleType, DecimalType


# =============================================================================
# 1. CONFIGURACIÓN
# =============================================================================

# Raíz del repo: este script vive en etl/, así que subimos un nivel.
BASE = Path(__file__).resolve().parent.parent
CUR = BASE / 'data' / 'curada'

# Versión del driver JDBC de PostgreSQL. Spark lo baja de Maven la primera vez
# y lo deja en caché (~/.ivy2). En el contenedor conviene hornearlo en la imagen
# para no depender de la red al arrancar.
PAQUETE_JDBC = 'org.postgresql:postgresql:42.7.4'


def conexion():
    """Arma la URL y las propiedades de JDBC desde variables de entorno.

    No hay valores por defecto para la contraseña a propósito: si falta, el
    trabajo debe fallar aquí y no a medio camino con media base cargada.
    """
    faltantes = [v for v in ('POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD')
                 if not os.environ.get(v)]
    if faltantes:
        sys.exit(f'ERROR: faltan variables de entorno: {", ".join(faltantes)}. '
                 f'Copia .env.example a .env y expórtalas.')

    host = os.environ.get('POSTGRES_HOST', 'localhost')
    puerto = os.environ.get('POSTGRES_PORT', '5432')
    url = f'jdbc:postgresql://{host}:{puerto}/{os.environ["POSTGRES_DB"]}'
    props = {
        'user': os.environ['POSTGRES_USER'],
        'password': os.environ['POSTGRES_PASSWORD'],
        'driver': 'org.postgresql.Driver',
    }
    return url, props


URL, PROPS = conexion()


# =============================================================================
# 2. UTILIDADES
# =============================================================================

def normalizar_columna(nombre):
    """Convierte un encabezado de CSV en un nombre de columna válido para SQL.

    Los CSV traen encabezados que PostgreSQL no acepta sin comillas: 'ámbito',
    '% que lo realiza', 'h/semana (quienes lo realizan)', 'mujeres / hombres (h)',
    'rango carga (1 = más alta)'. Esta función quita acentos, cambia '%' por
    'pct' y reemplaza todo lo que no sea letra o dígito por guion bajo.

    Solo se usa en la capa `cruda`, donde el objetivo es volcar el archivo tal
    cual. En `curada` e `indicadores` las columnas se nombran una por una, a
    mano, para que el diccionario de datos sea auditable y no dependa de una
    regla automática.
    """
    s = unicodedata.normalize('NFKD', nombre)
    s = ''.join(c for c in s if not unicodedata.combining(c))   # quita acentos
    s = s.lower().replace('%', 'pct')
    s = re.sub(r'[^a-z0-9]+', '_', s)
    s = re.sub(r'_+', '_', s).strip('_')
    return f'c_{s}' if s and s[0].isdigit() else s


def leer_csv(spark, archivo):
    """Lee un CSV de data/curada/ con TODAS las columnas como string.

    inferSchema=false no es un detalle: si Spark infiere tipos, la entidad '09'
    se vuelve el entero 9 y pierde el cero a la izquierda, y las 222 AGEB
    alfanuméricas ('003A') se vuelven null. Todas las claves geográficas del
    proyecto se leen y se guardan como texto.
    """
    return (spark.read
            .option('header', True)
            .option('inferSchema', False)      # TODO string, a propósito
            .option('encoding', 'UTF-8')
            .option('quote', '"')              # el DENUE trae comas dentro del nombre
            .option('escape', '"')
            .csv(str(CUR / archivo)))


def limpiar(df):
    """Recorta espacios y convierte las cadenas vacías en null.

    pandas escribe los faltantes como campo vacío. Si entraran como cadena
    vacía, un `WHERE columna IS NULL` del tablero no los encontraría.
    """
    return df.select([
        F.when(F.trim(F.col(c)) == '', None).otherwise(F.trim(F.col(c))).alias(c)
        for c in df.columns
    ])


# Columnas de trazabilidad que se agregan en `cruda`. No viajan a las capas
# siguientes: si lo hicieran, al unir dos tablas Spark quedaría con dos columnas
# con el mismo nombre y cualquier F.col('_cargado_en') sería ambiguo.
METADATOS = ['_archivo_origen', '_cargado_en']


def tabla_cruda(dfs, nombre):
    """Toma una tabla de la capa cruda, ya limpia y sin columnas de metadatos."""
    return limpiar(dfs[nombre]).drop(*METADATOS)


# Todas las conversiones usan try_cast, no cast. Desde Spark 4 el modo ANSI está
# activo por omisión y un cast que falla LANZA un error en vez de devolver null:
# un solo valor raro tiraría el trabajo entero. try_cast devuelve null, que es la
# semántica que queremos (lo que no es número es un faltante, no una catástrofe)
# y además no depende de cómo esté configurado el ANSI en cada entorno.

def entero(col):
    """Texto -> INTEGER. Tolera los conteos que pandas escribió como '1026.0'."""
    return F.col(col).try_cast(DoubleType()).try_cast(IntegerType())


def tasa(col, enteros=5, decimales=1):
    """Texto -> NUMERIC(enteros, decimales). Porcentajes y tasas, un decimal."""
    return F.col(col).try_cast(DoubleType()).try_cast(DecimalType(enteros, decimales))


def booleano(col):
    """Texto -> BOOLEAN. pandas escribe 'True'/'False' con mayúscula inicial."""
    return F.col(col).try_cast(BooleanType())


def doble(col):
    """Texto -> DOUBLE PRECISION. Para latitudes y longitudes."""
    return F.col(col).try_cast(DoubleType())


def truncar(spark, tabla):
    """Vacía una tabla ya existente, conservando su DDL, índices y comentarios.

    Se hace con una conexión JDBC directa en vez de usar mode('overwrite'),
    porque overwrite haría DROP + CREATE y Spark volvería a inventar los tipos:
    perderíamos los TEXT de las claves geográficas, las llaves primarias y los
    COMMENT del archivo SQL.

    Detalle de implementación que cuesta descubrir: no se puede usar
    java.sql.DriverManager. El jar que baja spark.jars.packages queda en el
    classloader de Spark, no en el del sistema, y DriverManager se niega a usar
    un driver cargado por un classloader distinto al de quien lo llama. La
    solución es instanciar el driver nosotros y pedirle la conexión.
    """
    jvm = spark.sparkContext._jvm
    cargador = jvm.java.lang.Thread.currentThread().getContextClassLoader()
    clase = jvm.java.lang.Class.forName(PROPS['driver'], True, cargador)
    driver = clase.newInstance()

    credenciales = jvm.java.util.Properties()
    credenciales.setProperty('user', PROPS['user'])
    credenciales.setProperty('password', PROPS['password'])

    cn = driver.connect(URL, credenciales)
    try:
        cn.createStatement().execute(f'TRUNCATE TABLE {tabla}')
    finally:
        cn.close()


def escribir_cruda(df, tabla):
    """Escribe en el esquema `cruda` con overwrite: aquí Spark SÍ crea la tabla.

    Como todas las columnas vienen como string, el dialecto de PostgreSQL de
    Spark las crea TEXT, que es justo lo que queremos en esta capa. Por eso no
    hace falta declarar los tipos a mano.
    """
    (df.write
       .mode('overwrite')
       .jdbc(URL, f'cruda.{tabla}', properties=PROPS))
    print(f'  cruda.{tabla:<42} {df.count():>5} filas')


def escribir(spark, df, tabla):
    """Trunca y escribe en append sobre una tabla creada por sql/01_esquemas.sql."""
    truncar(spark, tabla)
    df.write.mode('append').jdbc(URL, tabla, properties=PROPS)
    print(f'  {tabla:<48} {df.count():>5} filas')


# =============================================================================
# 3. CAPA CRUDA — copia 1:1 de los CSV
# =============================================================================

# Un CSV por tabla, mismo nombre. El orden no importa: ninguna depende de otra.
ARCHIVOS_CRUDA = [
    'ageb_acceso_cuidado_cdmx',
    'censo2020_ageb_cuidado_cdmx',
    'censo2020_alcaldia_cuidado_cdmx',
    'cruce_oferta_demanda_alcaldia',
    'denue_cuidado_cdmx',
    'enasic_busqueda_servicios',
    'enasic_disposicion_cuidar',
    'enasic_preferencia_cuidado',
    'enasic_razones_no_buscar',
    'enut2024_cuidados_cdmx_vs_nacional',
    'mujeres_carga_acceso_ageb',
    'mujeres_carga_alcaldia',
    'mujeres_cuidado_por_condicion',
    'mujeres_cuidado_por_edad',
    'mujeres_doble_jornada_cdmx',
    'mujeres_enut_carga_cdmx',
    'mujeres_zonas_sin_respaldo_alcaldia',
    'resumen_cifras_clave',
]


def cargar_cruda(spark):
    """Vuelca los 18 CSV al esquema `cruda`, sin tocar un solo valor.

    Devuelve un diccionario con los DataFrames ya leídos, para que las capas
    siguientes construyan sobre ellos y no vuelvan a leer disco.
    """
    print('\n--- CAPA CRUDA (copia 1:1, todo TEXT) ---')
    dfs = {}
    for nombre in ARCHIVOS_CRUDA:
        df = leer_csv(spark, f'{nombre}.csv')
        # Los nombres originales se conservan en el CSV, que está versionado en
        # git: aquí solo se normalizan para que PostgreSQL los acepte.
        df = df.toDF(*[normalizar_columna(c) for c in df.columns])
        df = df.withColumn('_archivo_origen', F.lit(f'data/curada/{nombre}.csv')) \
               .withColumn('_cargado_en', F.current_timestamp().cast('string'))
        df.cache()
        escribir_cruda(df, nombre)
        dfs[nombre] = df
    return dfs


# =============================================================================
# 4. CAPA CURADA — tipos correctos y limpieza
# =============================================================================

# Los seis códigos SCIAN que cuentan como respaldo de cuidado para el hallazgo B.
# El resto (comedores comunitarios, orfanatos, residencias de enfermería) está en
# el DENUE pero NO sustituye horas de cuidado en el hogar.
CODIGOS_RESPALDO = ['624411', '624412',    # guarderías
                    '623311', '623312',    # residencias y asilos de personas mayores
                    '624121', '624122']    # centros de día


def cargar_curada(spark, dfs):
    """Convierte tipos, limpia y llena las cuatro tablas de `curada` que tienen datos.

    curada.ageb_centroide_oficial NO se toca: la llena Karen con el Marco
    Geoestadístico y truncarla aquí borraría su trabajo en cada corrida.
    """
    print('\n--- CAPA CURADA (tipos y limpieza) ---')

    # -- 4.1 Censo por AGEB: las 2,433 AGEB urbanas, el universo canónico --------
    censo = tabla_cruda(dfs, 'censo2020_ageb_cuidado_cdmx')
    # Las AGEB con centroide son las que llegaron a la tabla de mujeres (2,320).
    con_centroide = tabla_cruda(dfs, 'mujeres_carga_acceso_ageb').select(
        F.col('cvegeo_ageb').alias('_cvegeo_centroide')).distinct()

    censo_ageb = (censo
        .join(con_centroide, censo.cvegeo_ageb == F.col('_cvegeo_centroide'), 'left')
        .select(
            F.col('cvegeo_ageb'),
            F.col('entidad').alias('cve_ent'),
            F.col('mun').alias('cve_mun'),
            F.col('nom_mun'),
            F.col('loc').alias('cve_loc'),
            F.col('ageb'),
            # Los conteos del Censo con '*' (reserva por confidencialidad) ya
            # vienen vacíos en el CSV; limpiar() los dejó en null y el cast los
            # mantiene en null. Nunca se convierten a 0.
            entero('pob_total').alias('pob_total'),
            entero('pob_0a2').alias('pob_0a2'),
            entero('pob_3a5').alias('pob_3a5'),
            entero('pob_0a5').alias('pob_0a5'),
            entero('pob_60mas').alias('pob_60mas'),
            entero('pob_65mas').alias('pob_65mas'),
            entero('pob_discapacidad').alias('pob_discapacidad'),
            entero('pob_disc_autocuidado').alias('pob_disc_autocuidado'),
            entero('pob_3a5_no_escuela').alias('pob_3a5_no_escuela'),
            entero('pob_sin_serv_salud').alias('pob_sin_serv_salud'),
            entero('hogares').alias('hogares'),
            entero('hogares_jefa').alias('hogares_jefa'),
            F.col('_cvegeo_centroide').isNotNull().alias('tiene_centroide'),
        ))
    escribir(spark, censo_ageb, 'curada.censo_ageb')

    # -- 4.2 Censo por AGEB, bloque de mujeres: las 2,320 con centroide ----------
    muj = tabla_cruda(dfs, 'mujeres_carga_acceso_ageb')
    censo_mujeres = muj.select(
        F.col('cvegeo_ageb'),
        F.col('mun').alias('cve_mun'),
        F.col('nom_mun'),
        entero('pobtot').alias('pob_total'),
        entero('pobfem').alias('pob_femenina'),
        entero('p_0a2').alias('p_0a2'),
        entero('p_3a5').alias('p_3a5'),
        entero('pob_0a5').alias('pob_0a5'),
        entero('p_15ymas_f').alias('p_15ymas_f'),
        entero('p_60ymas_f').alias('p_60ymas_f'),
        entero('p_12ymas_f').alias('p_12ymas_f'),
        entero('pcdisc_mot2').alias('pcdisc_mot2'),
        entero('pe_inac_f').alias('pe_inac_f'),
        entero('pea_f').alias('pea_f'),
        entero('tothog').alias('tothog'),
        entero('hogjef_f').alias('hogjef_f'),
        entero('mujeres_15a59').alias('mujeres_15a59'),
        # El CSV guarda la carga sin redondear (16.276803...); la base la
        # almacena con un decimal, que es como se reporta.
        tasa('carga_directa_x100_mujeres').alias('carga_directa_x100_mujeres'),
        tasa('pct_hog_jefa').alias('pct_hog_jefa'),
        tasa('pct_mujeres_inactivas').alias('pct_mujeres_inactivas'),
        # lat/lon se llaman _aprox porque NO son el centroide del polígono: son
        # la mediana de los establecimientos del DENUE dentro del AGEB.
        doble('lat').alias('lat_aprox'),
        doble('lon').alias('lon_aprox'),
    )
    escribir(spark, censo_mujeres, 'curada.censo_ageb_mujeres')

    # -- 4.3 Censo por alcaldía: los 16 totales, que sí incluyen zona rural ------
    alc = tabla_cruda(dfs, 'censo2020_alcaldia_cuidado_cdmx')
    censo_alcaldia = alc.select(
        F.col('cve_mun'),
        F.col('entidad').alias('cve_ent'),
        F.col('alcaldia'),
        entero('pob_total').alias('pob_total'),
        entero('pob_0a2').alias('pob_0a2'),
        entero('pob_3a5').alias('pob_3a5'),
        entero('pob_0a5').alias('pob_0a5'),
        entero('pob_60mas').alias('pob_60mas'),
        entero('pob_65mas').alias('pob_65mas'),
        entero('pob_discapacidad').alias('pob_discapacidad'),
        entero('pob_disc_autocuidado').alias('pob_disc_autocuidado'),
        entero('pob_3a5_no_escuela').alias('pob_3a5_no_escuela'),
        entero('pob_sin_serv_salud').alias('pob_sin_serv_salud'),
        entero('hogares').alias('hogares'),
        entero('hogares_jefa').alias('hogares_jefa'),
    )
    escribir(spark, censo_alcaldia, 'curada.censo_alcaldia')

    # -- 4.4 Establecimientos del DENUE ------------------------------------------
    den = tabla_cruda(dfs, 'denue_cuidado_cdmx')
    # Un CVEGEO del DENUE es válido si existe entre las AGEB urbanas del Censo.
    # Son 6 claves de 978 las que no empatan (AGEB rurales o mal capturadas).
    agebs_censo = censo.select(F.col('cvegeo_ageb').alias('_cvegeo_censo')).distinct()

    denue_cuidado = (den
        .join(agebs_censo, den.cvegeo_ageb == F.col('_cvegeo_censo'), 'left')
        .select(
            F.col('id'),
            F.col('nom_estab'),
            F.col('codigo_act'),
            F.col('nombre_act'),
            F.col('grupo'),
            F.col('tipo'),
            F.col('sector'),
            F.col('per_ocu'),
            # El CSV no trae cve_ent: se recupera de los 2 primeros caracteres
            # del CVEGEO, que es entidad(2)+municipio(3)+localidad(4)+ageb(4).
            F.substring(F.col('cvegeo_ageb'), 1, 2).alias('cve_ent'),
            F.col('cve_mun'),
            F.col('municipio'),
            F.col('cvegeo_ageb'),
            F.col('_cvegeo_censo').isNotNull().alias('cvegeo_valido'),
            F.col('codigo_act').isin(CODIGOS_RESPALDO).alias('es_respaldo'),
            doble('lat').alias('lat'),
            doble('lon').alias('lon'),
            # El DENUE publica la fecha de alta como AAAA-MM; se guarda con día 01.
            F.to_date(F.concat(F.col('fecha_alta'), F.lit('-01')), 'yyyy-MM-dd').alias('fecha_alta'),
        ))
    escribir(spark, denue_cuidado, 'curada.denue_cuidado')

    return {'censo_ageb': censo_ageb, 'censo_mujeres': censo_mujeres,
            'censo_alcaldia': censo_alcaldia, 'denue': denue_cuidado}


# =============================================================================
# 5. CAPA INDICADORES — lo que consume el tablero
# =============================================================================

def cargar_indicadores(spark, dfs, cur):
    """Construye las nueve tablas del esquema `indicadores`.

    Todas llevan nivel_geografico y fuente. No son adorno: impiden que alguien
    ponga en un mapa de la CDMX una cifra de la ENASIC, que es nacional.
    """
    print('\n--- CAPA INDICADORES (listo para el tablero) ---')

    FTE_ENUT = 'INEGI, ENUT 2024'
    FTE_ENASIC = 'INEGI, ENASIC 2022'
    FTE_CRUCE = 'INEGI, Censo 2020 + DENUE 05/2026'

    # -- 5.1 KPIs de cabecera -----------------------------------------------------
    kpi = tabla_cruda(dfs, 'resumen_cifras_clave')
    # 'valor' mezcla números y texto: 'Milpa Alta' es un KPI cualitativo. Se parte
    # en dos columnas para que el tablero no tenga que adivinar.
    valor_num = F.col('valor').try_cast(DoubleType())
    etiqueta = F.trim(F.split(F.col('clave'), '·').getItem(1))
    kpi_cdmx = kpi.select(
        F.col('clave'),
        etiqueta.alias('etiqueta'),
        valor_num.try_cast(DecimalType(12, 1)).alias('valor_num'),
        F.when(valor_num.isNull(), F.col('valor')).alias('valor_texto'),
        # La unidad es lo que permite al tablero distinguir un 62.2 de un 77.0.
        # El orden de las reglas importa: 'mujeres 15–59 en esas AGEB' contiene
        # tanto 'mujeres 15' como 'AGEB', y la unidad correcta es mujeres.
        F.when(valor_num.isNull(), F.lit('texto'))
         .when(F.col('clave').contains('%'), F.lit('%'))
         .when(F.col('clave').contains('h/semana') | F.col('clave').contains('jornada'),
               F.lit('horas por semana'))
         .when(F.col('clave').contains('mujeres 15'), F.lit('mujeres'))
         .when(F.col('clave').contains('AGEB'), F.lit('AGEB'))
         .when(F.col('clave').contains('carga directa'),
               F.lit('personas por cada 100 mujeres'))
         .otherwise(F.lit('valor')).alias('unidad'),
        F.col('nivel_geografico'),
        F.col('fuente'),
    )
    escribir(spark, kpi_cdmx, 'indicadores.kpi_cdmx')

    # -- 5.2 Resumen por alcaldía: el cruce de cuatro tablas ----------------------
    # Las tablas por alcaldía solo traen el NOMBRE, no la clave. Se unen por
    # nombre (los 16 empatan exactamente, acentos incluidos) y se recupera
    # cve_mun desde el Censo, que sí la trae. Por eso la base debe estar en UTF-8.
    carga_alc = tabla_cruda(dfs, 'mujeres_carga_alcaldia').withColumnRenamed('nom_mun', 'alcaldia')
    zonas_alc = tabla_cruda(dfs, 'mujeres_zonas_sin_respaldo_alcaldia').withColumnRenamed('nom_mun', 'alcaldia')
    cruce_alc = tabla_cruda(dfs, 'cruce_oferta_demanda_alcaldia')

    resumen_alcaldia = (cur['censo_alcaldia'].select('cve_mun', 'alcaldia', 'pob_total')
        .join(carga_alc, 'alcaldia')
        .join(zonas_alc, 'alcaldia')
        .join(cruce_alc.drop('pob_total'), 'alcaldia')
        .select(
            F.col('cve_mun'),
            F.col('alcaldia'),
            F.col('pob_total'),
            entero('mujeres_15a59').alias('mujeres_15a59'),
            tasa('pct_60mas').alias('pct_60mas'),
            tasa('carga_directa_x100_mujeres').alias('carga_directa_x100_mujeres'),
            entero('rango_carga_1_mas_alta').alias('rango_carga'),
            tasa('pct_hog_jefa').alias('pct_hog_jefa'),
            tasa('pct_mujeres_inactivas').alias('pct_mujeres_inactivas'),
            entero('agebs').alias('agebs'),
            entero('alta_carga').alias('agebs_alta_carga'),
            entero('sin_respaldo').alias('agebs_sin_respaldo'),
            entero('mujeres_sin_respaldo').alias('mujeres_sin_respaldo'),
            # Benito Juárez no tiene ninguna AGEB de alta carga: el porcentaje
            # queda en null (no aplica), nunca en 0.
            tasa('pct_ageb_de_alta_carga_sin_respaldo').alias('pct_agebs_alta_carga_sin_respaldo'),
            entero('guarderias').alias('guarderias'),
            entero('cuidado_mayores').alias('cuidado_mayores'),
            # Razones de presión sobre la oferta: llegan hasta 13,401, así que
            # necesitan más dígitos que un porcentaje.
            tasa('ninos_0a5_por_guarderia', enteros=10).alias('ninos_0a5_por_guarderia'),
            tasa('mayores_60_por_establecimiento', enteros=10).alias('mayores_60_por_establecimiento'),
            tasa('pct_guarderias_publicas').alias('pct_guarderias_publicas'),
            F.lit('Alcaldía').alias('nivel_geografico'),
            F.lit(FTE_CRUCE).alias('fuente'),
        ))
    escribir(spark, resumen_alcaldia, 'indicadores.resumen_alcaldia')

    # -- 5.3 Carga y acceso por AGEB: la capa del mapa ----------------------------
    muj = tabla_cruda(dfs, 'mujeres_carga_acceso_ageb')
    carga_ageb = muj.select(
        F.col('cvegeo_ageb'),
        F.col('mun').alias('cve_mun'),
        F.col('nom_mun').alias('alcaldia'),
        entero('mujeres_15a59').alias('mujeres_15a59'),
        entero('pob_0a5').alias('pob_0a5'),
        entero('pcdisc_mot2').alias('pob_disc_autocuidado'),
        tasa('carga_directa_x100_mujeres').alias('carga_directa_x100_mujeres'),
        tasa('pct_hog_jefa').alias('pct_hog_jefa'),
        tasa('pct_mujeres_inactivas').alias('pct_mujeres_inactivas'),
        entero('guarderias_1km').alias('guarderias_1km'),
        entero('respaldo_total_1km').alias('respaldo_total_1km'),
        booleano('alta_carga').alias('alta_carga'),
        booleano('sin_guarderia').alias('sin_guarderia'),
        booleano('sin_respaldo').alias('sin_respaldo'),
        doble('lat').alias('lat'),
        doble('lon').alias('lon'),
        # Se queda en TRUE mientras el punto venga de la mediana del DENUE.
        # Pasa a FALSE cuando se cargue curada.ageb_centroide_oficial.
        F.lit(True).alias('centroide_es_aproximado'),
        F.lit('AGEB').alias('nivel_geografico'),
        F.lit(FTE_CRUCE).alias('fuente'),
    )
    escribir(spark, carga_ageb, 'indicadores.carga_ageb')

    # -- 5.4 Establecimientos: la capa de puntos del mapa -------------------------
    establecimientos = cur['denue'].select(
        F.col('id'),
        F.col('nom_estab'),
        F.col('grupo'),
        F.col('tipo'),
        F.col('sector'),
        F.col('per_ocu'),
        F.col('codigo_act'),
        F.col('cve_mun'),
        F.col('municipio').alias('alcaldia'),
        # Si el CVEGEO no empata con ninguna AGEB del Censo, se deja en null en
        # vez de arrastrar una clave que no existe.
        F.when(F.col('cvegeo_valido'), F.col('cvegeo_ageb')).alias('cvegeo_ageb'),
        F.col('es_respaldo'),
        F.col('lat'),
        F.col('lon'),
        F.lit('AGEB').alias('nivel_geografico'),
        F.lit('INEGI, DENUE 05/2026').alias('fuente'),
    )
    escribir(spark, establecimientos, 'indicadores.establecimientos_cuidado')

    # -- 5.5 ENUT: carga por actividad, CDMX contra nacional ----------------------
    enut_act = tabla_cruda(dfs, 'enut2024_cuidados_cdmx_vs_nacional')
    enut_carga_actividad = enut_act.select(
        F.col('ambito'),
        F.col('sexo'),
        F.col('actividad'),
        tasa('pct_que_lo_realiza').alias('pct_realiza'),
        tasa('h_semana_quienes_lo_realizan').alias('horas_semana'),
        entero('n_muestral').alias('n_muestral'),
        # Semáforo simple. El coeficiente de variación formal, con est_dis,
        # upm_dis y fac_per, es trabajo aparte sobre el microdato.
        (entero('n_muestral') < 100).alias('precision_baja'),
        F.col('ambito').alias('nivel_geografico'),
        F.lit(FTE_ENUT).alias('fuente'),
    )
    escribir(spark, enut_carga_actividad, 'indicadores.enut_carga_actividad')

    # -- 5.6 ENUT: brecha de las mujeres de la CDMX -------------------------------
    enut_muj = tabla_cruda(dfs, 'mujeres_enut_carga_cdmx')
    enut_brecha = enut_muj.select(
        F.col('actividad'),
        tasa('pct_de_mujeres_que_lo_realiza').alias('pct_realiza_mujeres'),
        tasa('h_semana_mujeres_que_lo_realizan').alias('horas_mujeres'),
        entero('n_mujeres').alias('n_mujeres'),
        tasa('ref_h_semana_hombres').alias('horas_hombres_ref'),
        # Dos decimales a propósito: la razón vale entre 0.98 y 2.12 y con un
        # decimal se borraría la diferencia entre 1.51 y 1.53.
        tasa('mujeres_hombres_h', enteros=4, decimales=2).alias('razon_mujeres_hombres'),
        F.lit('CDMX').alias('nivel_geografico'),
        F.lit(FTE_ENUT).alias('fuente'),
    )
    escribir(spark, enut_brecha, 'indicadores.enut_brecha_mujeres_cdmx')

    # -- 5.7 ENUT: doble jornada (hallazgo A) -------------------------------------
    jor = tabla_cruda(dfs, 'mujeres_doble_jornada_cdmx')
    enut_doble_jornada = jor.select(
        F.col('grupo'),
        tasa('trabajo_para_el_mercado').alias('horas_trabajo_mercado'),
        tasa('trabajo_domestico_no_remunerado').alias('horas_trabajo_domestico'),
        tasa('cuidado_no_remunerado').alias('horas_cuidado'),
        tasa('total').alias('horas_jornada_total'),
        entero('n').alias('n_muestral'),
        F.lit('CDMX').alias('nivel_geografico'),
        F.lit(FTE_ENUT).alias('fuente'),
    )
    escribir(spark, enut_doble_jornada, 'indicadores.enut_doble_jornada')

    # -- 5.8 ENUT: qué mujeres cuidan más -----------------------------------------
    # Las dos desagregaciones (condición de actividad y edad) tienen las mismas
    # columnas, así que viven en una sola tabla separadas por tipo_grupo.
    def por_grupo(nombre_df, tipo_grupo, col_grupo):
        d = tabla_cruda(dfs, nombre_df)
        return d.select(
            F.lit(tipo_grupo).alias('tipo_grupo'),
            F.col(col_grupo).alias('grupo'),
            tasa('h_semana_de_cuidado_promedio_por_mujer').alias('horas_cuidado'),
            tasa('pct_que_cuida').alias('pct_que_cuida'),
            entero('n').alias('n_muestral'),
            # El CSV guarda 'sí' / 'no — muestra chica'.
            (F.col('confiable') == 'sí').alias('confiable'),
            F.lit('CDMX').alias('nivel_geografico'),
            F.lit(FTE_ENUT).alias('fuente'),
        )

    enut_por_grupo = por_grupo('mujeres_cuidado_por_condicion',
                               'Condición de actividad', 'condicion').unionByName(
                     por_grupo('mujeres_cuidado_por_edad',
                               'Grupo de edad', 'grupo_edad'))
    escribir(spark, enut_por_grupo, 'indicadores.enut_cuidado_por_grupo')

    # -- 5.9 ENASIC: las cuatro preguntas en una sola tabla larga -----------------
    # Comparten forma (categoría + %), así que se apilan con un campo `tema`.
    # `base` es indispensable: las razones para no buscar se calculan solo sobre
    # las mujeres que NO buscaron, así que su % no es comparable con el resto.
    BLOQUES_ENASIC = [
        ('enasic_busqueda_servicios', 'Búsqueda de servicios', 'respuesta',
         'pct_de_mujeres_cuidadoras', 'Mujeres cuidadoras de 15+', False, 'P6_42'),
        ('enasic_razones_no_buscar', 'Razones para no buscar', 'razon',
         'pct_de_mujeres_cuidadoras_que_no_buscaron',
         'Mujeres cuidadoras que no buscaron servicio', True, 'P6_45_01 a P6_45_10'),
        ('enasic_preferencia_cuidado', 'Preferencia de cuidado', 'preferencia',
         'pct_de_mujeres_cuidadoras', 'Mujeres cuidadoras de 15+', False, 'P6_46'),
        ('enasic_disposicion_cuidar', 'Disposición a cuidar', 'indicador',
         'pct_de_mujeres_cuidadoras', 'Mujeres cuidadoras de 15+', False, 'P6_47 / P6_48'),
    ]

    partes = []
    for archivo, tema, col_cat, col_pct, base, multiple, variable in BLOQUES_ENASIC:
        d = tabla_cruda(dfs, archivo)
        partes.append(d.select(
            F.lit(tema).alias('tema'),
            F.col(col_cat).alias('categoria'),
            tasa(col_pct).alias('pct'),
            F.lit(base).alias('base'),
            F.lit(multiple).alias('respuesta_multiple'),
            F.lit(variable).alias('variable_enasic'),
            # Se toma del propio CSV, que ya trae 'Nacional'. No se escribe a
            # mano: si algún día la ENASIC se pudiera desagregar, el dato manda.
            F.col('nivel_geografico'),
            F.lit(FTE_ENASIC).alias('fuente'),
        ))

    enasic = partes[0]
    for p in partes[1:]:
        enasic = enasic.unionByName(p)
    escribir(spark, enasic, 'indicadores.enasic_cuidadoras')


# =============================================================================
# 6. REPORTE DE CONTROL
# =============================================================================

# Cifras que deben reproducirse en cada corrida. Si una no cuadra, el trabajo
# falla: es el criterio de terminado que acordó el equipo. Borrar la base,
# correr esto y volver a obtener las mismas cifras.
CONTROLES = [
    ('Establecimientos de cuidado del DENUE',
     'SELECT count(*) FROM curada.denue_cuidado', 1463),
    ('AGEB con carga alta y sin respaldo a 1 km',
     'SELECT count(*) FROM indicadores.carga_ageb WHERE sin_respaldo', 88),
    ('Alcaldías en indicadores.resumen_alcaldia',
     'SELECT count(*) FROM indicadores.resumen_alcaldia', 16),
    ('Alcaldías en curada.censo_alcaldia',
     'SELECT count(*) FROM curada.censo_alcaldia', 16),
]


def consultar(spark, sql):
    """Ejecuta un SELECT que devuelve un solo número, vía JDBC."""
    return (spark.read
            .jdbc(URL, f'({sql}) AS t', properties=PROPS)
            .collect()[0][0])


def reporte(spark):
    """Imprime filas por tabla y verifica las cifras de control.

    Devuelve True si todo cuadra. El trabajo termina con código 1 si no, para
    que docker-compose y cualquier automatización se enteren del fallo.
    """
    print('\n' + '=' * 70)
    print('REPORTE DE CONTROL')
    print('=' * 70)

    print('\nFilas por tabla:')
    for tabla, filas in consultar_conteos(spark):
        print(f'  {tabla:<48} {filas:>6}')

    print('\nCifras de control:')
    todo_bien = True
    for etiqueta, sql, esperado in CONTROLES:
        obtenido = consultar(spark, sql)
        ok = obtenido == esperado
        todo_bien &= ok
        marca = 'OK ' if ok else 'MAL'
        print(f'  [{marca}] {etiqueta:<45} esperado={esperado:>6}  obtenido={obtenido:>6}')

    print()
    if todo_bien:
        print('Todas las cifras de control cuadran.')
    else:
        print('ERROR: al menos una cifra de control no cuadra. Revisa el ETL '
              'antes de usar la base para el tablero.')
    return todo_bien


# Tablas que este trabajo llena, en el orden en que se reportan.
# curada.ageb_centroide_oficial aparece a propósito: debe salir en 0 hasta que
# Karen cargue los polígonos del Marco Geoestadístico.
TABLAS_DESTINO = (
    [f'cruda.{t}' for t in ARCHIVOS_CRUDA] +
    ['curada.censo_ageb', 'curada.censo_ageb_mujeres', 'curada.censo_alcaldia',
     'curada.denue_cuidado', 'curada.ageb_centroide_oficial',
     'indicadores.kpi_cdmx', 'indicadores.resumen_alcaldia',
     'indicadores.carga_ageb', 'indicadores.establecimientos_cuidado',
     'indicadores.enut_carga_actividad', 'indicadores.enut_brecha_mujeres_cdmx',
     'indicadores.enut_doble_jornada', 'indicadores.enut_cuidado_por_grupo',
     'indicadores.enasic_cuidadoras']
)


def consultar_conteos(spark):
    """Cuenta las filas de cada tabla destino, en una sola consulta.

    Se arma un UNION ALL explícito en vez de recorrer el catálogo de PostgreSQL:
    así el reporte siempre lista las mismas tablas, y si una faltara la consulta
    falla en lugar de omitirla en silencio.
    """
    sql = ' UNION ALL '.join(
        f"SELECT '{t}' AS tabla, count(*) AS filas FROM {t}" for t in TABLAS_DESTINO)
    filas = spark.read.jdbc(URL, f'({sql}) AS t', properties=PROPS).collect()
    orden = {t: i for i, t in enumerate(TABLAS_DESTINO)}
    return sorted(((f['tabla'], f['filas']) for f in filas), key=lambda r: orden[r[0]])


# =============================================================================
# 7. PUNTO DE ENTRADA
# =============================================================================

def main():
    spark = (SparkSession.builder
             .appName('observatorio-cuidados-etl')
             # local[*]: un solo proceso, tantos hilos como núcleos. Sin clúster.
             .master('local[*]')
             # Spark baja el driver JDBC de Maven la primera vez y lo cachea.
             .config('spark.jars.packages', PAQUETE_JDBC)
             .config('spark.sql.session.timeZone', 'America/Mexico_City')
             .getOrCreate())
    spark.sparkContext.setLogLevel('WARN')

    print(f'Spark {spark.version} en modo local · origen: {CUR}')
    print(f'Destino: {URL}')

    exito = False
    try:
        dfs = cargar_cruda(spark)
        cur = cargar_curada(spark, dfs)
        cargar_indicadores(spark, dfs, cur)
        exito = reporte(spark)
    finally:
        spark.stop()

    sys.exit(0 if exito else 1)


if __name__ == '__main__':
    main()
