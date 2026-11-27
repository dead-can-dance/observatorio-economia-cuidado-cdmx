"""Configuración del backend: rutas del repositorio y conexión a PostgreSQL.

Lee el mismo .env que usa docker-compose (copiado de .env.example). Las variables de
entorno del sistema tienen prioridad sobre el archivo.

Variables propias del observatorio:

  OBSERVATORIO_FUENTE   auto (por omisión) | postgres | csv
                        auto: intenta PostgreSQL y, si no responde, reconstruye
                        `indicadores` desde data/curada/.
  OBSERVATORIO_PG_USUARIO  rol con el que se conecta el tablero (por omisión `tablero`).
"""

import os
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
FUENTES_VALIDAS = ('auto', 'postgres', 'csv')


@dataclass(frozen=True)
class Configuracion:
    fuente: str
    pg_host: str
    pg_puerto: int
    pg_base: str
    pg_usuario: str
    pg_clave: str | None
    dir_curada: Path
    dir_frontend: Path
    hay_env: bool


def leer_env(ruta):
    """Lee un archivo KEY=VALUE sencillo. Ignora comentarios y líneas vacías."""
    valores = {}
    if not ruta.exists():
        return valores
    for linea in ruta.read_text(encoding='utf-8').splitlines():
        linea = linea.strip()
        if not linea or linea.startswith('#') or '=' not in linea:
            continue
        clave, valor = linea.split('=', 1)
        valor = valor.strip()
        if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in '"\'':
            valor = valor[1:-1]
        valores[clave.strip()] = valor
    return valores


def cargar_configuracion(**sobrescribir):
    """Arma la configuración desde .env + entorno. `sobrescribir` es para las pruebas."""
    archivo_env = RAIZ / '.env'
    env = {**leer_env(archivo_env), **os.environ}

    fuente = env.get('OBSERVATORIO_FUENTE', 'auto').strip().lower()
    if fuente not in FUENTES_VALIDAS:
        raise ValueError(f'OBSERVATORIO_FUENTE={fuente!r}; usa una de {FUENTES_VALIDAS}')

    datos = dict(
        fuente=fuente,
        pg_host=env.get('POSTGRES_HOST', 'localhost'),
        pg_puerto=int(env.get('POSTGRES_PORT', '5432')),
        pg_base=env.get('POSTGRES_DB', 'cuidados'),
        pg_usuario=env.get('OBSERVATORIO_PG_USUARIO', 'tablero'),
        pg_clave=env.get('TABLERO_PASSWORD') or None,
        dir_curada=RAIZ / 'data' / 'curada',
        dir_frontend=RAIZ / 'frontend',
        hay_env=archivo_env.exists(),
    )
    datos.update(sobrescribir)
    return Configuracion(**datos)
