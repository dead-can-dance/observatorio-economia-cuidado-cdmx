# =============================================================================
# Trabajo de PySpark del Observatorio de la Economía del Cuidado.
#
# Imagen oficial de Apache Spark con Python, fijada a una versión concreta.
# Nada de Alpine: PySpark y sus dependencias dan problemas con musl, y el
# propio INEGI-PP7 ya lo había advertido en las instrucciones del equipo.
#
# Spark 4.x es obligatorio, no una preferencia: el ETL usa Column.try_cast(),
# que no existe en Spark 3.
# =============================================================================
FROM apache/spark:4.0.4-python3

# Debe coincidir con PAQUETE_JDBC en etl/cargar_capas.py. Si se cambia uno,
# hay que cambiar el otro: aquí se usa para precargar la caché de Ivy.
ARG PAQUETE_JDBC=org.postgresql:postgresql:42.7.4

# La imagen corre como el usuario spark (uid 185) y su HOME es /nonexistent,
# así que Ivy no tendría dónde dejar la caché de los paquetes y el trabajo
# fallaría al resolver el driver JDBC. Hay que crearle directorios propios.
USER root

ENV APP_DIR=/app \
    IVY_DIR=/opt/ivy \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=${SPARK_HOME}/python:${SPARK_HOME}/python/lib/py4j-0.10.9.9-src.zip

# La imagen base no trae $SPARK_HOME/conf; se crea para fijar ahí el directorio
# de Ivy. Así el script de Python no necesita saber nada de Docker.
RUN mkdir -p "${APP_DIR}" "${IVY_DIR}" "${SPARK_HOME}/conf" \
    && printf 'spark.jars.ivy %s\n' "${IVY_DIR}" > "${SPARK_HOME}/conf/spark-defaults.conf" \
    && chown -R 185:185 "${APP_DIR}" "${IVY_DIR}" "${SPARK_HOME}/conf"

WORKDIR ${APP_DIR}

# El ETL y las tablas limpias. data/raw/ NO entra: pesa ~175 MB y el trabajo no
# lo necesita, lee únicamente los CSV de data/curada/.
COPY --chown=185:185 etl/ ${APP_DIR}/etl/
COPY --chown=185:185 data/curada/ ${APP_DIR}/data/curada/

USER spark

# Precargar el driver JDBC en la caché de Ivy durante el build. Sin esto, el
# contenedor tendría que bajarlo de Maven en cada arranque: lento y, sobre todo,
# dependiente de la red justo cuando uno quiere levantar el proyecto.
RUN printf 'from pyspark.sql import SparkSession\nSparkSession.builder.master("local[1]").appName("precalentar").getOrCreate().stop()\n' > /tmp/precalentar.py \
    && "${SPARK_HOME}/bin/spark-submit" --master 'local[1]' \
         --packages "${PAQUETE_JDBC}" /tmp/precalentar.py > /dev/null 2>&1 \
    && rm /tmp/precalentar.py \
    && ls "${IVY_DIR}/jars" | grep -q postgresql

# La imagen base entra por /opt/entrypoint.sh, pensado para Spark en Kubernetes.
# Aquí no hace falta: el trabajo es un proceso que corre y termina.
ENTRYPOINT []
CMD ["python3", "etl/cargar_capas.py"]
