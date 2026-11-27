import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Perfil, Servicio, TipoCuidado, Usuario


def _usuario():
    return Usuario(
        email="cuidadora@ejemplo.com",
        password_hash="x",
        nombre="Cuidadora",
        perfil=Perfil.puede_cuidar,
        acepto_aviso_privacidad=True,
    )


def test_servicio_con_rango_de_tarifa_valido(session_factory):
    with session_factory() as db:
        u = _usuario()
        u.servicios.append(Servicio(tipo_cuidado=TipoCuidado.comidas, tarifa_min=80, tarifa_max=120))
        db.add(u)
        db.commit()
        assert db.get(Usuario, u.id).servicios[0].tarifa_max == 120


def test_servicio_rechaza_tarifa_maxima_menor_que_la_minima(session_factory):
    with session_factory() as db:
        u = _usuario()
        u.servicios.append(Servicio(tipo_cuidado=TipoCuidado.comidas, tarifa_min=150, tarifa_max=100))
        db.add(u)
        with pytest.raises(IntegrityError):
            db.commit()
