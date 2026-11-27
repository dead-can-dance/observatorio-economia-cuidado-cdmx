from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import requiere_perfil
from app.models import Perfil, Servicio, Usuario
from app.schemas import ServicioCrear, ServicioPublico

router = APIRouter(prefix="/servicios", tags=["servicios"])

_cuidadora = requiere_perfil(Perfil.puede_cuidar, Perfil.organizacion)


@router.post("", response_model=ServicioPublico, status_code=status.HTTP_201_CREATED)
def crear_servicio(datos: ServicioCrear, usuario: Usuario = Depends(_cuidadora), db: Session = Depends(get_db)):
    """La persona cuidadora publica un servicio con su rango de tarifa por hora."""
    servicio = Servicio(
        cuidadora_id=usuario.id,
        tipo_cuidado=datos.tipo_cuidado,
        tarifa_min=datos.tarifa_min,
        tarifa_max=datos.tarifa_max,
        disponibilidad=datos.disponibilidad,
    )
    db.add(servicio)
    db.commit()
    db.refresh(servicio)
    return servicio


@router.get("/mios", response_model=list[ServicioPublico])
def mis_servicios(usuario: Usuario = Depends(_cuidadora), db: Session = Depends(get_db)):
    """Lista los servicios que publicó la persona autenticada."""
    return db.scalars(select(Servicio).where(Servicio.cuidadora_id == usuario.id).order_by(Servicio.id)).all()
