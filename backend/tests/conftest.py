import pytest
from fastapi.testclient import TestClient

from observatorio.configuracion import cargar_configuracion
from observatorio.main import crear_app
from observatorio.repositorio import cargar_repositorio


@pytest.fixture(scope='session')
def cfg():
    # Las pruebas no dependen de que haya una base corriendo: leen data/curada/.
    return cargar_configuracion(fuente='csv')


@pytest.fixture(scope='session')
def repo(cfg):
    return cargar_repositorio(cfg)


@pytest.fixture(scope='session')
def cliente(cfg):
    with TestClient(crear_app(cfg)) as c:
        yield c
