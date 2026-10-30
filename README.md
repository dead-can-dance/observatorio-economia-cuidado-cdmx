# Observatorio de la Economía del Cuidado — CDMX

Proyecto universitario de Ciencia de Datos (UNRC, 7.º semestre) que mide **dónde y cuánto
trabajo de cuidado no remunerado recae sobre las mujeres de la Ciudad de México, y qué
tanto lo alivia la oferta de cuidados que tienen cerca**. Cruza cuatro fuentes públicas
del INEGI —DENUE 05/2026, Censo de Población y Vivienda 2020, ENUT 2024 y ENASIC 2022—
y las deja en una base PostgreSQL organizada en tres capas. Encima de esa base vive el
**observatorio web** (Fase 4): una página que va de lo general a lo particular —México,
Ciudad de México, alcaldías y AGEB— y que se levanta en tu computadora con un solo
comando. La unidad de análisis es la mujer cuidadora; los datos de hombres aparecen solo
como referencia para dimensionar la brecha. Los notebooks que originaron cada tabla se
conservan en el repositorio como evidencia del método.

Encima del diagnóstico hay una **capa analítica** (notebook 03, trabajo integrador de
Analítica para Negocios): la serie histórica de la oferta de cuidado con 19 ediciones del
DENUE y su pronóstico, un modelo que estima las horas de cuidado por AGEB y la evaluación
financiera de una red de cuidado a domicilio en Iztapalapa (escenario simulado). Ver
[Capa analítica: del dato a la decisión](#capa-analítica-del-dato-a-la-decisión).

> **Inicio rápido del observatorio:** `python iniciar.py` y se abre en
> <http://127.0.0.1:8000>. Solo necesita Python 3.10+; ver
> [El observatorio web](#el-observatorio-web-fase-4).
>
> **En internet, sin tu computadora:** la misma historia está en una app de Streamlit
> (`tablero/app.py`) que se publica gratis en Streamlit Community Cloud; ver
> [La versión en Streamlit](#la-versión-en-streamlit).

**Cifras de cabecera** (ver `docs/diccionario_datos.md` para cómo citarlas):

| Cifra | Valor | Fuente |
|---|---|---|
| Mujeres de la CDMX que realizan trabajo de cuidado | 62.2 % | ENUT 2024 |
| Jornada total de las mujeres ocupadas | 77.0 h/semana | ENUT 2024 |
| Brecha de trabajo no pagado, mujeres − hombres ocupados | +12.7 h/semana | ENUT 2024 |
| AGEB con carga alta y sin respaldo a 1 km | 88 | Censo 2020 + DENUE |
| Mujeres de 15 a 59 que viven ahí | 125,256 | Censo 2020 + DENUE |
| Cuidadoras que preferirían el cuidado en casa | 61.2 % | ENASIC 2022 *(nacional)* |
| Oferta formal de respaldo, 01/2016 → 05/2026 | 1,337 → 838 (−37 %) | DENUE, 19 ediciones |
| VAN de la red de cuidado a domicilio, escenario realista | $0.49 millones | Escenario simulado |

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
    NB["notebooks/<br/>02_mujeres_cuidadoras_pp7.ipynb<br/>exploracion_fuentes_pp7.ipynb<br/>03_del_dato_a_la_decision_pp7.ipynb"]
    CUR[("data/curada/<br/>24 CSV · 1.9 MB<br/>versionados en git")]
    SPARK["etl/cargar_capas.py<br/>PySpark en modo local"]

    subgraph pg["PostgreSQL 16"]
        SCRUDA[("cruda<br/>copia 1:1, todo TEXT")]
        SCURADA[("curada<br/>tipos, llaves primarias")]
        SIND[("indicadores<br/>15 tablas listas para graficar")]
    end

    API["backend/ · FastAPI<br/>usuario tablero, solo indicadores"]
    WEB["frontend/ · Vue 3 + ECharts + Leaflet<br/>observatorio web (Fase 4)"]
    ST["tablero/ · Streamlit<br/>versión en línea (Community Cloud)"]

    DESC --> D & C & E & A
    D & C & E & A --> NB
    NB --> CUR
    CUR --> SPARK
    SPARK --> SCRUDA
    SCRUDA --> SCURADA
    SCURADA --> SIND
    SIND --> API
    CUR -.respaldo sin Docker:<br/>mismas reglas del ETL.-> API
    API --> WEB
    API -.mismos módulos de backend/observatorio.-> ST

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

Eso es todo: **no hace falta descargar nada del INEGI.** Las 24 tablas limpias de
`data/curada/` pesan 1.9 MB y vienen en el repositorio, justamente para que el proyecto
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
  [OK ] Respaldo DENUE 05/2026 en la serie histórica  esperado=   838  obtenido=   838

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

## Problemas comunes

**`429 Too Many Requests` al bajar las imágenes.** El build falla con algo como
`failed to copy: httpReadSeeker: failed open: unexpected status code ... 429 Too Many
Requests`. No es el proyecto: Docker Hub limita las descargas por dirección IP a quien
no inicia sesión, y en una red compartida (la universidad, un café) ese límite se gasta
entre todos. Se arregla iniciando sesión con una cuenta gratuita de Docker Hub, que
tiene un límite mucho más alto:

```bash
docker login          # usuario y contraseña de hub.docker.com
docker compose up --build
```

**La primera construcción tarda.** La imagen de Spark pesa cerca de 2 GB, así que el
primer `docker compose up --build` puede llevarse varios minutos bajándola y otro tanto
precargando el driver JDBC en la caché de Ivy. No está colgado. Las veces siguientes
usan la caché de Docker y arrancan en segundos; un `docker compose down -v` borra la
base pero no la imagen, así que no vuelve a pasar por esto.

---

## Conectarse a PostgreSQL desde una herramienta de tablero

El puerto está publicado al host, así que Metabase, Power BI, Superset, Grafana, Tableau,
un notebook o `psql` se conectan igual.

**El tablero se conecta con el usuario `tablero`, no con el administrador.** El
`POSTGRES_USER` de `.env` es el dueño de la base: crea las tablas y las escribe desde el
ETL. El rol `tablero` (lo crea `sql/02_usuario_tablero.sql` al inicializar la base) solo
puede hacer `SELECT` sobre el esquema `indicadores`; `cruda` y `curada` no existen para
él. Si la herramienta de tablero pide credenciales, son estas:

| Parámetro | Valor |
|---|---|
| Host | `localhost` |
| Puerto | `5432` (o el que hayas puesto en `POSTGRES_PORT`) |
| Base de datos | `cuidados` (el `POSTGRES_DB` de tu `.env`) |
| Usuario | **`tablero`** |
| Contraseña | el `TABLERO_PASSWORD` de tu `.env` |
| Esquema | **`indicadores`** |
| SSL | no hace falta en local |

> El rol se crea junto con la base, así que cambiar `TABLERO_PASSWORD` en un `.env` que
> ya levantó una vez no tiene efecto hasta un `docker compose down -v`.

Prueba rápida **sin instalar nada**, usando el `psql` que ya viene en el contenedor:

```bash
docker compose exec db psql -U tablero -d cuidados \
  -c "SELECT etiqueta, valor_num, unidad, nivel_geografico FROM indicadores.kpi_cdmx;"
```

Lo mismo desde tu máquina, si instalaste `postgresql-client`. Te pedirá el
`TABLERO_PASSWORD` que pusiste en `.env`:

```bash
psql -h localhost -p 5432 -U tablero -d cuidados \
     -c "SELECT etiqueta, valor_num, unidad, nivel_geografico FROM indicadores.kpi_cdmx;"
```

Cadena de conexión para SQLAlchemy, Metabase u otras herramientas:

```
postgresql://tablero:TU_TABLERO_PASSWORD@localhost:5432/cuidados
```

Que el usuario del tablero no pueda leer `cruda` ni `curada` es a propósito: son las
capas de auditoría y se consultan con el usuario administrador, desde `psql` o desde un
notebook, no desde una herramienta de visualización.

> Si la herramienta de tablero corre **dentro de la misma red de Docker**, el host no es
> `localhost` sino `db`, y el puerto siempre `5432`.

**Apunta al esquema `indicadores` y a ningún otro.** `docs/diccionario_datos.md` describe
las quince tablas, sus columnas y, sobre todo, cómo *no* leerlas.

---

## El observatorio web (Fase 4)

Una página que responde la pregunta rectora de lo general a lo particular:

| Sección | Escala | Fuentes | Qué muestra |
|---|---|---|---|
| 01 · México | Nacional | ENUT 2024, ENASIC 2022 | Quiénes cuidan y cuánto en el país; las cuidadoras y los servicios de cuidado (solo nacional). |
| 02 · Ciudad de México | CDMX | ENUT 2024, Censo 2020 | Hallazgo A (doble jornada), la ciudad frente al país, la brecha por actividad y qué mujeres cuidan más. |
| 03 · Alcaldías | Alcaldía | Censo 2020 + DENUE | Mosaico y ranking de 11 indicadores, ficha de cada alcaldía con sus hallazgos, carga contra presión sobre las guarderías y tabla completa. |
| 04 · Territorio | AGEB | Censo 2020 + DENUE | Hallazgo B (exploratorio): mapa de las 2,320 AGEB, las 88 sin respaldo, embudo y distribución de la carga. |
| 05 · Metodología | — | — | Las siete advertencias, fuentes, glosario, descargas en CSV y estado de las cifras de control. |

### Cómo levantarlo

```bash
python iniciar.py
```

- La primera vez crea un entorno virtual e instala `backend/requirements.txt` (unos
  minutos, con internet). Si el repositorio está dentro de OneDrive, el entorno se crea en
  `%LOCALAPPDATA%\observatorio-cuidado\.venv` para no sincronizar miles de archivos a la
  nube; si no, en `.venv/`. Las siguientes veces arranca en segundos y sin internet.
- Abre <http://127.0.0.1:8000> en el navegador. `Ctrl+C` lo detiene.
- Opciones: `--puerto 8080`, `--fuente csv|postgres|auto`, `--red` (visible para otros
  equipos de tu red local), `--sin-navegador`, `--recarga` (para desarrollo) y
  `--pruebas` (corre las pruebas del backend).

No necesita Node.js ni Docker. Vue, ECharts y Leaflet están copiados en `frontend/vendor/`
con su versión y su verificación de integridad (`frontend/vendor/VERSIONES.md`), así que
la página funciona sin internet; lo único que se pide fuera es el mapa base de
OpenStreetMap, que se puede apagar desde la propia página.

### De dónde lee los datos

El backend respeta la regla del proyecto: **solo lee el esquema `indicadores`**.

| Modo (`--fuente` u `OBSERVATORIO_FUENTE`) | Qué hace |
|---|---|
| `auto` (por omisión) | Si hay `.env` con `TABLERO_PASSWORD` y la base responde, lee PostgreSQL con el rol `tablero`. Si no, reconstruye las quince tablas de `indicadores` desde `data/curada/` con las mismas reglas que `etl/cargar_capas.py` (columnas, tipos y redondeo). |
| `postgres` | Solo PostgreSQL; si la base no responde, no arranca. |
| `csv` | Solo la réplica local. |

Para usar la base: `docker compose up --build -d` (ver arriba) y después `python iniciar.py`.
En cualquier modo, al arrancar se verifican las mismas cifras de control que el ETL (más
las del README), y la sección de Metodología muestra la fuente activa y el resultado. Si
alguna cifra no cuadra, la página lo avisa en una franja roja.

### La API

Documentación interactiva en <http://127.0.0.1:8000/api/docs>. Rutas principales:

| Ruta | Devuelve |
|---|---|
| `/api/estado` | Fuente activa y cifras de control |
| `/api/kpis` | `indicadores.kpi_cdmx` (filtro `?nivel=CDMX` o `Nacional`) |
| `/api/hallazgos/{nacional,cdmx,alcaldias}` | Hallazgos redactados a partir de los datos, cada uno con fuente y nivel |
| `/api/enut/carga-actividad`, `/api/enut/brecha`, `/api/enut/doble-jornada` | ENUT 2024 |
| `/api/enut/cuidado-por-grupo?tipo_grupo=…` | Edad o condición de actividad: el parámetro es obligatorio porque no se mezclan |
| `/api/enasic` | ENASIC 2022 por tema, con su base (siempre nacional) |
| `/api/alcaldias`, `/api/alcaldias/{cve_mun}` | Las 16 alcaldías y la ficha de cada una |
| `/api/agebs`, `/api/establecimientos`, `/api/territorio` | Capas del mapa, embudo y distribución de la carga |
| `/api/indicadores/{tabla}` y `/api/indicadores/{tabla}.csv` | Cualquiera de las quince tablas, en JSON o CSV |

Toda respuesta con cifras lleva `fuente` y `nivel_geografico`. Los hallazgos no están
escritos a mano: se calculan con los datos y respetan las advertencias del
diccionario de datos (una prueba automática lo verifica).

### Pruebas

```bash
python iniciar.py --pruebas
```

Verifican que la réplica reproduce las cifras de control y los tipos del DDL (incluido el
redondeo de Spark), que la ruta de PostgreSQL produce tablas idénticas, que la API respeta
las restricciones del diccionario y que el frontend se sirve con los tipos MIME correctos.
El mismo comando corre también las pruebas de la app de Streamlit (`tablero/tests/`).

### Decisiones de diseño

- **Vue 3 sin paso de compilación.** Las plantillas se compilan en el navegador: no hace
  falta Node.js para correr ni para modificar el frontend.
- **Mosaico de alcaldías en lugar de coropletas.** El repositorio no tiene los polígonos
  del Marco Geoestadístico; el mosaico ubica cada alcaldía en su posición aproximada sin
  fingir una geografía que no tenemos. Con los polígonos se puede cambiar por coropletas.
- **Paleta violeta validada.** Mismo perfil de luminosidad que la rampa de referencia de
  la guía de visualización, verificada para daltonismo y contraste (detalle en
  `frontend/css/tokens.css`). Cada gráfica tiene su tabla gemela («Ver tabla») y hay tema
  claro y oscuro.

---

## La versión en Streamlit

`tablero/app.py` cuenta la misma historia que la página web, en siete páginas: Inicio,
México, Ciudad de México, Alcaldías, Territorio, **Decisión** y Metodología. No duplica
cálculos: importa `backend/observatorio`, así que usa la misma réplica del ETL, las mismas
cifras de control y los mismos hallazgos redactados. La página «Decisión» solo existe en
Streamlit: es el dashboard del trabajo integrador (KPIs contra su meta, pronóstico, modelo,
escenarios y un simulador del programa). Existe para publicar el observatorio en internet
sin depender de que una computadora del equipo esté prendida.

### Probarla en tu computadora

```bash
python iniciar.py --streamlit        # http://127.0.0.1:8501
```

La primera vez instala `tablero/requirements.txt` en el mismo entorno virtual.

### Publicarla en Streamlit Community Cloud (gratis)

1. Entra a <https://share.streamlit.io> con **Continue with GitHub**. La cuenta tiene que
   ser administradora del repositorio (la dueña, `dead-can-dance`); una cuenta que solo
   colabora puede editar la app pero no publicarla. La alternativa es hacer un fork a la
   cuenta propia y publicar desde el fork.
2. **Create app** → desplegar desde GitHub, con estos datos:

   | Campo | Valor |
   |---|---|
   | Repository | `dead-can-dance/observatorio-economia-cuidado-cdmx` |
   | Branch | `observatorio-streamlit` (o `main`, cuando se fusione) |
   | Main file path | `tablero/app.py` |
   | Advanced settings → Python | 3.12 |

3. **Deploy**. La primera vez tarda unos minutos en instalar dependencias. Después, cada
   `git push` a esa rama actualiza la app sola.

En la nube no hay `.env` ni PostgreSQL, así que la app reconstruye las tablas de
`indicadores` desde `data/curada/` (la página de Metodología dice qué fuente usó). Las
apps gratuitas se duermen si nadie las visita por un tiempo; la primera visita después
tarda unos segundos en despertarla. Los colores y el tema están en `.streamlit/config.toml`.

### Decisiones de la versión en Streamlit

- **Gráficas en Altair y mapa en pydeck**, los dos incluidos en Streamlit: no hay
  dependencias extra. El mapa base es el de CARTO que Streamlit elige según el tema.
- **Colores de datos que sirven en tema claro y oscuro.** Streamlit no siempre sabe al
  abrir la app qué tema usa la persona, así que el acento (#6f5bf0), el gris de referencia
  y los tres tramos de la doble jornada se validaron contra los dos fondos (detalle en
  `tablero/estilo.py`). El texto de las gráficas toma el color del tema.
- **Clic para elegir.** Una casilla del mosaico, una barra del ranking o un punto de la
  dispersión cambian la ficha de alcaldía, y «Ver sus AGEB en el mapa» lleva a Territorio
  con esa alcaldía enfocada.

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

El notebook 03 (capa analítica) se corre después de los otros dos, porque lee
`data/curada/mujeres_carga_acceso_ageb.csv`:

```bash
jupyter nbconvert --to notebook --execute --inplace notebooks/03_del_dato_a_la_decision_pp7.ipynb
```

La primera vez descarga las 18 ediciones históricas del DENUE de la CDMX (~45 MB cada una),
cuenta los establecimientos de respaldo y borra cada zip: solo deja
`data/raw/denue_historico/conteos.csv`. Necesita además `scikit-learn`, `statsmodels` y
`openpyxl`. Si cambias un supuesto en `backend/observatorio/factibilidad.py`, vuelve a
correrlo: el observatorio avisa con una cifra de control si la tabla de escenarios ya no
coincide con el módulo.

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
├── iniciar.py                   Levanta el observatorio web (o la app de Streamlit)
├── docker-compose.yml           Los dos servicios: db y etl
├── .streamlit/config.toml       Tema y colores de la app de Streamlit
├── .env.example                 Plantilla de credenciales (copiar a .env)
├── .gitignore                   Excluye data/raw/, *.zip, .env, checkpoints
│
├── backend/                     API del observatorio (FastAPI)
│   ├── observatorio/            esquema de indicadores, fuentes (PostgreSQL o
│   │                            réplica del ETL), hallazgos, metodología, rutas
│   │                            y factibilidad.py (modelo financiero del programa)
│   ├── tests/                   Pruebas (pytest)
│   └── requirements.txt
├── frontend/                    Página del observatorio (Vue 3 sin compilación)
│   ├── index.html
│   ├── css/                     tokens.css (paleta claro/oscuro) y estilos.css
│   ├── js/                      secciones, componentes y gráficas
│   └── vendor/                  Vue, ECharts y Leaflet, copiados y verificados
├── tablero/                     App de Streamlit (versión en línea)
│   ├── app.py                   Archivo principal y navegación
│   ├── paginas/                 Las siete páginas (decision.py: trabajo integrador)
│   ├── datos.py, graficas.py,   Carga de datos, gráficas en Altair, mapa en
│   │   mapa.py, componentes.py  pydeck y piezas comunes
│   ├── tests/                   Pruebas (AppTest de Streamlit)
│   └── requirements.txt         Lo que instala Streamlit Community Cloud
│
├── docker/
│   └── spark/
│       └── Dockerfile           Imagen del ETL, sobre apache/spark:4.0.4-python3
│
├── sql/
│   ├── 01_esquemas.sql          Esquemas y DDL de curada e indicadores,
│   │                            con COMMENT en las 180 columnas
│   └── 02_usuario_tablero.sql   Rol `tablero`: solo lectura sobre indicadores
├── etl/
│   ├── descargar_datos.py       Descarga las 4 fuentes del INEGI a data/raw/
│   └── cargar_capas.py          Trabajo de PySpark: cruda → curada → indicadores
│
├── notebooks/
│   ├── 02_mujeres_cuidadoras_pp7.ipynb    Notebook principal; de aquí salen los
│   │                                      tres hallazgos y 12 de los CSV
│   ├── exploracion_fuentes_pp7.ipynb      Anexo: primera exploración de las 4 fuentes
│   ├── 03_del_dato_a_la_decision_pp7.ipynb   Capa analítica: serie y pronóstico de la
│   │                                      oferta, modelo de horas, factibilidad
│   └── anexo_excel.py                     Genera el anexo de Excel con fórmulas
│
├── data/
│   ├── curada/                  24 CSV limpios, 1.9 MB — SÍ se versionan
│   └── raw/                     Microdatos del INEGI — NO se versionan
│
├── figuras/                     Gráficas generadas por los notebooks
│
└── docs/
    ├── diccionario_datos.md     Las 15 tablas de indicadores, columna por columna,
    │                            y la sección "Cómo NO leer estos datos"
    └── anexos/
        └── anexo_A_calculos_pp7.xlsx   Pronóstico, modelo y factibilidad con fórmulas
```

---

## Capa analítica: del dato a la decisión

Trabajo integrador de Analítica para Negocios. Responde si conviene invertir en una **red de
cuidado a domicilio** en las 25 AGEB de Iztapalapa de alta carga y sin respaldo, y bajo qué
condiciones. Todo sale de `notebooks/03_del_dato_a_la_decision_pp7.ipynb`:

| Capa | Qué se hizo | Resultado |
|---|---|---|
| Descriptiva | Serie de la oferta de respaldo con 19 ediciones del DENUE (2016-2026) | 1,337 → 838 establecimientos (−37 %); las guarderías, −47 %. Las caídas llegan en escalones, con los Censos Económicos 2019 y 2024. |
| Predictiva (series de tiempo) | Ingenuo, suavizamiento simple, Holt amortiguado, deriva y ARIMA(0,1,1) con origen móvil | Gana el ingenuo (MAPE de 2.9 % a un semestre): la oferta se queda en ~838 y el riesgo es solo a la baja. |
| Predictiva (modelo) | Regresión lineal contra Random Forest de las horas de cuidado de cada mujer de 15 a 59 (ENUT 2024, 30,301 mujeres), aplicada al Censo por AGEB | La lineal predice el promedio de una entidad que no vio con MAPE de 7.8 %; el Random Forest con promedios, 50.6 %. Se elige la lineal. |
| Prescriptiva | VAN, TIR, payback y punto de equilibrio en tres escenarios a 60 meses, al 10 % real | Realista: VAN de $0.49 millones y TIR de 31.5 %. Valor esperado invirtiendo por etapas: $1.08 millones. |

**Recomendación:** invertir por etapas, condicionado a un subsidio de al menos $40 por hora
(el VAN realista llega a cero con $38), a una revisión en el mes 12 y a financiar el
déficit acumulado máximo (~$0.82 millones), no solo la fórmula clásica de capital.

El modelo financiero vive en `backend/observatorio/factibilidad.py`, para que el notebook, el
anexo de Excel (`docs/anexos/anexo_A_calculos_pp7.xlsx`, con fórmulas vivas) y la página
«Decisión» de Streamlit usen las mismas reglas. El programa y su operador son un **escenario
simulado** (ver advertencia 7 del diccionario).

---

## Documentos relacionados

- **`docs/diccionario_datos.md`** — qué hay en cada tabla de `indicadores` y las siete
  advertencias que hay que respetar al citar cualquier cifra. Lectura obligatoria antes
  de construir el tablero.

El contexto del proyecto, el reparto de tareas y las fichas técnicas por fuente viven en
Notion, no en el repositorio.

## Estado y pendientes

- El hallazgo B (zonas sin respaldo) es **exploratorio** hasta que se integren los
  polígonos del Marco Geoestadístico del INEGI en `curada.ageb_centroide_oficial`, hoy
  vacía a propósito.
- Los márgenes de error formales de la ENUT y la ENASIC, con diseño muestral
  (`est_dis`, `upm_dis`, factores de expansión), están pendientes; las banderas
  `precision_baja` y `confiable` son por ahora un semáforo por tamaño de muestra.
- PostGIS no está activado. Los conteos a 1 km vienen precalculados en los CSV; cuando se
  integren los polígonos conviene rehacerlos en SQL con `ST_DWithin`.
- Con los polígonos, el observatorio web puede cambiar el mosaico de alcaldías por un mapa
  de coropletas y los puntos de las AGEB por sus polígonos.
- El modelo de horas por AGEB es una estimación ecológica: sus variables de AGEB son
  promedios por hogar del Censo y no la composición exacta del hogar de cada mujer. Con los
  microdatos del Censo (muestra ampliada) se podría estimar por municipio con menos supuestos.
- El pronóstico de la oferta no incorpora los 300 Centros de Cuidado Infantil anunciados por
  la CDMX en 09/2026. Cuando aparezcan en el DENUE habrá que volver a correr el notebook 03.
- La plataforma de vinculación (*matching*) del programa la desarrolla otra parte del equipo;
  la factibilidad solo incluye sus costos.
- El nivel nacional del observatorio se limita a lo que traen los datos del repositorio
  (ENUT 2024 nacional y ENASIC 2022). Un desglose por entidad o el valor económico del
  trabajo no remunerado (Cuenta Satélite del INEGI) requerirían fuentes nuevas.
