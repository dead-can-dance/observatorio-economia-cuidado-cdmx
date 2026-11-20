from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import Perfil


class UsuarioCrear(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    nombre: str = Field(min_length=1, max_length=120)
    perfil: Perfil
    ageb: str | None = Field(default=None, max_length=20)
    acepto_aviso_privacidad: bool


class LoginEntrada(BaseModel):
    email: EmailStr
    password: str


class UsuarioPublico(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    nombre: str
    perfil: Perfil
    ageb: str | None = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Servicios, solicitudes y matching (Paso 3) ----------
from pydantic import model_validator  # noqa: E402

from app.models import EstadoSolicitud, EstadoVinculacion, TipoCuidado, TipoDecision  # noqa: E402


class ServicioCrear(BaseModel):
    tipo_cuidado: TipoCuidado
    tarifa_min: int = Field(ge=0, le=100000, description="MXN por hora")
    tarifa_max: int = Field(ge=0, le=100000, description="MXN por hora")
    disponibilidad: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def _rango_valido(self):
        if self.tarifa_max < self.tarifa_min:
            raise ValueError("La tarifa máxima no puede ser menor que la mínima")
        return self


class ServicioPublico(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo_cuidado: TipoCuidado
    tarifa_min: int
    tarifa_max: int
    disponibilidad: str | None = None


class SolicitudCrear(BaseModel):
    tipo_cuidado: TipoCuidado
    horario: str | None = Field(default=None, max_length=200)
    ageb: str | None = Field(default=None, max_length=20, description="Si se omite, se usa la de tu cuenta")
    presupuesto_min: int = Field(ge=0, le=100000, description="MXN por hora")
    presupuesto_max: int = Field(ge=0, le=100000, description="MXN por hora")

    @model_validator(mode="after")
    def _rango_valido(self):
        if self.presupuesto_max < self.presupuesto_min:
            raise ValueError("El presupuesto máximo no puede ser menor que el mínimo")
        return self


class SolicitudPublica(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo_cuidado: TipoCuidado
    horario: str | None = None
    ageb: str | None = None
    presupuesto_min: int
    presupuesto_max: int
    estado: EstadoSolicitud


class CriterioPublico(BaseModel):
    nombre: str
    estado: str


class Coincidencia(BaseModel):
    servicio_id: int
    nombre: str
    tipo_cuidado: TipoCuidado
    tarifa_min: int
    tarifa_max: int
    disponibilidad: str | None = None
    puntaje: int
    zona_prioritaria: bool
    criterios: list[CriterioPublico]


class DecisionCrear(BaseModel):
    servicio_id: int
    decision: TipoDecision


class DecisionRespuesta(BaseModel):
    decision: TipoDecision
    vinculacion_id: int | None = None


class VinculacionPublica(BaseModel):
    id: int
    estado: EstadoVinculacion
    tipo_cuidado: TipoCuidado
    horario: str | None = None
    presupuesto_min: int
    presupuesto_max: int
    tarifa_min: int
    tarifa_max: int
    otra_persona: str
    contacto: str | None = Field(default=None, description="Solo se muestra cuando la vinculación está aceptada")


class RespuestaVinculacion(BaseModel):
    aceptar: bool


# ---------- Seguimiento, horas y pago simulado (Paso 4) ----------
from datetime import date  # noqa: E402

from app.models import TipoSeguimiento  # noqa: E402


class PasoSeguimiento(BaseModel):
    clave: str
    titulo: str
    detalle: str
    estado: str  # "hecho", "actual" o "pendiente"


class SeguimientoRespuesta(BaseModel):
    otra_persona: str
    estado_vinculacion: EstadoVinculacion
    pasos: list[PasoSeguimiento]
    aviso_seguridad: str


class CheckinCrear(BaseModel):
    todo_bien: bool
    nota: str | None = Field(default=None, max_length=500)


class CheckinRespuesta(BaseModel):
    tipo: TipoSeguimiento


class EvaluacionCrear(BaseModel):
    puntuacion: int = Field(ge=1, le=5)
    comentario: str | None = Field(default=None, max_length=500)


class HoraCrear(BaseModel):
    fecha: date
    horas: int = Field(ge=1, le=24)


class HoraPublica(BaseModel):
    id: int
    fecha: date
    horas: int
    confirmada: bool


class HorasRespuesta(BaseModel):
    registros: list[HoraPublica]
    total_horas: int
    tarifa_acordada: int
    total_a_pagar: int
    quien_paga: str
    estado_pago: str  # "sin_horas", "por_confirmar" o "pagado_simulado"
