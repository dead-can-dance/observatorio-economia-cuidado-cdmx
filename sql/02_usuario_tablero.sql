-- =============================================================================
-- Observatorio de la Economía del Cuidado — PP7 UNRC
-- Usuario de solo lectura para el tablero.
--
-- Se ejecuta junto con 01_esquemas.sql al inicializar el contenedor de
-- PostgreSQL (va montado en /docker-entrypoint-initdb.d/), después de que los
-- esquemas existen. Es idempotente: se puede volver a correr sin romper nada.
--
-- Por qué existe: el usuario de .env (POSTGRES_USER) es el administrador de la
-- base, el dueño de las tablas y el que usa el ETL para escribir. El tablero no
-- necesita nada de eso. Se conecta con el rol `tablero`, que solo puede LEER el
-- esquema `indicadores` y no ve `cruda` ni `curada`.
-- =============================================================================


-- -----------------------------------------------------------------------------
-- 1. Contraseña
--
-- No se escribe aquí: se toma de TABLERO_PASSWORD, que el contenedor recibe de
-- .env (env_file en docker-compose.yml). \getenv la trae al entorno de psql.
-- El \set previo deja la variable en vacío si la variable de entorno no existe,
-- porque \getenv no la define en ese caso.
-- -----------------------------------------------------------------------------
\set tablero_password ''
\getenv tablero_password TABLERO_PASSWORD

-- El valor se pasa a un parámetro de sesión para poder revisarlo desde PL/pgSQL:
-- psql no sustituye :'variables' dentro de un bloque $$ ... $$. Se usa SET y no
-- set_config() porque SET no devuelve filas: un SELECT imprimiría la contraseña
-- en los registros del contenedor.
SET observatorio.tablero_password TO :'tablero_password';

DO $$
BEGIN
    IF coalesce(current_setting('observatorio.tablero_password', true), '') = '' THEN
        RAISE EXCEPTION
            'Falta TABLERO_PASSWORD en .env. Cópiala de .env.example, pon una '
            'contraseña propia y vuelve a levantar con docker compose down -v.';
    END IF;
END $$;


-- -----------------------------------------------------------------------------
-- 2. El rol
--
-- LOGIN porque es un usuario que se conecta; sin CREATEDB, sin CREATEROLE y sin
-- SUPERUSER, que son los valores por omisión de CREATE ROLE.
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'tablero') THEN
        CREATE ROLE tablero LOGIN;
    END IF;
END $$;

-- Fuera del DO para poder interpolar la contraseña con :'...', que psql escribe
-- como literal entrecomillado. Así el rol queda con la contraseña de .env tanto
-- si acaba de crearse como si ya existía.
ALTER ROLE tablero WITH LOGIN PASSWORD :'tablero_password';

COMMENT ON ROLE tablero IS
    'Usuario de solo lectura del tablero. Solo SELECT sobre el esquema '
    'indicadores. No debe usarse para el ETL ni para administrar la base.';


-- -----------------------------------------------------------------------------
-- 3. Permisos sobre `indicadores`: USAGE y SELECT, nada más
-- -----------------------------------------------------------------------------
GRANT USAGE ON SCHEMA indicadores TO tablero;
GRANT SELECT ON ALL TABLES IN SCHEMA indicadores TO tablero;

-- Las tablas que existan en el futuro. ALTER DEFAULT PRIVILEGES aplica a lo que
-- cree el rol actual (el POSTGRES_USER de .env), que es justamente quien crea
-- las tablas: este archivo y el trabajo de Spark corren con ese usuario.
ALTER DEFAULT PRIVILEGES IN SCHEMA indicadores GRANT SELECT ON TABLES TO tablero;


-- -----------------------------------------------------------------------------
-- 4. Nada sobre `cruda` ni `curada`
--
-- Un rol nuevo no tiene permisos sobre esos esquemas, así que bastaría con no
-- otorgarle ninguno. El REVOKE va explícito para que se lea como una decisión y
-- no como un olvido: el tablero cita cifras de `indicadores`, y las capas de
-- auditoría no se exponen a una herramienta de visualización.
-- -----------------------------------------------------------------------------
REVOKE ALL ON SCHEMA cruda, curada FROM tablero;
REVOKE ALL ON ALL TABLES IN SCHEMA cruda, curada FROM tablero;

-- Tampoco las tablas que Spark cree después en `cruda`.
ALTER DEFAULT PRIVILEGES IN SCHEMA cruda, curada REVOKE ALL ON TABLES FROM tablero;
