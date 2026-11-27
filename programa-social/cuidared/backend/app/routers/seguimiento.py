from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, requiere_perfil
from app.models import (
    Evaluacion,
    EstadoVinculacion,
    HoraTrabajo,
    Perfil,
    Seguimiento,
    TipoSeguimiento,
    Usuario,
    Vinculacion,
)
from app.schemas import (
    CheckinCrear,
    CheckinRespuesta,
    EvaluacionCrear,
    HoraCrear,
    HoraPublica,
    HorasRespuesta,
    PasoSeguimiento,
    SeguimientoRespuesta,
)
from app.seguimiento import AVISO_SEGURIDAD, armar_pasos, estado_pago, tarifa_acordada

router = APIRouter(prefix="/vinculaciones", tags=["seguimiento, horas y pago"])

_cuidadora = requiere_perfil(Perfil.puede_cuidar, Perfil.organizacion)
_contratante = requiere_perfil(Perfil.necesita_cuidado)


def _participante(db: Session, vinculacion_id: int, usuario: Usuario) -> tuple[Vinculacion, bool]:
    """Devuelve la vinculación y si quien consulta es la persona cuidadora. 404 si no participa."""
    v = db.get(Vinculacion, vinculacion_id)
    if v is not None:
        es_cuidadora = v.servicio.cuidadora_id == usuario.id
        es_contratante = v.solicitud.solicitante_id == usuario.id
        if es_cuidadora or es_contratante:
            return v, es_cuidadora
    raise HTTPException(status.HTTP_404_NOT_FOUND, "Vinculación no encontrada")


def _exige_aceptada(v: Vinculacion) -> None:
    if v.estado != EstadoVinculacion.aceptada:
        raise HTTPException(status.HTTP_409_CONFLICT, "La vinculación todavía no está aceptada")


def _horas(db: Session, v: Vinculacion) -> HorasRespuesta:
    filas = db.scalars(
        select(HoraTrabajo).where(HoraTrabajo.vinculacion_id == v.id).order_by(HoraTrabajo.fecha, HoraTrabajo.id)
    ).all()
    tarifa = tarifa_acordada(
        v.solicitud.presupuesto_min, v.solicitud.presupuesto_max, v.servicio.tarifa_min, v.servicio.tarifa_max
    )
    total_horas = sum(f.horas for f in filas)
    confirmadas = sum(1 for f in filas if f.confirmada_contratante)
    return HorasRespuesta(
        registros=[
            HoraPublica(id=f.id, fecha=f.fecha, horas=f.horas, confirmada=f.confirmada_contratante) for f in filas
        ],
        total_horas=total_horas,
        tarifa_acordada=tarifa,
        total_a_pagar=total_horas * tarifa,
        quien_paga="Quien contrata",
        estado_pago=estado_pago(len(filas), confirmadas),
    )


@router.get("/{vinculacion_id}/seguimiento", response_model=SeguimientoRespuesta)
def seguimiento(vinculacion_id: int, usuario: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """Línea de tiempo de la vinculación, calculada con lo que ya ocurrió."""
    v, es_cuidadora = _participante(db, vinculacion_id, usuario)
    otra = v.solicitud.solicitante if es_cuidadora else v.servicio.persona_cuidadora
    horas = _horas(db, v)
    checkin = db.scalar(select(func.count()).select_from(Seguimiento).where(Seguimiento.vinculacion_id == v.id))
    evaluacion = db.scalar(
        select(func.count())
        .select_from(Evaluacion)
        .where(Evaluacion.vinculacion_id == v.id, Evaluacion.usuario_id == usuario.id)
    )
    pasos = armar_pasos(
        estado_vinculacion=v.estado.value,
        nombre_otra_persona=otra.nombre,
        fecha_solicitud=f"Enviada el {v.creado_en:%d/%m/%Y}",
        hay_horas=bool(horas.registros),
        horas_confirmadas=horas.estado_pago == "pagado_simulado",
        checkin_hecho=bool(checkin),
        evaluacion_hecha=bool(evaluacion),
    )
    return SeguimientoRespuesta(
        otra_persona=otra.nombre,
        estado_vinculacion=v.estado,
        pasos=[PasoSeguimiento(clave=p.clave, titulo=p.titulo, detalle=p.detalle, estado=p.estado) for p in pasos],
        aviso_seguridad=AVISO_SEGURIDAD,
    )


@router.post("/{vinculacion_id}/checkin", response_model=CheckinRespuesta, status_code=status.HTTP_201_CREATED)
def checkin(
    vinculacion_id: int,
    datos: CheckinCrear,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """"Todo va bien" o "Reportar un problema". Cualquiera de las dos partes puede hacerlo."""
    v, _ = _participante(db, vinculacion_id, usuario)
    _exige_aceptada(v)
    tipo = TipoSeguimiento.todo_bien if datos.todo_bien else TipoSeguimiento.problema
    db.add(Seguimiento(vinculacion_id=v.id, usuario_id=usuario.id, tipo=tipo, nota=datos.nota))
    db.commit()
    return CheckinRespuesta(tipo=tipo)


@router.post("/{vinculacion_id}/evaluacion", status_code=status.HTTP_201_CREATED)
def evaluar(
    vinculacion_id: int,
    datos: EvaluacionCrear,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Valoración mutua (1 a 5). Cada persona evalúa una sola vez."""
    v, _ = _participante(db, vinculacion_id, usuario)
    _exige_aceptada(v)
    previa = db.scalar(
        select(Evaluacion).where(Evaluacion.vinculacion_id == v.id, Evaluacion.usuario_id == usuario.id)
    )
    if previa is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya enviaste tu evaluación")
    db.add(
        Evaluacion(
            vinculacion_id=v.id, usuario_id=usuario.id, puntuacion=datos.puntuacion, comentario=datos.comentario
        )
    )
    db.commit()
    return {"puntuacion": datos.puntuacion}


@router.get("/{vinculacion_id}/horas", response_model=HorasRespuesta)
def ver_horas(vinculacion_id: int, usuario: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    v, _ = _participante(db, vinculacion_id, usuario)
    return _horas(db, v)


@router.post("/{vinculacion_id}/horas", response_model=HorasRespuesta, status_code=status.HTTP_201_CREATED)
def registrar_horas(
    vinculacion_id: int,
    datos: HoraCrear,
    usuario: Usuario = Depends(_cuidadora),
    db: Session = Depends(get_db),
):
    """La persona cuidadora registra horas trabajadas."""
    v, es_cuidadora = _participante(db, vinculacion_id, usuario)
    if not es_cuidadora:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vinculación no encontrada")
    _exige_aceptada(v)
    db.add(HoraTrabajo(vinculacion_id=v.id, fecha=datos.fecha, horas=datos.horas))
    db.commit()
    return _horas(db, v)


@router.post("/{vinculacion_id}/horas/confirmar", response_model=HorasRespuesta)
def confirmar_horas(vinculacion_id: int, usuario: Usuario = Depends(_contratante), db: Session = Depends(get_db)):
    """Quien contrata confirma las horas ya realizadas. Con eso el pago (simulado) queda listo."""
    v, es_cuidadora = _participante(db, vinculacion_id, usuario)
    if es_cuidadora:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vinculación no encontrada")
    _exige_aceptada(v)
    # Solo se confirman las horas que ya ocurrieron; las programadas quedan pendientes.
    pendientes = db.scalars(
        select(HoraTrabajo).where(
            HoraTrabajo.vinculacion_id == v.id,
            HoraTrabajo.confirmada_contratante.is_(False),
            HoraTrabajo.fecha <= date.today(),
        )
    ).all()
    if not pendientes:
        raise HTTPException(status.HTTP_409_CONFLICT, "No hay horas por confirmar")
    for fila in pendientes:
        fila.confirmada_contratante = True
    db.commit()
    return _horas(db, v)
