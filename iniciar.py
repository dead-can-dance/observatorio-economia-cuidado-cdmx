#!/usr/bin/env python3
"""Levanta el Observatorio de la Economía del Cuidado en esta computadora.

    python iniciar.py                    # http://127.0.0.1:8000 y abre el navegador
    python iniciar.py --puerto 8080      # otro puerto
    python iniciar.py --fuente csv       # no intentar PostgreSQL
    python iniciar.py --red              # visible para otros equipos de la red local
    python iniciar.py --recarga          # reinicia solo al editar el backend (desarrollo)
    python iniciar.py --pruebas          # corre las pruebas (backend y app de Streamlit) y termina
    python iniciar.py --streamlit        # la versión en Streamlit: http://127.0.0.1:8501

La primera vez crea un entorno virtual e instala backend/requirements.txt (tarda unos
minutos y necesita internet). Las siguientes veces arranca en segundos y sin internet.

Fuente de datos: si existe .env con TABLERO_PASSWORD y PostgreSQL responde (docker
compose up), lee el esquema `indicadores`. Si no, reconstruye esas mismas tablas desde
data/curada/ con las reglas del ETL. La página indica cuál está usando.
"""

import argparse
import hashlib
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import venv
import webbrowser
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
BACKEND = RAIZ / 'backend'
REQUISITOS = BACKEND / 'requirements.txt'
REQUISITOS_DEV = BACKEND / 'requirements-dev.txt'
TABLERO = RAIZ / 'tablero'
REQUISITOS_TABLERO = TABLERO / 'requirements.txt'


def dentro_de_onedrive(ruta):
    """OneDrive sincronizaría miles de archivos del entorno virtual a la nube."""
    for variable in ('OneDrive', 'OneDriveConsumer', 'OneDriveCommercial'):
        carpeta = os.environ.get(variable)
        if carpeta and str(ruta).lower().startswith(str(Path(carpeta)).lower()):
            return True
    return False


def ruta_entorno():
    if os.environ.get('OBSERVATORIO_VENV'):
        return Path(os.environ['OBSERVATORIO_VENV'])
    if dentro_de_onedrive(RAIZ) and os.environ.get('LOCALAPPDATA'):
        return Path(os.environ['LOCALAPPDATA']) / 'observatorio-cuidado' / '.venv'
    return RAIZ / '.venv'


def python_de(entorno):
    return entorno / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')


def preparar_entorno(entorno, *requisitos):
    python = python_de(entorno)
    if not python.exists():
        print(f'Creando el entorno virtual en {entorno} (solo la primera vez)...', flush=True)
        try:
            venv.create(entorno, with_pip=True)
        except Exception as e:  # p. ej. falta python3-venv en Debian/Ubuntu
            sys.exit(f'No se pudo crear el entorno virtual: {e}\n'
                     'En Debian/Ubuntu instala python3-venv (sudo apt install python3-venv).')
    # Un sello por archivo de requisitos (backend-requirements, tablero-requirements...):
    # se reinstala solo si su contenido cambió.
    for archivo in requisitos or (REQUISITOS,):
        nombre = f'{archivo.parent.name}-{archivo.stem}'
        sello = entorno / f'.observatorio-{nombre}'
        huella = hashlib.sha256(archivo.read_bytes()).hexdigest()
        if not sello.exists() or sello.read_text().strip() != huella:
            print(f'Instalando dependencias ({nombre}, solo cuando cambian)...', flush=True)
            r = subprocess.run([str(python), '-m', 'pip', 'install', '--disable-pip-version-check',
                                '-q', '-r', str(archivo)])
            if r.returncode != 0:
                sys.exit('Falló la instalación de dependencias. Revisa tu conexión a internet y '
                         'vuelve a intentarlo.')
            sello.write_text(huella)
    return python


def puerto_libre(host, puerto):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, puerto))
            return True
        except OSError:
            return False


def abrir_navegador_cuando_responda(url, segundos=60):
    def esperar():
        limite = time.time() + segundos
        while time.time() < limite:
            try:
                with urllib.request.urlopen(f'{url}/api/estado', timeout=2):
                    webbrowser.open(url)
                    return
            except Exception:
                time.sleep(0.5)
    threading.Thread(target=esperar, daemon=True).start()


def main():
    if sys.version_info < (3, 10):
        sys.exit('Se necesita Python 3.10 o más reciente.')

    p = argparse.ArgumentParser(description='Levanta el Observatorio de la Economía del Cuidado.')
    p.add_argument('--puerto', type=int, default=None,
                   help='Por omisión: 8000 (página web) u 8501 (Streamlit).')
    p.add_argument('--fuente', choices=['auto', 'postgres', 'csv'], default=None,
                   help='De dónde leer los datos (por omisión: auto).')
    p.add_argument('--red', action='store_true',
                   help='Escucha en todas las interfaces: otros equipos de tu red podrán abrirlo.')
    p.add_argument('--sin-navegador', action='store_true', help='No abrir el navegador.')
    p.add_argument('--recarga', action='store_true', help='Recarga automática del backend.')
    p.add_argument('--pruebas', action='store_true', help='Corre las pruebas y termina.')
    p.add_argument('--streamlit', action='store_true',
                   help='Levanta la versión en Streamlit (tablero/app.py) en lugar de la página web.')
    args = p.parse_args()

    if args.pruebas:
        python = preparar_entorno(ruta_entorno(), REQUISITOS_DEV, REQUISITOS_TABLERO)
        entorno = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}
        print('Pruebas del backend y la página web:', flush=True)
        backend = subprocess.call([str(python), '-m', 'pytest', '-q'], cwd=str(BACKEND), env=entorno)
        print('\nPruebas de la app de Streamlit:', flush=True)
        tablero = subprocess.call([str(python), '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
                                   str(TABLERO / 'tests')], cwd=str(RAIZ), env=entorno)
        return backend or tablero

    if args.puerto is None:
        args.puerto = 8501 if args.streamlit else 8000
    host = '0.0.0.0' if args.red else '127.0.0.1'
    if not puerto_libre(host, args.puerto):
        sys.exit(f'El puerto {args.puerto} está ocupado. Prueba con: python iniciar.py --puerto 8080')

    if args.streamlit:
        return levantar_streamlit(args, host)

    python = preparar_entorno(ruta_entorno())

    entorno = dict(os.environ)
    # Acentos bien escritos aunque la salida se redirija a un archivo en Windows.
    entorno.setdefault('PYTHONIOENCODING', 'utf-8')
    if args.fuente:
        entorno['OBSERVATORIO_FUENTE'] = args.fuente
    comando = [str(python), '-m', 'uvicorn', 'observatorio.main:app', '--app-dir', str(BACKEND),
               '--host', host, '--port', str(args.puerto), '--log-level', 'warning']
    if args.recarga:
        comando += ['--reload', '--reload-dir', str(BACKEND)]

    url = f'http://127.0.0.1:{args.puerto}'
    print(f'\nObservatorio en {url}   (Ctrl+C para detener)', flush=True)
    if args.red:
        print('Modo red: otros equipos de tu red local pueden abrirlo con la IP de esta computadora.',
              flush=True)
    if not args.sin_navegador:
        abrir_navegador_cuando_responda(url)

    proceso = subprocess.Popen(comando, cwd=str(RAIZ), env=entorno)
    try:
        return proceso.wait()
    except KeyboardInterrupt:
        try:
            proceso.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proceso.terminate()
        print('\nObservatorio detenido.')
        return 0


def levantar_streamlit(args, host):
    python = preparar_entorno(ruta_entorno(), REQUISITOS_TABLERO)
    entorno = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}
    if args.fuente:
        entorno['OBSERVATORIO_FUENTE'] = args.fuente
    comando = [str(python), '-m', 'streamlit', 'run', str(TABLERO / 'app.py'),
               '--server.address', host, '--server.port', str(args.puerto),
               '--server.headless', 'true' if args.sin_navegador else 'false']
    if args.recarga:
        comando += ['--server.runOnSave', 'true']
    print(f'\nObservatorio (Streamlit) en http://127.0.0.1:{args.puerto}   (Ctrl+C para detener)', flush=True)
    proceso = subprocess.Popen(comando, cwd=str(RAIZ), env=entorno)
    try:
        return proceso.wait()
    except KeyboardInterrupt:
        try:
            proceso.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proceso.terminate()
        print('\nObservatorio detenido.')
        return 0


if __name__ == '__main__':
    sys.exit(main())
