# Observatorio de la Economía del Cuidado — CDMX

Proyecto universitario de Ciencia de Datos (UNRC, 7.º semestre) que mide **dónde y cuánto
trabajo de cuidado no remunerado recae sobre las mujeres de la Ciudad de México, y qué
tanto lo alivia la oferta de cuidados que tienen cerca**. Cruza cuatro fuentes públicas
del INEGI —DENUE 05/2026, Censo de Población y Vivienda 2020, ENUT 2024 y ENASIC 2022—
y las deja en una base PostgreSQL organizada en tres capas, lista para construir un
tablero encima. La unidad de análisis es la mujer cuidadora; los datos de hombres
aparecen solo como referencia para dimensionar la brecha. Los notebooks que originaron
cada tabla se conservan en el repositorio como evidencia del método.

**Cifras de cabecera** (ver `docs/diccionario_datos.md` para cómo citarlas):

| Cifra | Valor | Fuente |
|---|---|---|
| Mujeres de la CDMX que realizan trabajo de cuidado | 62.2 % | ENUT 2024 |
| Jornada total de las mujeres ocupadas | 77.0 h/semana | ENUT 2024 |
| Brecha de trabajo no pagado, mujeres − hombres ocupados | +12.7 h/semana | ENUT 2024 |
| AGEB con carga alta y sin respaldo a 1 km | 88 | Censo 2020 + DENUE |
| Mujeres de 15 a 59 que viven ahí | 125,256 | Censo 2020 + DENUE |
| Cuidadoras que preferirían el cuidado en casa | 61.2 % | ENASIC 2022 *(nacional)* |

---

## Arquitectura

```mermaid
flowchart TD
    subgraph fuentes["Fuentes INEGI (data/raw/, fuera de git)"]
        D["DENUE 05/2026<br/>462,732 establecimientos CDMX"]
        C["Censo 2020<br/>AGEB y manzana urbana"]
        E["ENUT 2024<br/>uso del tiempo"]
        A["ENASIC 2022<br/>población cuidadora"]
    end

    DESC["etl/descargar_datos.py"]
    NB["notebooks/<br/>02_mujeres_cuidadoras_pp7.ipynb<br/>exploracion_fuentes_pp7.ipynb"]
    CUR[("data/curada/<br/>18 CSV · 1.5 MB<br/>versionados en git")]
    SPARK["etl/cargar_capas.py<br/>PySpark en modo local"]

    subgraph pg["PostgreSQL 16"]
        SCRUDA[("cruda<br/>copia 1:1, todo TEXT")]
        SCURADA[("curada<br/>tipos, llaves primarias")]
        SIND[("indicadores<br/>listo para graficar")]
    end

    DASH["Tablero<br/>(Fase 4)"]

    DESC --> D & C & E & A
    D & C & E & A --> NB
    NB --> CUR
    CUR --> SPARK
    SPARK --> SCRUDA
    SCRUDA --> SCURADA
    SCURADA --> SIND
    SIND --> DASH

    SQLDDL["sql/01_esquemas.sql"] -.define.-> SCURADA & SIND
```

Las tres capas y por qué existen:

| Capa | Qué contiene | Quién la crea |
|---|---|---|
| `cruda` | Copia 1:1 de cada CSV, **todas las columnas TEXT**. Permite rastrear cualquier cifra del tablero hasta el archivo de origen. | Spark, al cargar |
| `curada` | Entidades con tipos correctos y llave primaria: establecimientos, AGEB, alcaldías. | `sql/01_esquemas.sql` define, Spark llena |
| `indicadores` | Tablas ya agregadas y cruzadas, con `nivel_geografico` y `fuente` en cada fila. **Es lo único que debe leer el tablero.** | `sql/01_esquemas.sql` define, Spark llena |

---

## Requisitos

Para levantar la base y el ETL, lo único que hace falta:

- **Docker** y **Docker Compose v2 o superior**
- ~4 GB de disco libre (la imagen de Spark es grande) y conexión a internet la primera vez

Opcional, solo si quieres consultar la base con `psql` desde tu máquina en vez de desde
el contenedor: **`postgresql-client`** (`sudo apt install postgresql-client` en
Debian/Ubuntu, `brew install libpq` en macOS). No es necesario: más abajo hay una
alternativa que corre dentro de Docker.

Para volver a ejecutar los notebooks, además:

- **Python 3.10+** con `pandas>=2.2,<3`, `numpy`, `matplotlib`, `scikit-learn` y `jupyter`
  > El tope de pandas no es un capricho: en pandas 3.0 se eliminó el parámetro
  > `include_groups` que usa el notebook 02 y el cuaderno truena.
- En Debian/Ubuntu, el paquete **`python3-venv`** (`sudo apt install python3-venv`). No
  viene de fábrica y sin él `python3 -m venv` falla con *"ensurepip is not available"*.
- ~400 MB de disco para los microdatos del INEGI

---

## Cómo levantarlo

```bash
# 1. Clonar
git clone https://github.com/dead-can-dance/observatorio-economia-cuidado-cdmx
cd observatorio-economia-cuidado-cdmx

# 2. Crear el archivo de credenciales y cambiar la contraseña
cp .env.example .env
#    editar .env y poner un POSTGRES_PASSWORD propio

# 3. Levantar
docker compose up --build
```

> **Si el puerto 5432 ya está ocupado** —porque tienes PostgreSQL instalado o algún otro
> proyecto corriendo— el arranque falla con *"port is already allocated"*. No hay que
> apagar nada: cambia `POSTGRES_PORT` en tu `.env` (por ejemplo `55432`) y vuelve a
> levantar. Solo cambia el puerto del host; dentro de Docker la base sigue en el 5432.

Eso es todo: **no hace falta descargar nada del INEGI.** Las 18 tablas limpias de
`data/curada/` pesan 1.5 MB y vienen en el repositorio, justamente para que el proyecto
se levante sin bajar los ~175 MB de microdatos.

Qué pasa al correr ese comando:

1. `db` arranca con PostgreSQL 16 y ejecuta `sql/01_esquemas.sql`, que crea los tres
   esquemas y 14 tablas con tipos, llaves primarias y comentarios.
2. El *healthcheck* con `pg_isready` espera a que la base acepte conexiones.
3. `etl` arranca solo entonces, corre el trabajo de PySpark y termina.

La primera construcción tarda varios minutos, casi todo bajando la imagen de Spark; las
siguientes usan caché. Al final verás el reporte de control:

```
Cifras de control:
  [OK ] Establecimientos de cuidado del DENUE         esperado=  1463  obtenido=  1463
  [OK ] AGEB con carga alta y sin respaldo a 1 km     esperado=    88  obtenido=    88
  [OK ] Alcaldías en indicadores.resumen_alcaldia     esperado=    16  obtenido=    16
  [OK ] Alcaldías en curada.censo_alcaldia            esperado=    16  obtenido=    16
  [OK ] Brecha ENUT de trabajo no pagado (h)          esperado=  12.7  obtenido=  12.7

Todas las cifras de control cuadran.
```

Si alguna cifra no cuadra, el contenedor termina con código 1. Es el criterio de
terminado del equipo: borrar la base, correr todo y obtener los mismos números.

**El comando no devuelve el prompt**, porque `db` es un servicio permanente y la terminal
queda mostrando sus registros. Es lo correcto: la base debe seguir arriba para el
tablero. Si prefieres recuperar el prompt:

```bash
docker compose up --build -d     # en segundo plano
docker compose logs etl          # ver el reporte
```

Otros comandos útiles:

```bash
docker compose ps                # estado de los servicios
docker compose run --rm etl      # volver a correr solo el ETL
docker compose down              # apagar, conservando los datos
docker compose down -v           # apagar y BORRAR la base
```

---

## Conectarse a PostgreSQL desde una herramienta de tablero

El puerto está publicado al host, así que Metabase, Power BI, Superset, Grafana, Tableau,
un notebook o `psql` se conectan igual:

| Parámetro | Valor |
|---|---|
| Host | `localhost` |
| Puerto | `5432` (o el que hayas puesto en `POSTGRES_PORT`) |
| Base de datos | `cuidados` (el `POSTGRES_DB` de tu `.env`) |
| Usuario | el `POSTGRES_USER` de tu `.env` |
| Contraseña | el `POSTGRES_PASSWORD` de tu `.env` |
| Esquema | **`indicadores`** |
| SSL | no hace falta en local |

Prueba rápida **sin instalar nada**, usando el `psql` que ya viene en el contenedor:

```bash
docker compose exec db psql -U observatorio -d cuidados \
  -c "SELECT etiqueta, valor_num, unidad, nivel_geografico FROM indicadores.kpi_cdmx;"
```

Lo mismo desde tu máquina, si instalaste `postgresql-client`. Te pedirá la contraseña
que pusiste en `.env`:

```bash
psql -h localhost -p 5432 -U observatorio -d cuidados \
     -c "SELECT etiqueta, valor_num, unidad, nivel_geografico FROM indicadores.kpi_cdmx;"
```

Cadena de conexión para SQLAlchemy, Metabase u otras herramientas:

```
postgresql://observatorio:TU_CONTRASEÑA@localhost:5432/cuidados
```

> Si la herramienta de tablero corre **dentro de la misma red de Docker**, el host no es
> `localhost` sino `db`, y el puerto siempre `5432`.

**Apunta al esquema `indicadores` y a ningún otro.** `docs/diccionario_datos.md` describe
las nueve tablas, sus columnas y, sobre todo, cómo *no* leerlas.

---

## Regenerar los datos desde cero

Los CSV de `data/curada/` ya están en el repositorio, así que esto solo hace falta para
verificar el método, cambiar un cálculo o actualizar una fuente del INEGI.

```bash
# 1. Entorno de Python  (en Debian/Ubuntu: sudo apt install python3-venv)
python3 -m venv .venv && source .venv/bin/activate
pip install "pandas>=2.2,<3" numpy matplotlib scikit-learn jupyter

# 2. Descargar los microdatos del INEGI a data/raw/ (~175 MB comprimidos)
python etl/descargar_datos.py

# 3. Ejecutar los notebooks, que reescriben data/curada/
jupyter nbconvert --to notebook --execute --inplace notebooks/exploracion_fuentes_pp7.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/02_mujeres_cuidadoras_pp7.ipynb

# 4. Recargar la base desde los CSV nuevos
docker compose down -v
docker compose up --build
```

El script de descarga es idempotente: si un archivo ya existe en `data/raw/`, no lo
vuelve a bajar. Los notebooks se pueden abrir también con `jupyter lab` desde
`notebooks/`; resuelven las rutas contra la raíz del repositorio, así que encuentran
`data/` y `figuras/` desde cualquiera de los dos directorios.

Al terminar el paso 3, el notebook 02 debe imprimir estas cifras de control. Si alguna no
coincide, hay que avisar al equipo antes de seguir:

| Cifra de control | Valor esperado |
|---|---|
| % de mujeres de la CDMX que cuidan (ENUT) | 62.2 |
| Jornada total de mujeres ocupadas (ENUT) | 77.0 h |
| Brecha de trabajo no pagado, mujeres − hombres ocupados (ENUT) | 12.7 h |
| AGEB con carga alta y sin respaldo | 88 |
| % de cuidadoras que prefiere cuidado en casa (ENASIC) | 61.2 |

`data/raw/` está en `.gitignore`: los microdatos del INEGI nunca se suben al repositorio.

---

## Estructura de carpetas

```
.
├── docker-compose.yml           Los dos servicios: db y etl
├── .env.example                 Plantilla de credenciales (copiar a .env)
├── .gitignore                   Excluye data/raw/, *.zip, .env, checkpoints
│
├── docker/
│   └── spark/
│       └── Dockerfile           Imagen del ETL, sobre apache/spark:4.0.4-python3
│
├── sql/
│   └── 01_esquemas.sql          Esquemas y DDL de curada e indicadores,
│                                con COMMENT en las 180 columnas
├── etl/
│   ├── descargar_datos.py       Descarga las 4 fuentes del INEGI a data/raw/
│   └── cargar_capas.py          Trabajo de PySpark: cruda → curada → indicadores
│
├── notebooks/
│   ├── 02_mujeres_cuidadoras_pp7.ipynb    Notebook principal; de aquí salen los
│   │                                      tres hallazgos y 12 de los CSV
│   └── exploracion_fuentes_pp7.ipynb      Anexo: primera exploración de las 4 fuentes
│
├── data/
│   ├── curada/                  18 CSV limpios, 1.5 MB — SÍ se versionan
│   └── raw/                     Microdatos del INEGI — NO se versionan
│
├── figuras/                     Gráficas generadas por los notebooks
│
└── docs/
    └── diccionario_datos.md     Las 9 tablas de indicadores, columna por columna,
                                 y la sección "Cómo NO leer estos datos"
```

---

## Documentos relacionados

- **`docs/diccionario_datos.md`** — qué hay en cada tabla de `indicadores` y las cinco
  advertencias que hay que respetar al citar cualquier cifra. Lectura obligatoria antes
  de construir el tablero.
- **`LEEME.md`** — contexto del proyecto, hallazgos candidatos y reparto de tareas.
- **`INSTRUCCIONES_EQUIPO.md`** — instrucciones por persona y plantilla de ficha técnica
  por fuente.

## Estado y pendientes

- El hallazgo B (zonas sin respaldo) es **exploratorio** hasta que se integren los
  polígonos del Marco Geoestadístico del INEGI en `curada.ageb_centroide_oficial`, hoy
  vacía a propósito.
- Los márgenes de error formales de la ENUT y la ENASIC, con diseño muestral
  (`est_dis`, `upm_dis`, factores de expansión), están pendientes; las banderas
  `precision_baja` y `confiable` son por ahora un semáforo por tamaño de muestra.
- PostGIS no está activado. Los conteos a 1 km vienen precalculados en los CSV; cuando se
  integren los polígonos conviene rehacerlos en SQL con `ST_DWithin`.
