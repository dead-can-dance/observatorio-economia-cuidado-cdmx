"""Reglas puras (sin base de datos) del seguimiento, las horas y el pago simulado."""

from dataclasses import dataclass

AVISO_SEGURIDAD = (
    "Para tu primer encuentro: hazlo con otra persona presente o en un lugar público, "
    "y avisa a alguien de confianza."
)


def tarifa_acordada(presupuesto_min: int, presupuesto_max: int, tarifa_min: int, tarifa_max: int) -> int:
    """Punto medio del traslape entre el presupuesto y la tarifa. Si no se traslapan, usa la tarifa mínima."""
    bajo = max(presupuesto_min, tarifa_min)
    alto = min(presupuesto_max, tarifa_max)
    if bajo > alto:
        return tarifa_min
    return (bajo + alto) // 2


def estado_pago(total_registros: int, confirmados: int) -> str:
    if total_registros == 0:
        return "sin_horas"
    return "pagado_simulado" if confirmados == total_registros else "por_confirmar"


@dataclass(frozen=True)
class Paso:
    clave: str
    titulo: str
    detalle: str
    estado: str


def armar_pasos(
    *,
    estado_vinculacion: str,
    nombre_otra_persona: str,
    fecha_solicitud: str,
    hay_horas: bool,
    horas_confirmadas: bool,
    checkin_hecho: bool,
    evaluacion_hecha: bool,
) -> list[Paso]:
    """Línea de tiempo: lo cumplido va como "hecho"; el primer paso sin cumplir es el "actual"."""
    aceptada = estado_vinculacion == "aceptada"
    rechazada = estado_vinculacion == "rechazada"
    base = [
        ("solicitud", "Solicitud enviada", fecha_solicitud, True),
        (
            "respuesta",
            f"{nombre_otra_persona} rechazó" if rechazada else f"{nombre_otra_persona} aceptó",
            "La otra persona no pudo esta vez" if rechazada else "Las dos partes confirmaron",
            aceptada,
        ),
        ("encuentro", "Primer encuentro", "Acuerden día y lugar por el contacto compartido", hay_horas),
        ("horas", "Horas y pago", "Se registran las horas y quien contrata las confirma", horas_confirmadas),
        ("checkin", "Check-in de seguimiento", "A los 7 días te preguntamos cómo va", checkin_hecho),
        ("evaluacion", "Evaluación", "Valoración mutua para mejorar las coincidencias", evaluacion_hecha),
    ]
    pasos: list[Paso] = []
    actual_asignado = rechazada  # si fue rechazada, no hay paso "actual"
    for clave, titulo, detalle, cumplido in base:
        if cumplido:
            estado = "hecho"
        elif not actual_asignado:
            estado = "actual"
            actual_asignado = True
        else:
            estado = "pendiente"
        pasos.append(Paso(clave, titulo, detalle, estado))
    return pasos
