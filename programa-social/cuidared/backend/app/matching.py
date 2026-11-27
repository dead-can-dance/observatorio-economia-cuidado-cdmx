"""Reglas de compatibilidad entre una solicitud y un servicio.

Este módulo no depende de la base de datos, así que se puede probar y ajustar con facilidad.
La compatibilidad va de 0 a 100 y cada criterio explica cuántos puntos aportó.
"""

import re
from dataclasses import dataclass

PUNTOS_TIPO = 20
PUNTOS_ZONA_AGEB = 40
PUNTOS_ZONA_ALCALDIA = 25
PUNTOS_ZONA_SIN_DATO = 10
PUNTOS_PRECIO_DENTRO = 40
PUNTOS_PRECIO_PARCIAL = 25

# La clave AGEB de INEGI empieza con 2 dígitos de entidad y 3 de municipio o alcaldía.
LARGO_CLAVE_ALCALDIA = 5


@dataclass(frozen=True)
class Criterio:
    nombre: str
    estado: str  # "coincide", "parcial" o "sin_dato"
    puntos: int


@dataclass(frozen=True)
class Resultado:
    puntaje: int
    criterios: list[Criterio]


def rangos_se_traslapan(min_a: int, max_a: int, min_b: int, max_b: int) -> bool:
    return min_a <= max_b and min_b <= max_a


def evaluar_zona(ageb_solicitud: str | None, ageb_servicio: str | None) -> Criterio | None:
    """None significa que la persona cuidadora queda fuera por estar en otra alcaldía."""
    if not ageb_solicitud or not ageb_servicio:
        return Criterio("Zona", "sin_dato", PUNTOS_ZONA_SIN_DATO)
    if ageb_solicitud == ageb_servicio:
        return Criterio("Zona", "coincide", PUNTOS_ZONA_AGEB)
    if ageb_solicitud[:LARGO_CLAVE_ALCALDIA] == ageb_servicio[:LARGO_CLAVE_ALCALDIA]:
        return Criterio("Zona", "parcial", PUNTOS_ZONA_ALCALDIA)
    return None


def evaluar_precio(presupuesto_min: int, presupuesto_max: int, tarifa_min: int, tarifa_max: int) -> Criterio | None:
    """None significa que los rangos de precio no se traslapan."""
    if not rangos_se_traslapan(presupuesto_min, presupuesto_max, tarifa_min, tarifa_max):
        return None
    if tarifa_max <= presupuesto_max:
        return Criterio("Precio", "coincide", PUNTOS_PRECIO_DENTRO)
    return Criterio("Precio", "parcial", PUNTOS_PRECIO_PARCIAL)


def normalizar_franjas(texto: str | None) -> set[str]:
    """Convierte "Mañanas, tardes" en {"mañana", "tarde"} para poder comparar horarios."""
    franjas = set()
    for parte in re.split(r"[,;/]|\sy\s", (texto or "").lower()):
        franja = parte.strip()
        if franja.endswith("s") and not franja.startswith("fines"):
            franja = franja[:-1]
        if franja:
            franjas.add(franja)
    return franjas


def evaluar_horario(horario_solicitud: str | None, disponibilidad: str | None) -> Criterio | None:
    """Criterio informativo (0 puntos): None si falta alguno de los dos datos."""
    pedidas, ofrecidas = normalizar_franjas(horario_solicitud), normalizar_franjas(disponibilidad)
    if not pedidas or not ofrecidas:
        return None
    return Criterio("Horario", "coincide" if pedidas & ofrecidas else "no_coincide", 0)


def calcular_compatibilidad(
    *,
    ageb_solicitud: str | None,
    presupuesto_min: int,
    presupuesto_max: int,
    ageb_servicio: str | None,
    tarifa_min: int,
    tarifa_max: int,
) -> Resultado | None:
    """Devuelve la compatibilidad, o None si el servicio no cumple zona o precio.

    El tipo de cuidado se filtra antes, en la consulta.
    """
    zona = evaluar_zona(ageb_solicitud, ageb_servicio)
    precio = evaluar_precio(presupuesto_min, presupuesto_max, tarifa_min, tarifa_max)
    if zona is None or precio is None:
        return None
    criterios = [Criterio("Tipo de cuidado", "coincide", PUNTOS_TIPO), zona, precio]
    return Resultado(puntaje=sum(c.puntos for c in criterios), criterios=criterios)
