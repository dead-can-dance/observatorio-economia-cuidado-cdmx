from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.database import get_db
from app.deps import requiere_perfil
from app.matching import calcular_compatibilidad, evaluar_horario
from app.models import Decision, Perfil, Servicio, Solicitud, TipoDecision, Usuario, Vinculacion
from app.schemas import (
    Coincidencia,
    CriterioPublico,
    DecisionCrear,
    DecisionRespuesta,
    SolicitudCrear,
    SolicitudPublica,
)

router = APIRouter(prefix="/solicitudes", tags=["solicitudes y matching"])

_solicitante = requiere_perfil(Perfil.necesita_cuidado)


def _solicitud_propia(db: Session, solicitud_id: int, usuario: Usuario) -> Solicitud:
    solicitud = db.get(Solicitud, solicitud_id)
    if solicitud is None or solicitud.solicitante_id != usuario.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Solicitud no encontrada")
    return solicitud


@router.post("", response_model=SolicitudPublica, status_code=status.HTTP_201_CREATED)
def crear_solicitud(datos: SolicitudCrear, usuario: Usuario = Depends(_solicitante), db: Session = Depends(get_db)):
    """Quien necesita cuidado publica su solicitud con un presupuesto por hora (mínimo y máximo)."""
    solicitud = Solicitud(
        solicitante_id=usuario.id,
        tipo_cuidado=datos.tipo_cuidado,
        horario=datos.horario,
        ageb=datos.ageb or usuario.ageb,
        presupuesto_min=datos.presupuesto_min,
        presupuesto_max=datos.presupuesto_max,
    )
    db.add(solicitud)
    db.commit()
    db.refresh(solicitud)
    return solicitud


@router.get("/mias", response_model=list[SolicitudPublica])
def mis_solicitudes(usuario: Usuario = Depends(_solicitante), db: Session = Depends(get_db)):
    """Lista las solicitudes de la persona autenticada."""
    return db.scalars(select(Solicitud).where(Solicitud.solicitante_id == usuario.id).order_by(Solicitud.id)).all()


@router.get("/{solicitud_id}/coincidencias", response_model=list[Coincidencia])
def coincidencias(
    solicitud_id: int,
    limite: int = Query(default=10, ge=1, le=50),
    usuario: Usuario = Depends(_solicitante),
    db: Session = Depends(get_db),
):
    """La pila de tarjetas: perfiles compatibles que aún no se han deslizado, de mayor a menor compatibilidad."""
    solicitud = _solicitud_propia(db, solicitud_id, usuario)
    ya_decididos = select(Decision.servicio_id).where(Decision.solicitud_id == solicitud.id)
    candidatos = db.scalars(
        select(Servicio)
        .where(Servicio.tipo_cuidado == solicitud.tipo_cuidado, Servicio.id.not_in(ya_decididos))
        .options(selectinload(Servicio.persona_cuidadora))
    ).all()

    prioritaria = solicitud.ageb is not None and solicitud.ageb in settings.agebs_prioritarias_lista
    tarjetas = []
    for servicio in candidatos:
        resultado = calcular_compatibilidad(
            ageb_solicitud=solicitud.ageb,
            presupuesto_min=solicitud.presupuesto_min,
            presupuesto_max=solicitud.presupuesto_max,
            ageb_servicio=servicio.persona_cuidadora.ageb,
            tarifa_min=servicio.tarifa_min,
            tarifa_max=servicio.tarifa_max,
        )
        if resultado is None:
            continue
        criterios = [CriterioPublico(nombre=c.nombre, estado=c.estado) for c in resultado.criterios]
        horario = evaluar_horario(solicitud.horario, servicio.disponibilidad)
        if horario is not None:  # informativo: no cambia el puntaje
            criterios.insert(1, CriterioPublico(nombre=horario.nombre, estado=horario.estado))
        tarjetas.append(
            Coincidencia(
                servicio_id=servicio.id,
                nombre=servicio.persona_cuidadora.nombre,
                tipo_cuidado=servicio.tipo_cuidado,
                tarifa_min=servicio.tarifa_min,
                tarifa_max=servicio.tarifa_max,
                disponibilidad=servicio.disponibilidad,
                puntaje=resultado.puntaje,
                zona_prioritaria=prioritaria,
                criterios=criterios,
            )
        )
    tarjetas.sort(key=lambda t: (-t.puntaje, t.tarifa_min, t.servicio_id))
    return tarjetas[:limite]


@router.post("/{solicitud_id}/decisiones", response_model=DecisionRespuesta, status_code=status.HTTP_201_CREATED)
def decidir(
    solicitud_id: int,
    datos: DecisionCrear,
    usuario: Usuario = Depends(_solicitante),
    db: Session = Depends(get_db),
):
    """Deslizar a la derecha ("me_interesa") o a la izquierda ("pasar").

    "me_interesa" envía una solicitud de contacto que la persona cuidadora debe aceptar.
    """
    solicitud = _solicitud_propia(db, solicitud_id, usuario)
    servicio = db.get(Servicio, datos.servicio_id)
    if servicio is None or servicio.tipo_cuidado != solicitud.tipo_cuidado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Perfil no encontrado")
    previa = db.scalar(
        select(Decision).where(Decision.solicitud_id == solicitud.id, Decision.servicio_id == servicio.id)
    )
    if previa is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya decidiste sobre este perfil")

    db.add(Decision(solicitud_id=solicitud.id, servicio_id=servicio.id, decision=datos.decision))
    vinculacion = None
    if datos.decision == TipoDecision.me_interesa:
        vinculacion = Vinculacion(solicitud_id=solicitud.id, servicio_id=servicio.id)
        db.add(vinculacion)
    db.commit()
    return DecisionRespuesta(decision=datos.decision, vinculacion_id=vinculacion.id if vinculacion else None)
