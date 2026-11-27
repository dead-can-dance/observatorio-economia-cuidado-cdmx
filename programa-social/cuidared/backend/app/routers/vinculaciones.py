from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import requiere_perfil
from app.models import EstadoVinculacion, Perfil, Servicio, Solicitud, Usuario, Vinculacion
from app.schemas import RespuestaVinculacion, VinculacionPublica

router = APIRouter(prefix="/vinculaciones", tags=["vinculaciones"])

_cuidadora = requiere_perfil(Perfil.puede_cuidar, Perfil.organizacion)
_solicitante = requiere_perfil(Perfil.necesita_cuidado)


def _publica(v: Vinculacion, *, vista_cuidadora: bool) -> VinculacionPublica:
    """Arma la respuesta. El contacto de la otra persona solo aparece si ya se aceptó."""
    otra = v.solicitud.solicitante if vista_cuidadora else v.servicio.persona_cuidadora
    return VinculacionPublica(
        id=v.id,
        estado=v.estado,
        tipo_cuidado=v.servicio.tipo_cuidado,
        horario=v.solicitud.horario,
        presupuesto_min=v.solicitud.presupuesto_min,
        presupuesto_max=v.solicitud.presupuesto_max,
        tarifa_min=v.servicio.tarifa_min,
        tarifa_max=v.servicio.tarifa_max,
        otra_persona=otra.nombre,
        contacto=otra.email if v.estado == EstadoVinculacion.aceptada else None,
    )


@router.get("/recibidas", response_model=list[VinculacionPublica])
def recibidas(usuario: Usuario = Depends(_cuidadora), db: Session = Depends(get_db)):
    """Solicitudes de contacto que recibió la persona cuidadora."""
    filas = db.scalars(
        select(Vinculacion)
        .join(Servicio, Vinculacion.servicio_id == Servicio.id)
        .where(Servicio.cuidadora_id == usuario.id)
        .order_by(Vinculacion.id.desc())
    ).all()
    return [_publica(v, vista_cuidadora=True) for v in filas]


@router.get("/mias", response_model=list[VinculacionPublica])
def mias(usuario: Usuario = Depends(_solicitante), db: Session = Depends(get_db)):
    """Solicitudes de contacto que envió quien contrata."""
    filas = db.scalars(
        select(Vinculacion)
        .join(Solicitud, Vinculacion.solicitud_id == Solicitud.id)
        .where(Solicitud.solicitante_id == usuario.id)
        .order_by(Vinculacion.id.desc())
    ).all()
    return [_publica(v, vista_cuidadora=False) for v in filas]


@router.post("/{vinculacion_id}/responder", response_model=VinculacionPublica)
def responder(
    vinculacion_id: int,
    datos: RespuestaVinculacion,
    usuario: Usuario = Depends(_cuidadora),
    db: Session = Depends(get_db),
):
    """La persona cuidadora acepta o rechaza. Al aceptar, ambas partes ven el contacto de la otra."""
    vinculacion = db.get(Vinculacion, vinculacion_id)
    if vinculacion is None or vinculacion.servicio.cuidadora_id != usuario.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vinculación no encontrada")
    if vinculacion.estado != EstadoVinculacion.pendiente:
        raise HTTPException(status.HTTP_409_CONFLICT, "Esta vinculación ya fue respondida")
    vinculacion.estado = EstadoVinculacion.aceptada if datos.aceptar else EstadoVinculacion.rechazada
    vinculacion.respondida_en = datetime.now(timezone.utc)
    db.commit()
    return _publica(vinculacion, vista_cuidadora=True)
