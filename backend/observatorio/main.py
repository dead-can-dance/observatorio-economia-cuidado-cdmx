"""Aplicación FastAPI: la API en /api y el frontend en /.

Se levanta con `python iniciar.py` desde la raíz del repositorio, o a mano:

    uvicorn observatorio.main:app --app-dir backend
"""

import logging
import mimetypes
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from . import __version__
from .api import router
from .configuracion import cargar_configuracion
from .repositorio import cargar_repositorio

# En Windows, mimetypes lee el registro y a veces asocia .js con text/plain; el
# navegador se niega entonces a ejecutar los módulos del frontend. Se fija a mano.
mimetypes.add_type('text/javascript', '.js')
mimetypes.add_type('text/css', '.css')
mimetypes.add_type('image/svg+xml', '.svg')

log = logging.getLogger('observatorio')


def _anunciar(repo):
    controles = repo.controles
    buenos = sum(c['ok'] for c in controles)
    lineas = [
        'Observatorio de la Economía del Cuidado',
        f'  Fuente de datos : {repo.detalle}',
    ]
    if repo.aviso:
        lineas.append(f'  Aviso           : {repo.aviso}')
    lineas.append(f'  Cifras de control: {buenos}/{len(controles)} cuadran')
    for c in controles:
        if not c['ok']:
            lineas.append(f'    [MAL] {c["etiqueta"]}: esperado {c["esperado"]}, '
                          f'obtenido {c["obtenido"]}')
    print('\n'.join(lineas), flush=True)


def crear_app(cfg=None):
    cfg = cfg or cargar_configuracion()

    @asynccontextmanager
    async def ciclo_de_vida(app):
        app.state.repositorio = cargar_repositorio(cfg)
        _anunciar(app.state.repositorio)
        yield

    app = FastAPI(
        title='Observatorio de la Economía del Cuidado — API',
        description='Lee el esquema `indicadores` (PostgreSQL o su réplica desde '
                    '`data/curada/`). Toda cifra viaja con su fuente y su nivel geográfico.',
        version=__version__,
        lifespan=ciclo_de_vida,
        docs_url='/api/docs',
        redoc_url=None,
        openapi_url='/api/openapi.json',
    )
    app.add_middleware(GZipMiddleware, minimum_size=1024)
    app.include_router(router)
    if cfg.dir_frontend.is_dir():
        app.mount('/', StaticFiles(directory=cfg.dir_frontend, html=True), name='frontend')
    else:  # pragma: no cover
        log.warning('No existe %s: solo se sirve la API.', cfg.dir_frontend)
    return app


app = crear_app()
