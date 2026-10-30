"""Modelo financiero de la Red de Cuidado a Domicilio «Manos que Cuidan» (escenario simulado).

Evalúa si conviene invertir en el programa de vinculación que deriva de los hallazgos del
observatorio: cuidado a domicilio por horas, con cuidadoras capacitadas y verificadas de
las propias colonias, en las 25 AGEB de Iztapalapa de alta carga y sin respaldo a 1 km.
El operador es el Centro Comunitario «Manos que Cuidan» (institución simulada, tomada del
incidente crítico del propio PP). La vinculación entre familias y cuidadoras la hace la
plataforma de matching del equipo; aquí solo entran sus costos.

Es Python puro a propósito: el notebook 03, el anexo de Excel y la página «Decisión» de
Streamlit usan exactamente estas reglas. El Excel replica las fórmulas celda por celda y
el notebook verifica que den lo mismo.

Convenciones:
  * Pesos constantes de 2026 (sin inflación) y tasa de descuento REAL.
  * Flujos mensuales; mes 0 = inversión inicial; horizonte de 60 meses (vida útil de la
    plataforma y del equipo), sin valor de rescate (conservador).
  * Decisión por etapas: en el mes de revisión (12) el programa se cierra si atiende a
    menos de la mitad de las familias de su punto de equilibrio. El VAN «con revisión»
    incluye ese cierre y su costo; el VAN «sin revisión» supone que se opera pase lo que pase.
  * Sin ISR: el operador es una OSC donataria autorizada y el servicio es su objeto social.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace

SEMANAS_POR_MES = 52 / 12

# --- Insumos que vienen de los datos (notebook 03, sección 5) ---------------------------
# Hogares con al menos una persona que necesita cuidado directo en las 25 AGEB de la zona:
# (población de 0 a 5 + discapacidad para el autocuidado, Censo 2020) ÷ 1.206 personas con
# necesidad por hogar con necesidad (ENUT 2024, nacional; CDMX: 1.224 con solo 103 hogares).
HOGARES_ZONA = 9415


@dataclass(frozen=True)
class Supuestos:
    """Todo lo que mueve el resultado. Cada valor lleva su fuente en SUPUESTOS_FUENTES."""

    # Variables que cambian por escenario
    adopcion: float                 # fracción de HOGARES_ZONA que son clientes en estado estable
    horas_semana_familia: float     # horas contratadas por familia a la semana
    subsidio_hora: float            # pesos por hora que paga el Sistema Público de Cuidados
    meses_estado_estable: int       # mes en que se alcanza la adopción objetivo

    # Variables comunes
    hogares_zona: int = HOGARES_ZONA
    copago_hora: float = 60.0               # lo que paga la familia por hora
    pago_cuidadora_hora: float = 55.0       # pago bruto a la cuidadora por hora
    prestaciones: float = 0.30              # IMSS, aguinaldo, vacaciones: % sobre el pago
    insumos_hora: float = 3.0               # seguro por hora de servicio, guantes, traslados
    horas_semana_cuidadora: float = 30.0    # jornada de una cuidadora de la red
    rotacion_mensual: float = 0.03          # cuidadoras que se van cada mes
    capacitacion_cuidadora: float = 3500.0  # curso de 40 h + verificación de antecedentes
    familias_por_trabajadora_social: int = 80
    familias_piloto: int = 15
    cuidadoras_piloto: int = 6
    meses_piloto: int = 6
    # Costos fijos mensuales (con 35 % de carga social en el personal)
    coordinacion: float = 29700.0           # coordinadora del programa
    trabajadora_social: float = 24300.0     # verificación, seguimiento e incidentes
    plataforma: float = 6000.0              # hospedaje, mensajería y mantenimiento
    seguro_fijo: float = 3000.0             # póliza de responsabilidad civil
    difusion: float = 4000.0                # trabajo comunitario y materiales
    administracion: float = 6000.0          # contabilidad y facturación (honorarios)
    # Inversión inicial (mes 0)
    inv_plataforma: float = 120000.0        # adaptar y endurecer el prototipo del equipo
    inv_proteccion_datos: float = 35000.0   # aviso de privacidad, protocolo LFPDPPP, asesoría
    inv_equipamiento: float = 30000.0       # kits, botiquines, uniformes, teléfonos
    inv_lanzamiento: float = 20000.0        # presentación en las colonias
    # Evaluación
    tasa_descuento_anual: float = 0.10      # tasa social de descuento, real (SHCP)
    horizonte_meses: int = 60
    colchon: float = 0.10                   # imprevistos sobre inversión + operación
    # Decisión por etapas
    mes_revision: int = 12
    umbral_continuar: float = 0.5           # fracción de las familias del punto de equilibrio
    meses_costo_cierre: float = 2.0         # liquidaciones y cierre, en meses de costos fijos

    @property
    def tarifa_hora(self):
        return self.copago_hora + self.subsidio_hora

    @property
    def costo_variable_hora(self):
        return self.pago_cuidadora_hora * (1 + self.prestaciones) + self.insumos_hora

    @property
    def margen_hora(self):
        return self.tarifa_hora - self.costo_variable_hora

    @property
    def inversion_inicial(self):
        capacitacion_piloto = self.cuidadoras_piloto * self.capacitacion_cuidadora
        return (self.inv_plataforma + self.inv_proteccion_datos + self.inv_equipamiento
                + self.inv_lanzamiento + capacitacion_piloto)

    @property
    def familias_objetivo(self):
        return self.hogares_zona * self.adopcion

    @property
    def tasa_mensual(self):
        return (1 + self.tasa_descuento_anual) ** (1 / 12) - 1


ESCENARIOS = {
    'Pesimista': Supuestos(adopcion=0.010, horas_semana_familia=6, subsidio_hora=20,
                           meses_estado_estable=24),
    'Realista': Supuestos(adopcion=0.020, horas_semana_familia=8, subsidio_hora=40,
                          meses_estado_estable=18),
    'Optimista': Supuestos(adopcion=0.032, horas_semana_familia=10, subsidio_hora=40,
                           meses_estado_estable=12),
}
# Probabilidades subjetivas, cargadas hacia abajo: no hay historia del servicio, la tasa
# de búsqueda activa de servicios es baja (3.2 %, ENASIC) y el subsidio depende de un
# convenio que todavía no existe.
PROBABILIDADES = {'Pesimista': 0.30, 'Realista': 0.50, 'Optimista': 0.20}

# Lo que cambia entre escenarios, para tablas y para el simulador.
VARIABLES_ESCENARIO = [
    ('adopcion', 'Adopción en estado estable', '% de hogares con necesidad de cuidado'),
    ('horas_semana_familia', 'Horas contratadas por familia', 'horas por semana'),
    ('subsidio_hora', 'Subsidio público por hora', 'pesos por hora'),
    ('meses_estado_estable', 'Meses para llegar al estado estable', 'meses'),
]

SUPUESTOS_FUENTES = {
    'hogares_zona': 'Censo 2020 (25 AGEB de Iztapalapa sin respaldo) y ENUT 2024 (1.206 personas '
                    'con necesidad de cuidado por hogar con necesidad).',
    'adopcion': 'Anclada en la ENASIC 2022 (nacional): 3.2 % de las cuidadoras buscó un servicio '
                'formal en el último año; es el techo del escenario optimista.',
    'horas_semana_familia': 'ENUT 2024: las mujeres de la CDMX que cuidan dedican 12.2 h a la '
                            'semana; el servicio cubre la mitad o algo más.',
    'subsidio_hora': 'Supuesto de convenio con el Sistema Público de Cuidados de la CDMX (ley '
                     'promulgada el 2 de julio de 2026). Sin convenio no hay subsidio.',
    'copago_hora': 'Tarifa social, por debajo del mercado (≈ $142/h de una cuidadora de tiempo '
                   'completo a $25,000 al mes en la CDMX).',
    'pago_cuidadora_hora': '1.28 veces el salario mínimo profesional de las trabajadoras del hogar '
                           '2026 ($342.47 diarios, $42.81 por hora en jornada de 8 h).',
    'prestaciones': 'Seguridad social obligatoria del trabajo del hogar, aguinaldo y vacaciones.',
    'tasa_descuento_anual': 'Tasa social de descuento de 10 % real (SHCP, Unidad de Inversiones, 2022).',
    'familias_piloto': 'Incidente crítico del PP: piloto de 2 colonias, 15 familias y 6 cuidadoras.',
}


@dataclass
class Resultado:
    escenario: str
    supuestos: Supuestos
    meses: list = field(default_factory=list)  # un dict por mes, del 0 al horizonte
    van: float = 0.0
    tir_anual: float | None = None
    payback_meses: int | None = None
    payback_descontado_meses: int | None = None
    punto_equilibrio_horas_mes: float | None = None
    punto_equilibrio_familias: float | None = None
    utilidad_neta: float = 0.0
    capital_inversion: float = 0.0
    capital_operacion: float = 0.0
    capital_colchon: float = 0.0
    capital_total: float = 0.0
    deficit_maximo: float = 0.0
    horas_mes_estable: float = 0.0
    familias_estable: float = 0.0
    cuidadoras_estable: int = 0
    se_cierra_en_revision: bool = False
    van_con_revision: float = 0.0
    utilidad_neta_con_revision: float = 0.0


def familias_en_mes(s: Supuestos, mes: int) -> float:
    """Piloto fijo los primeros meses y después rampa lineal hasta la adopción objetivo."""
    if mes <= 0:
        return 0.0
    if mes <= s.meses_piloto:
        return float(s.familias_piloto)
    objetivo = max(s.familias_objetivo, s.familias_piloto)
    if mes >= s.meses_estado_estable:
        return objetivo
    avance = (mes - s.meses_piloto) / (s.meses_estado_estable - s.meses_piloto)
    return s.familias_piloto + (objetivo - s.familias_piloto) * avance


def cuidadoras_necesarias(s: Supuestos, horas_semana: float) -> int:
    return max(s.cuidadoras_piloto, math.ceil(horas_semana / s.horas_semana_cuidadora - 1e-9))


def trabajadoras_sociales(s: Supuestos, familias: float) -> int:
    return max(1, math.ceil(familias / s.familias_por_trabajadora_social - 1e-9))


def fijos_sin_personal_variable(s: Supuestos) -> float:
    return s.coordinacion + s.plataforma + s.seguro_fijo + s.difusion + s.administracion


def van(flujos, tasa):
    return sum(f / (1 + tasa) ** t for t, f in enumerate(flujos))


def tir(flujos, bajo=-0.99, alto=1.0, iteraciones=200):
    """TIR mensual por bisección. None si no hay cambio de signo en el intervalo."""
    def f(r):
        return van(flujos, r)
    fb, fa = f(bajo), f(alto)
    if fb * fa > 0:
        return None
    for _ in range(iteraciones):
        medio = (bajo + alto) / 2
        fm = f(medio)
        if abs(fm) < 1e-7:
            return medio
        if fb * fm < 0:
            alto, fa = medio, fm
        else:
            bajo, fb = medio, fm
    return (bajo + alto) / 2


def _payback(acumulado):
    for mes, valor in enumerate(acumulado):
        if mes > 0 and valor >= 0:
            return mes
    return None


def evaluar(s: Supuestos, escenario: str = 'Personalizado') -> Resultado:
    r = Resultado(escenario=escenario, supuestos=s)
    tm = s.tasa_mensual
    cuidadoras_previas = 0
    flujos, acumulado, acumulado_desc = [], [], []
    for mes in range(s.horizonte_meses + 1):
        if mes == 0:
            fila = {'mes': 0, 'familias': 0.0, 'horas_semana': 0.0, 'horas_mes': 0.0,
                    'cuidadoras': 0, 'cuidadoras_nuevas': 0, 'trabajadoras_sociales': 0,
                    'ingresos': 0.0, 'costo_variable': 0.0, 'costos_fijos': 0.0,
                    'capacitacion': 0.0, 'inversion': s.inversion_inicial,
                    'flujo': -s.inversion_inicial}
            # Las 6 cuidadoras del piloto se capacitan con la inversión inicial.
            cuidadoras_previas = s.cuidadoras_piloto
        else:
            familias = familias_en_mes(s, mes)
            horas_semana = familias * s.horas_semana_familia
            horas_mes = horas_semana * SEMANAS_POR_MES
            cuidadoras = cuidadoras_necesarias(s, horas_semana)
            nuevas = max(0, cuidadoras - cuidadoras_previas) + s.rotacion_mensual * cuidadoras
            ts = trabajadoras_sociales(s, familias)
            ingresos = horas_mes * s.tarifa_hora
            variable = horas_mes * s.costo_variable_hora
            fijos = fijos_sin_personal_variable(s) + ts * s.trabajadora_social
            capacitacion = nuevas * s.capacitacion_cuidadora
            flujo = ingresos - variable - fijos - capacitacion
            fila = {'mes': mes, 'familias': familias, 'horas_semana': horas_semana,
                    'horas_mes': horas_mes, 'cuidadoras': cuidadoras, 'cuidadoras_nuevas': nuevas,
                    'trabajadoras_sociales': ts, 'ingresos': ingresos, 'costo_variable': variable,
                    'costos_fijos': fijos, 'capacitacion': capacitacion, 'inversion': 0.0,
                    'flujo': flujo}
            cuidadoras_previas = cuidadoras
        flujos.append(fila['flujo'])
        acumulado.append((acumulado[-1] if acumulado else 0) + fila['flujo'])
        acumulado_desc.append((acumulado_desc[-1] if acumulado_desc else 0)
                              + fila['flujo'] / (1 + tm) ** mes)
        fila['flujo_acumulado'] = acumulado[-1]
        fila['flujo_descontado_acumulado'] = acumulado_desc[-1]
        r.meses.append(fila)

    r.van = van(flujos, tm)
    tm_tir = tir(flujos)
    r.tir_anual = None if tm_tir is None else (1 + tm_tir) ** 12 - 1
    r.payback_meses = _payback(acumulado)
    r.payback_descontado_meses = _payback(acumulado_desc)
    r.utilidad_neta = acumulado[-1]
    r.deficit_maximo = -min(0.0, min(acumulado))

    estable = r.meses[-1]
    r.familias_estable = estable['familias']
    r.horas_mes_estable = estable['horas_mes']
    r.cuidadoras_estable = estable['cuidadoras']
    if s.margen_hora > 0:
        # Punto de equilibrio operativo con la plantilla del estado estable.
        r.punto_equilibrio_horas_mes = estable['costos_fijos'] / s.margen_hora
        r.punto_equilibrio_familias = (r.punto_equilibrio_horas_mes / SEMANAS_POR_MES
                                       / s.horas_semana_familia)

    # Decisión por etapas: ¿se cerraría en el mes de revisión?
    revision = r.meses[s.mes_revision]
    umbral = None if r.punto_equilibrio_familias is None else s.umbral_continuar * r.punto_equilibrio_familias
    r.se_cierra_en_revision = umbral is None or revision['familias'] < umbral
    if r.se_cierra_en_revision:
        cierre = s.meses_costo_cierre * revision['costos_fijos']
        truncados = flujos[:s.mes_revision + 1] + [-cierre]
        r.van_con_revision = van(truncados, tm)
        r.utilidad_neta_con_revision = sum(truncados)
    else:
        r.van_con_revision = r.van
        r.utilidad_neta_con_revision = r.utilidad_neta

    primer_mes = r.meses[1]
    r.capital_inversion = s.inversion_inicial
    r.capital_operacion = 3 * (primer_mes['costos_fijos'] + primer_mes['costo_variable'])
    r.capital_colchon = s.colchon * (r.capital_inversion + r.capital_operacion)
    r.capital_total = r.capital_inversion + r.capital_operacion + r.capital_colchon
    return r


def evaluar_escenarios(escenarios=None):
    escenarios = escenarios or ESCENARIOS
    return {nombre: evaluar(s, nombre) for nombre, s in escenarios.items()}


def valor_esperado(resultados, probabilidades=None, con_revision=False):
    probabilidades = probabilidades or PROBABILIDADES
    return sum(probabilidades[n] * (r.van_con_revision if con_revision else r.van)
               for n, r in resultados.items())


def con_cambios(base: Supuestos, **cambios) -> Supuestos:
    return replace(base, **cambios)


# Filas de indicadores.escenarios_programa: (clave, unidad, función sobre Resultado).
INDICADORES = [
    ('VAN', 'pesos', lambda r: r.van),
    ('VAN con revisión en el mes 12', 'pesos', lambda r: r.van_con_revision),
    ('Se cierra en la revisión del mes 12', 'sí = 1', lambda r: int(r.se_cierra_en_revision)),
    ('TIR anual', '%', lambda r: None if r.tir_anual is None else r.tir_anual * 100),
    ('Payback', 'meses', lambda r: r.payback_meses),
    ('Payback descontado', 'meses', lambda r: r.payback_descontado_meses),
    ('Punto de equilibrio', 'horas al mes', lambda r: r.punto_equilibrio_horas_mes),
    ('Punto de equilibrio en familias', 'familias', lambda r: r.punto_equilibrio_familias),
    ('Utilidad neta acumulada (60 meses)', 'pesos', lambda r: r.utilidad_neta),
    ('Inversión inicial', 'pesos', lambda r: r.capital_inversion),
    ('Capital de operación (3 meses)', 'pesos', lambda r: r.capital_operacion),
    ('Colchón para imprevistos (10 %)', 'pesos', lambda r: r.capital_colchon),
    ('Requerimiento total de capital', 'pesos', lambda r: r.capital_total),
    ('Déficit acumulado máximo', 'pesos', lambda r: r.deficit_maximo),
    ('Familias atendidas en estado estable', 'familias', lambda r: r.familias_estable),
    ('Horas de cuidado al mes en estado estable', 'horas al mes', lambda r: r.horas_mes_estable),
    ('Cuidadoras empleadas en estado estable', 'cuidadoras', lambda r: r.cuidadoras_estable),
    ('Margen por hora', 'pesos por hora', lambda r: r.supuestos.margen_hora),
]
