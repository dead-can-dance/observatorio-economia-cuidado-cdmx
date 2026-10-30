"""Hallazgos e indicadores derivados para el tablero.

Todo se calcula a partir de las tablas de `indicadores`, nunca de `cruda` ni `curada`,
y respeta las advertencias de docs/diccionario_datos.md ("Cómo NO leer estos datos"):

  1. El DENUE cuenta establecimientos, no lugares: se habla de presión sobre la oferta,
     nunca de cobertura.
  2. La ENASIC es nacional: sus cifras nunca se atribuyen a la CDMX.
  3. Las zonas sin respaldo usan ubicaciones aproximadas: son exploratorias.
  4. Las cifras con muestra chica se marcan y no se usan para encabezar.
  5. La unidad de análisis es la mujer cuidadora: los hombres solo como referencia.

Cada hallazgo lleva su fuente y su nivel geográfico, porque ninguna cifra se publica sin
ellos. Los números se redactan con el formato de México (1,234.5).
"""

import math
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd

from .esquema import a_registros
from .fuente_csv import CLAVE_BRECHA_NO_PAGADO

NBSP = ' '
FTE_ENUT = 'INEGI, ENUT 2024'
FTE_ENASIC = 'INEGI, ENASIC 2022'
FTE_CENSO = 'INEGI, Censo de Población y Vivienda 2020'
FTE_CRUCE = 'INEGI, Censo 2020 + DENUE 05/2026'
FTE_DENUE = 'INEGI, DENUE 05/2026'

AVISO_ENASIC = ('Cifra nacional: los microdatos de la ENASIC no traen geografía, así que '
                'no se puede atribuir a la Ciudad de México.')
AVISO_PRESION = ('Es presión sobre la oferta, no cobertura: el DENUE registra '
                 'establecimientos, no lugares disponibles.')
AVISO_EXPLORATORIO = ('Exploratorio: la ubicación de cada AGEB es aproximada (mediana de los '
                      'establecimientos del DENUE), no el centroide oficial.')
TOTAL_CUIDADO = 'Cuidado a integrantes del hogar (total)'


# =============================================================================
# Formato
# =============================================================================

def num(v, decimales=1):
    return f'{v:,.{decimales}f}'


def ent(v):
    """Entero con separador de miles. Redondea HALF_UP: la mediana 926.5 es 927."""
    return f'{int(Decimal(repr(float(v))).quantize(Decimal(1), rounding=ROUND_HALF_UP)):,}'


def pct(v, decimales=1):
    return f'{v:,.{decimales}f}{NBSP}%'


def horas(v):
    return f'{v:,.1f}{NBSP}h'


def veces(a, b, decimales=1):
    return num(a / b, decimales) if b else '—'


def _y(siguiente):
    """'y' o 'e': delante de una palabra que empieza con sonido i (Iztapalapa) va 'e'."""
    s = siguiente.lower()
    return 'e' if s.startswith(('i', 'í', 'hi')) and not s.startswith(('hia', 'hie', 'hio', 'hiu')) else 'y'


def lista(nombres):
    nombres = list(nombres)
    if not nombres:
        return ''
    if len(nombres) == 1:
        return nombres[0]
    return f'{", ".join(nombres[:-1])} {_y(nombres[-1])} {nombres[-1]}'


_NUMEROS = ['Ninguna', 'Una', 'Dos', 'Tres', 'Cuatro', 'Cinco', 'Seis', 'Siete', 'Ocho',
            'Nueve', 'Diez']


def _de_cada_diez(porcentaje, resto):
    """62.2 -> 'Seis de cada diez mujeres cuidan'. Redondea como lo haría un titular."""
    n = int(Decimal(str(porcentaje / 10)).quantize(Decimal(1), rounding=ROUND_HALF_UP))
    return f'{_NUMEROS[n]} de cada diez {resto}'


def hallazgo(clave, titulo, texto, *, fuente, nivel, destacado=False,
             exploratorio=False, advertencia=None):
    return {'clave': clave, 'titulo': titulo, 'texto': texto, 'fuente': fuente,
            'nivel_geografico': nivel, 'destacado': destacado,
            'exploratorio': exploratorio, 'advertencia': advertencia}


def _kpi(repo, clave):
    df = repo.tabla('kpi_cdmx')
    fila = df[df['clave'] == clave]
    if fila.empty:
        return None
    v = fila['valor_num'].iloc[0]
    return fila['valor_texto'].iloc[0] if pd.isna(v) else float(v)


def _fila(df, **filtros):
    for col, valor in filtros.items():
        df = df[df[col] == valor]
    return None if df.empty else df.iloc[0]


# =============================================================================
# Nivel nacional: ENUT nacional + ENASIC
# =============================================================================

def hallazgos_nacionales(repo):
    enut = repo.tabla('enut_carga_actividad')
    nac = enut[enut['ambito'] == 'Nacional']
    muj = nac[nac['sexo'] == 'Mujeres'].set_index('actividad')
    hom = nac[nac['sexo'] == 'Hombres'].set_index('actividad')
    resultado = []

    m, h = muj.loc[TOTAL_CUIDADO], hom.loc[TOTAL_CUIDADO]
    resultado.append(hallazgo(
        'nac_cuidado_total', _de_cada_diez(m.pct_realiza, 'mujeres cuidan'),
        f'En el país, {pct(m.pct_realiza)} de las mujeres de 12 años y más cuida a '
        f'integrantes de su hogar. Las que cuidan le dedican {horas(m.horas_semana)} a la '
        f'semana; los hombres que cuidan, {horas(h.horas_semana)} (referencia).',
        fuente=FTE_ENUT, nivel='Nacional', destacado=True))

    especificas = muj.drop(index=TOTAL_CUIDADO)
    act = especificas['horas_semana'].idxmax()
    mm, hh = especificas.loc[act], hom.loc[act]
    resultado.append(hallazgo(
        'nac_mas_intensivo', 'El cuidado más intensivo',
        f'El cuidado que más horas exige es «{act.lower()}»: {horas(mm.horas_semana)} a la '
        f'semana entre las mujeres que lo realizan, {veces(mm.horas_semana, hh.horas_semana)} '
        f'veces las horas de los hombres (referencia).',
        fuente=FTE_ENUT, nivel='Nacional'))

    enasic = repo.tabla('enasic_cuidadoras')

    def tema(t):
        return enasic[enasic['tema'] == t].set_index('categoria')['pct']

    busqueda = tema('Búsqueda de servicios')
    razones = tema('Razones para no buscar').sort_values(ascending=False)
    if 'Sí buscó' in busqueda:
        r1, r2 = razones.index[0], razones.index[1]
        resultado.append(hallazgo(
            'nac_busqueda', 'Casi ninguna busca servicios de cuidado',
            f'Solo {pct(busqueda["Sí buscó"])} de las mujeres cuidadoras buscó una guardería, '
            f'casa de día o asilo. Entre las que no buscaron, {pct(razones[r1])} dice '
            f'«{r1.lower()}» y {pct(razones[r2])}, «{r2.lower()}».',
            fuente=FTE_ENASIC, nivel='Nacional', destacado=True, advertencia=AVISO_ENASIC))

    pref = tema('Preferencia de cuidado')
    if {'En su casa', 'No contrataría'} <= set(pref.index):
        centros = [(c, pref[c]) for c in ('En un centro público', 'En un centro privado') if c in pref]
        extra = ''
        if len(centros) == 2:
            extra = (f' Un centro público lo elegiría {pct(centros[0][1])} y uno privado, '
                     f'{pct(centros[1][1])}.')
        resultado.append(hallazgo(
            'nac_preferencia', 'La preferencia es cuidar en casa',
            f'Si tuvieran que contratar un servicio, {pct(pref["En su casa"])} de las '
            f'cuidadoras preferiría que fuera en su casa y {pct(pref["No contrataría"])} no '
            f'contrataría ninguno.{extra}',
            fuente=FTE_ENASIC, nivel='Nacional', advertencia=AVISO_ENASIC))

    disp = tema('Disposición a cuidar')
    if len(disp) == 2:
        pagada = disp.get('Le gustaría ser cuidadora profesional si le pagaran')
        capacitar = disp.get('Estaría dispuesta a capacitarse para ser cuidadora')
        if pagada is not None and capacitar is not None:
            resultado.append(hallazgo(
                'nac_disposicion', 'Disposición a cuidar con pago',
                f'{pct(pagada)} de las cuidadoras sería cuidadora profesional si le pagaran '
                f'y {pct(capacitar)} estaría dispuesta a capacitarse para hacerlo.',
                fuente=FTE_ENASIC, nivel='Nacional', advertencia=AVISO_ENASIC))
    return resultado


# =============================================================================
# Nivel ciudad: ENUT CDMX + Censo
# =============================================================================

def hallazgos_cdmx(repo):
    resultado = []
    brecha = _kpi(repo, CLAVE_BRECHA_NO_PAGADO)
    jornada = repo.tabla('enut_doble_jornada')
    muj = _fila(jornada, grupo='Mujeres ocupadas')
    if brecha is not None and muj is not None:
        # Se encabeza con el trabajo no pagado (sólido) y la jornada total va de apoyo,
        # como acordó el equipo (diccionario de datos, enut_doble_jornada).
        resultado.append(hallazgo(
            'cdmx_doble_jornada', 'La doble jornada',
            f'Las mujeres ocupadas de la CDMX hacen {horas(brecha)} más de trabajo no pagado '
            f'a la semana que los hombres ocupados (referencia). Con el trabajo pagado, su '
            f'jornada total llega a {horas(muj.horas_jornada_total)}.',
            fuente=FTE_ENUT, nivel='CDMX', destacado=True))

    br = repo.tabla('enut_brecha_mujeres_cdmx')
    total = _fila(br, actividad=TOTAL_CUIDADO)
    if total is not None:
        resultado.append(hallazgo(
            'cdmx_cuidado_total', _de_cada_diez(total.pct_realiza_mujeres, 'mujeres cuidan'),
            f'{pct(total.pct_realiza_mujeres)} de las mujeres de 12 años y más de la CDMX '
            f'cuida a integrantes de su hogar. Las que cuidan le dedican '
            f'{horas(total.horas_mujeres)} a la semana, {num(total.razon_mujeres_hombres, 2)} '
            f'veces las horas de los hombres que cuidan (referencia).',
            fuente=FTE_ENUT, nivel='CDMX', destacado=True))

    # La mayor brecha, solo entre cifras con al menos 100 casos (advertencia 4).
    especificas = br[(br['actividad'] != TOTAL_CUIDADO)
                     & (br['actividad'] != 'Trabajo doméstico no remunerado')]
    solidas = especificas[especificas['n_mujeres'] >= 100]
    if not solidas.empty:
        top = solidas.sort_values('razon_mujeres_hombres', ascending=False).iloc[0]
        fragiles = especificas[(especificas['n_mujeres'] < 100)
                               & (especificas['razon_mujeres_hombres'] >= top.razon_mujeres_hombres)]
        nota = None
        if not fragiles.empty:
            f = fragiles.iloc[0]
            nota = (f'«{f.actividad}» tiene una razón igual o mayor ({num(f.razon_mujeres_hombres, 2)}), '
                    f'pero sale de {int(f.n_mujeres)} casos: es solo un indicio.')
        resultado.append(hallazgo(
            'cdmx_mayor_brecha', 'Donde la brecha es más amplia',
            f'En el {top.actividad[0].lower() + top.actividad[1:]}, las mujeres que lo realizan '
            f'le dedican {horas(top.horas_mujeres)} a la semana: '
            f'{num(top.razon_mujeres_hombres, 2)} veces lo de los hombres (referencia).',
            fuente=FTE_ENUT, nivel='CDMX', advertencia=nota))

    grupos = repo.tabla('enut_cuidado_por_grupo')
    confiables = grupos[grupos['confiable'].fillna(False)]
    edad = confiables[confiables['tipo_grupo'] == 'Grupo de edad']
    if not edad.empty:
        pico = edad.sort_values('horas_cuidado', ascending=False).iloc[0]
        resultado.append(hallazgo(
            'cdmx_edad', 'Las que más cuidan',
            f'Las mujeres de {pico.grupo.replace("–", " a ")} años son las que más cuidan: '
            f'{horas(pico.horas_cuidado)} a la semana en promedio, contando también a las que '
            f'no cuidan.',
            fuente=FTE_ENUT, nivel='CDMX'))

    cond = confiables[confiables['tipo_grupo'] == 'Condición de actividad'].set_index('grupo')
    if {'Ocupada', 'Dedicada al hogar o al cuidado'} <= set(cond.index):
        oc, hog = cond.loc['Ocupada'], cond.loc['Dedicada al hogar o al cuidado']
        resultado.append(hallazgo(
            'cdmx_ocupadas', 'Tener empleo no libera del cuidado',
            f'Las mujeres ocupadas cuidan {horas(oc.horas_cuidado)} a la semana en promedio, '
            f'cerca de las {horas(hog.horas_cuidado)} de las dedicadas al hogar o al cuidado. '
            f'Y cuida una proporción mayor de ellas: {pct(oc.pct_que_cuida)} frente a '
            f'{pct(hog.pct_que_cuida)}.'
            if oc.pct_que_cuida > hog.pct_que_cuida else
            f'Las mujeres ocupadas cuidan {horas(oc.horas_cuidado)} a la semana en promedio, '
            f'frente a {horas(hog.horas_cuidado)} de las dedicadas al hogar o al cuidado.',
            fuente=FTE_ENUT, nivel='CDMX'))

    enut = repo.tabla('enut_carga_actividad')
    c = _fila(enut, ambito='CDMX', sexo='Mujeres', actividad=TOTAL_CUIDADO)
    n = _fila(enut, ambito='Nacional', sexo='Mujeres', actividad=TOTAL_CUIDADO)
    if c is not None and n is not None:
        menos_pct = c.pct_realiza < n.pct_realiza
        menos_h = c.horas_semana < n.horas_semana
        resultado.append(hallazgo(
            'cdmx_vs_pais', 'La ciudad frente al país',
            f'En la CDMX cuida una proporción {"menor" if menos_pct else "mayor"} de mujeres '
            f'que en el país ({pct(c.pct_realiza)} frente a {pct(n.pct_realiza)}) y las que '
            f'cuidan le dedican {"menos" if menos_h else "más"} horas '
            f'({horas(c.horas_semana)} frente a {horas(n.horas_semana)}).',
            fuente=FTE_ENUT, nivel='CDMX'))

    carga = _kpi(repo, 'Censo · carga directa x100 mujeres, CDMX')
    alc = repo.tabla('resumen_alcaldia')
    if carga is not None and not alc.empty:
        top = alc.sort_values('carga_directa_x100_mujeres', ascending=False).iloc[0]
        resultado.append(hallazgo(
            'cdmx_carga', 'Quién necesita cuidado directo',
            f'En la ciudad hay {num(carga)} personas que necesitan cuidado directo (niñas y '
            f'niños de 0 a 5 años y personas con discapacidad para su autocuidado) por cada 100 '
            f'mujeres de 15 a 59 años. La carga más alta está en {top.alcaldia} '
            f'({num(top.carga_directa_x100_mujeres)}).',
            fuente=FTE_CENSO, nivel='CDMX'))
    return resultado


# =============================================================================
# Nivel alcaldía
# =============================================================================

# Indicadores de indicadores.resumen_alcaldia que el tablero sabe mostrar. La fuente
# es la de cada columna (la fila completa cita el cruce Censo + DENUE).
INDICADORES_ALCALDIA = [
    {'columna': 'carga_directa_x100_mujeres', 'etiqueta': 'Carga de cuidado directo',
     'unidad': 'personas por cada 100 mujeres de 15 a 59', 'decimales': 1,
     'descripcion': 'Niñas y niños de 0 a 5 años más personas con discapacidad para '
                    'vestirse, bañarse o comer, por cada 100 mujeres de 15 a 59 años.',
     'fuente': FTE_CENSO},
    {'columna': 'mujeres_sin_respaldo', 'etiqueta': 'Mujeres en zonas sin respaldo',
     'unidad': 'mujeres de 15 a 59', 'decimales': 0,
     'descripcion': 'Mujeres de 15 a 59 que viven en AGEB de alta carga sin guardería, '
                    'residencia ni centro de día a menos de 1 km.',
     'fuente': FTE_CRUCE, 'exploratorio': True},
    {'columna': 'agebs_sin_respaldo', 'etiqueta': 'AGEB de alta carga sin respaldo',
     'unidad': 'AGEB', 'decimales': 0,
     'descripcion': 'AGEB en el cuartil más alto de carga de la ciudad sin ningún '
                    'servicio de respaldo a menos de 1 km.',
     'fuente': FTE_CRUCE, 'exploratorio': True},
    {'columna': 'pct_agebs_alta_carga_sin_respaldo',
     'etiqueta': 'Zonas de alta carga sin respaldo', 'unidad': '% de sus AGEB de alta carga',
     'decimales': 1,
     'descripcion': 'De las AGEB de alta carga de la alcaldía, qué porcentaje no tiene '
                    'ningún servicio de respaldo a menos de 1 km. No aplica donde no hay '
                    'AGEB de alta carga.',
     'fuente': FTE_CRUCE, 'exploratorio': True},
    {'columna': 'ninos_0a5_por_guarderia', 'etiqueta': 'Niñas y niños por guardería',
     'unidad': 'niñas y niños de 0 a 5 por guardería', 'decimales': 0,
     'descripcion': 'Niñas y niños de 0 a 5 años por cada guardería registrada en el DENUE.',
     'fuente': FTE_CRUCE, 'advertencia': AVISO_PRESION},
    {'columna': 'mayores_60_por_establecimiento',
     'etiqueta': 'Personas mayores por establecimiento',
     'unidad': 'personas de 60+ por establecimiento', 'decimales': 0,
     'descripcion': 'Personas de 60 años o más por cada residencia, asilo o centro de día '
                    'para personas mayores.',
     'fuente': FTE_CRUCE, 'advertencia': AVISO_PRESION},
    {'columna': 'pct_guarderias_publicas', 'etiqueta': 'Guarderías públicas',
     'unidad': '% de las guarderías', 'decimales': 1,
     'descripcion': 'Porcentaje de las guarderías de la alcaldía que son del sector público.',
     'fuente': FTE_DENUE},
    {'columna': 'pct_hog_jefa', 'etiqueta': 'Hogares con jefatura femenina',
     'unidad': '% de los hogares', 'decimales': 1,
     'descripcion': 'Hogares cuya persona de referencia es una mujer.', 'fuente': FTE_CENSO},
    {'columna': 'pct_mujeres_inactivas', 'etiqueta': 'Mujeres fuera del mercado laboral',
     'unidad': '% de las mujeres de 12+', 'decimales': 1,
     'descripcion': 'Mujeres de 12 años y más que no participan en el mercado laboral. '
                    'Incluye estudiantes y jubiladas.', 'fuente': FTE_CENSO},
    {'columna': 'pct_60mas', 'etiqueta': 'Población de 60 años o más',
     'unidad': '% de la población', 'decimales': 1,
     'descripcion': 'Proporción de la población que tiene 60 años o más.', 'fuente': FTE_CENSO},
    {'columna': 'mujeres_15a59', 'etiqueta': 'Mujeres de 15 a 59 años',
     'unidad': 'mujeres', 'decimales': 0,
     'descripcion': 'Población sobre la que recae el trabajo de cuidado.', 'fuente': FTE_CENSO},
]


def _lugar(serie, indice, descendente=True):
    """Lugar (1 = mayor) de un valor dentro de la serie, con empates en el mismo lugar."""
    valor = serie.loc[indice]
    if pd.isna(valor):
        return None
    validos = serie.dropna()
    mejores = (validos > valor).sum() if descendente else (validos < valor).sum()
    return int(mejores) + 1


def contexto_ciudad(repo):
    """Referencias de toda la ciudad que usan las fichas de alcaldía."""
    alc = repo.tabla('resumen_alcaldia')
    est = repo.tabla('establecimientos_cuidado')
    guarderias = est[est['tipo'] == 'Guardería']
    publicas = (guarderias['sector'] == 'Público').mean() * 100 if len(guarderias) else None
    # Desigualdad interna de cada alcaldía: percentil 90 entre percentil 10 de la carga
    # de sus AGEB (como en el notebook 02), para poder compararlas entre sí.
    q = (repo.tabla('carga_ageb').groupby('cve_mun')['carga_directa_x100_mujeres']
         .quantile([0.1, 0.9]).unstack())
    return {
        'carga_cdmx': _kpi(repo, 'Censo · carga directa x100 mujeres, CDMX'),
        'mujeres_15a59': int(alc['mujeres_15a59'].sum()),
        'mujeres_sin_respaldo': int(alc['mujeres_sin_respaldo'].sum()),
        'agebs_sin_respaldo': int(alc['agebs_sin_respaldo'].sum()),
        'pct_guarderias_publicas': None if publicas is None else round(publicas, 1),
        'medianas': {i['columna']: _a_float(alc[i['columna']].median())
                     for i in INDICADORES_ALCALDIA},
        'razon_p90_p10': {cve: round(float(fila[0.9] / fila[0.1]), 2)
                          for cve, fila in q.iterrows() if fila[0.1]},
    }


def _a_float(v):
    return None if v is None or pd.isna(v) else float(v)


def posiciones(repo, cve_mun):
    """Lugar de la alcaldía (de 16) en cada indicador; 1 = valor más alto."""
    alc = repo.tabla('resumen_alcaldia').set_index('cve_mun')
    salida = {}
    for ind in INDICADORES_ALCALDIA:
        col = ind['columna']
        serie = alc[col]
        lugar = _lugar(serie, cve_mun)
        empates = []
        if lugar is not None:
            valor = serie.loc[cve_mun]
            empates = sorted(alc.loc[(serie == valor) & (alc.index != cve_mun), 'alcaldia'])
        salida[col] = {'lugar': lugar, 'de': int(serie.notna().sum()), 'empates': empates}
    return salida


def resumen_agebs(repo, cve_mun=None):
    """Distribución de la carga entre las AGEB de la ciudad o de una alcaldía."""
    a = repo.tabla('carga_ageb')
    if cve_mun is not None:
        a = a[a['cve_mun'] == cve_mun]
    carga = a['carga_directa_x100_mujeres'].dropna()
    alta = a['alta_carga'].fillna(False).astype(bool)
    sin_g = a['sin_guarderia'].fillna(False).astype(bool)
    sin_r = a['sin_respaldo'].fillna(False).astype(bool)
    mujeres = a['mujeres_15a59'].fillna(0)
    p10, p50, p90 = (carga.quantile(q) for q in (0.1, 0.5, 0.9)) if len(carga) else (None,) * 3
    return {
        'agebs': int(len(a)),
        'percentil_10': _redondo(p10), 'mediana': _redondo(p50), 'percentil_90': _redondo(p90),
        'razon_p90_p10': _redondo(p90 / p10, 2) if p10 else None,
        'embudo': [
            {'etapa': 'AGEB urbanas analizadas', 'agebs': int(len(a)),
             'mujeres_15a59': int(mujeres.sum())},
            {'etapa': 'De alta carga (cuartil superior de la ciudad)', 'agebs': int(alta.sum()),
             'mujeres_15a59': int(mujeres[alta].sum())},
            {'etapa': 'De alta carga y sin guardería a 1 km', 'agebs': int(sin_g.sum()),
             'mujeres_15a59': int(mujeres[sin_g].sum())},
            {'etapa': 'De alta carga y sin ningún respaldo a 1 km', 'agebs': int(sin_r.sum()),
             'mujeres_15a59': int(mujeres[sin_r].sum())},
        ],
    }


def _redondo(v, decimales=1):
    return None if v is None or pd.isna(v) else round(float(v), decimales)


def histograma_carga(repo, cve_mun=None):
    """Conteo de AGEB por intervalos de carga de 1 punto, separando las de alta carga.

    Los intervalos son los de toda la ciudad aunque se filtre una alcaldía, para que las
    distribuciones se puedan comparar. Se separa por la bandera alta_carga y no por el
    valor: el umbral (24.1) se aplicó sobre la cifra sin redondear, así que en el
    intervalo 24-25 conviven AGEB de los dos lados.
    """
    todas = repo.tabla('carga_ageb')
    a = todas if cve_mun is None else todas[todas['cve_mun'] == cve_mun]
    valores = todas['carga_directa_x100_mujeres'].dropna()
    inicio, fin = int(math.floor(valores.min())), int(math.ceil(valores.max()))
    if fin == valores.max():
        fin += 1
    alta = a['alta_carga'].fillna(False).astype(bool)
    intervalos = []
    for desde in range(inicio, fin):
        en = (a['carga_directa_x100_mujeres'] >= desde) & (a['carga_directa_x100_mujeres'] < desde + 1)
        intervalos.append({'desde': desde, 'hasta': desde + 1,
                           'alta_carga': int((en & alta).sum()),
                           'resto': int((en & ~alta).sum())})
    umbral = todas.loc[todas['alta_carga'].fillna(False).astype(bool), 'carga_directa_x100_mujeres'].min()
    return {'intervalos': intervalos, 'umbral_alta_carga': _redondo(umbral)}


def ficha_alcaldia(repo, cve_mun):
    alc = repo.tabla('resumen_alcaldia')
    fila = _fila(alc, cve_mun=cve_mun)
    if fila is None:
        return None
    ctx = contexto_ciudad(repo)
    pos = posiciones(repo, cve_mun)
    agebs = resumen_agebs(repo, cve_mun)

    est = repo.tabla('establecimientos_cuidado')
    est = est[est['cve_mun'] == cve_mun]
    por_tipo = (est.groupby(['tipo', 'sector']).size().unstack(fill_value=0)
                .reindex(columns=['Público', 'Privado'], fill_value=0))
    respaldo_tipos = set(est.loc[est['es_respaldo'].fillna(False).astype(bool), 'tipo'])
    tipos = [{'tipo': t, 'publico': int(r['Público']), 'privado': int(r['Privado']),
              'total': int(r.sum()), 'es_respaldo': t in respaldo_tipos}
             for t, r in por_tipo.iterrows()]
    tipos.sort(key=lambda x: (not x['es_respaldo'], -x['total']))

    return {
        'alcaldia': a_registros(alc[alc['cve_mun'] == cve_mun])[0],
        'posiciones': pos,
        'ciudad': ctx,
        'agebs': agebs,
        'establecimientos': {
            'total': int(len(est)),
            'respaldo': int(est['es_respaldo'].fillna(False).sum()),
            'por_tipo': tipos,
            'fuente': FTE_DENUE,
        },
        'hallazgos': hallazgos_alcaldia(repo, fila, ctx, pos, agebs),
    }


def hallazgos_alcaldia(repo, f, ctx, pos, agebs):
    nombre = f.alcaldia
    H = []

    # --- Carga de cuidado -------------------------------------------------------
    carga, cdmx = f.carga_directa_x100_mujeres, ctx['carga_cdmx']
    lugar = int(f.rango_carga)
    empates = pos['carga_directa_x100_mujeres']['empates']
    if cdmx is not None:
        dif = round(carga - cdmx, 1)
        comparacion = (f', {num(abs(dif))} más que el conjunto de la ciudad ({num(cdmx)})' if dif > 0
                       else f', {num(abs(dif))} menos que el conjunto de la ciudad ({num(cdmx)})' if dif < 0
                       else ', igual que el conjunto de la ciudad')
    else:
        comparacion = ''
    if empates:
        cierre = f'Comparte el {lugar}.º lugar de 16 con {lista(empates)}.'
    elif lugar == 1:
        cierre = 'Es la alcaldía con la carga más alta de la ciudad.'
    elif lugar == 16:
        cierre = 'Es la alcaldía con la carga más baja de la ciudad.'
    else:
        cierre = f'Ocupa el {lugar}.º lugar de 16 (1 = la carga más alta).'
    H.append(hallazgo(
        'carga', 'Carga de cuidado',
        f'Hay {num(carga)} personas que necesitan cuidado directo por cada 100 mujeres de 15 '
        f'a 59 años{comparacion}. {cierre}',
        fuente=FTE_CENSO, nivel='Alcaldía', destacado=_extremo({'lugar': lugar, 'de': 16})))

    # --- Zonas sin respaldo (hallazgo B, exploratorio) --------------------------
    alta, sin = int(f.agebs_alta_carga), int(f.agebs_sin_respaldo)
    mujeres = int(f.mujeres_sin_respaldo)
    if alta == 0:
        H.append(hallazgo(
            'sin_respaldo', 'Zonas sin respaldo',
            'Ninguna de sus AGEB está en el cuartil de mayor carga de la ciudad, así que el '
            'indicador de zonas sin respaldo no aplica.',
            fuente=FTE_CRUCE, nivel='Alcaldía', exploratorio=True))
    elif sin == 0:
        H.append(hallazgo(
            'sin_respaldo', 'Zonas sin respaldo',
            f'Sus {alta} AGEB de alta carga tienen al menos una guardería, residencia o centro '
            f'de día a menos de 1 km.',
            fuente=FTE_CRUCE, nivel='Alcaldía', exploratorio=True,
            advertencia=AVISO_EXPLORATORIO))
    else:
        total = ctx['mujeres_sin_respaldo']
        participacion = mujeres / total * 100 if total else 0
        lugar_sin = pos['agebs_sin_respaldo']['lugar']
        extra = ' Es la alcaldía que más concentra en la ciudad.' if lugar_sin == 1 else ''
        H.append(hallazgo(
            'sin_respaldo', 'Mujeres que cuidan sin respaldo cercano',
            f'{sin} de sus {alta} AGEB de alta carga ({pct(f.pct_agebs_alta_carga_sin_respaldo)}) '
            f'no tienen ninguna guardería, residencia ni centro de día a menos de 1 km. Ahí '
            f'viven {ent(mujeres)} mujeres de 15 a 59 años, {pct(participacion)} de las que '
            f'están en esa situación en toda la ciudad.{extra}',
            fuente=FTE_CRUCE, nivel='Alcaldía', exploratorio=True,
            destacado=lugar_sin is not None and lugar_sin <= 3
            or (pos['pct_agebs_alta_carga_sin_respaldo']['lugar'] or 99) <= 3,
            advertencia=AVISO_EXPLORATORIO))

    # --- Desigualdad interna (carga por AGEB) -----------------------------------
    if agebs['agebs'] >= 10 and agebs['percentil_10']:
        razones = pd.Series(ctx['razon_p90_p10'])
        p = {'lugar': _lugar(razones, f.cve_mun) if f.cve_mun in razones else None,
             'de': len(razones)}
        H.append(hallazgo(
            'desigualdad', 'Diferencias dentro de la alcaldía',
            f'Entre sus {agebs["agebs"]} AGEB analizadas, la carga va de '
            f'{num(agebs["percentil_10"])} a {num(agebs["percentil_90"])} personas por cada 100 '
            f'mujeres (percentiles 10 y 90): {num(agebs["razon_p90_p10"])} veces más en las '
            f'zonas más cargadas que en las menos cargadas.',
            fuente=FTE_CRUCE, nivel='AGEB',
            destacado=p['lugar'] is not None and p['lugar'] <= 2))

    # --- Guarderías -------------------------------------------------------------
    p = pos['ninos_0a5_por_guarderia']
    mediana = ctx['medianas']['ninos_0a5_por_guarderia']
    publicas = ''
    if not pd.isna(f.pct_guarderias_publicas) and ctx['pct_guarderias_publicas'] is not None:
        publicas = (f' Tiene {int(f.guarderias)} guarderías registradas, '
                    f'{pct(f.pct_guarderias_publicas)} públicas (en la ciudad, '
                    f'{pct(ctx["pct_guarderias_publicas"])}).')
    H.append(hallazgo(
        'guarderias', 'Presión sobre las guarderías',
        f'Hay {ent(f.ninos_0a5_por_guarderia)} niñas y niños de 0 a 5 años por cada guardería '
        f'registrada en el DENUE: {_lugar_texto(p)}. La mediana de las alcaldías es '
        f'{ent(mediana)}.{publicas}',
        fuente=FTE_CRUCE, nivel='Alcaldía', destacado=_extremo(p),
        advertencia=AVISO_PRESION))

    # --- Personas mayores -------------------------------------------------------
    p = pos['mayores_60_por_establecimiento']
    H.append(hallazgo(
        'mayores', 'Cuidado de personas mayores',
        f'{pct(f.pct_60mas)} de su población tiene 60 años o más. Hay '
        f'{int(f.cuidado_mayores)} residencias, asilos y centros de día para personas mayores: '
        f'{ent(f.mayores_60_por_establecimiento)} personas de 60+ por establecimiento, '
        f'{_lugar_texto(p)}.',
        fuente=FTE_CRUCE, nivel='Alcaldía', destacado=_extremo(p),
        advertencia=AVISO_PRESION))

    # --- Hogares y mercado laboral ----------------------------------------------
    pj, pi = pos['pct_hog_jefa'], pos['pct_mujeres_inactivas']
    H.append(hallazgo(
        'hogares', 'Hogares y trabajo de las mujeres',
        f'{pct(f.pct_hog_jefa)} de sus hogares tiene jefatura femenina '
        f'({_lugar_corto(pj)}) y {pct(f.pct_mujeres_inactivas)} de las mujeres de 12 años y '
        f'más está fuera del mercado laboral ({_lugar_corto(pi)}).',
        fuente=FTE_CENSO, nivel='Alcaldía', destacado=_extremo(pj) or _extremo(pi),
        advertencia='«Fuera del mercado laboral» incluye a estudiantes y jubiladas.'))

    # --- Peso en la ciudad ------------------------------------------------------
    total = ctx['mujeres_15a59']
    H.append(hallazgo(
        'poblacion', 'Cuántas mujeres viven aquí',
        f'Viven en {nombre} {ent(f.mujeres_15a59)} mujeres de 15 a 59 años, '
        f'{pct(f.mujeres_15a59 / total * 100)} de las de toda la ciudad.',
        fuente=FTE_CENSO, nivel='Alcaldía'))

    # Primero lo que destaca; dentro de cada grupo, el orden de arriba.
    return sorted(H, key=lambda h: not h['destacado'])


def _lugar_texto(p, sustantivo='presión'):
    lugar, de = p['lugar'], p['de']
    if lugar == 1:
        return f'la mayor {sustantivo} de la ciudad'
    if lugar == de:
        return f'la menor {sustantivo} de la ciudad'
    return f'el {lugar}.º lugar de {de} en {sustantivo}'


def _lugar_corto(p):
    return f'{p["lugar"]}.º lugar de {p["de"]}'


def _extremo(p, k=2):
    """True si la alcaldía está entre las k primeras o las k últimas del indicador."""
    lugar, de = p['lugar'], p['de']
    return lugar is not None and (lugar <= k or lugar > de - k)


def hallazgos_alcaldias(repo):
    """Hallazgos de la comparación entre las 16 alcaldías."""
    alc = repo.tabla('resumen_alcaldia')
    H = []

    orden = alc.sort_values('agebs_sin_respaldo', ascending=False)
    total = int(alc['agebs_sin_respaldo'].sum())
    if total:
        primera = orden.iloc[0]
        siguientes = orden.iloc[1:3]
        suma3 = int(orden['agebs_sin_respaldo'].iloc[:3].sum())
        H.append(hallazgo(
            'alc_concentracion', 'Dónde se concentran las zonas sin respaldo',
            f'{primera.alcaldia} concentra {int(primera.agebs_sin_respaldo)} de las {total} AGEB '
            f'de alta carga sin respaldo a 1 km ({pct(primera.agebs_sin_respaldo / total * 100, 0)}). '
            f'Con {lista(f"{r.alcaldia} ({int(r.agebs_sin_respaldo)})" for r in siguientes.itertuples())} '
            f'suman {suma3}: {pct(suma3 / total * 100, 0)} del total.',
            fuente=FTE_CRUCE, nivel='Alcaldía', destacado=True, exploratorio=True,
            advertencia=AVISO_EXPLORATORIO))

        con = alc[alc['agebs_sin_respaldo'] > 0]
        sin_alta = alc[alc['agebs_alta_carga'] == 0]
        cubiertas = alc[(alc['agebs_sin_respaldo'] == 0) & (alc['agebs_alta_carga'] > 0)]
        partes = [f'{len(con)} de las 16 alcaldías tienen al menos una AGEB de alta carga sin '
                  f'respaldo cercano.']
        if len(cubiertas):
            partes.append(f'En {len(cubiertas)}, todas sus zonas de alta carga tienen algún '
                          f'servicio a menos de 1 km')
            if len(sin_alta):
                partes[-1] += (f', y en {lista(sin_alta["alcaldia"])} no hay zonas de alta '
                               f'carga.')
            else:
                partes[-1] += '.'
        H.append(hallazgo(
            'alc_extension', 'Un problema localizado',
            ' '.join(partes), fuente=FTE_CRUCE, nivel='Alcaldía', exploratorio=True,
            advertencia=AVISO_EXPLORATORIO))

    g = alc.dropna(subset=['ninos_0a5_por_guarderia']).sort_values('ninos_0a5_por_guarderia')
    if len(g) >= 2:
        menor, mayor = g.iloc[0], g.iloc[-1]
        H.append(hallazgo(
            'alc_presion_guarderias', 'La presión sobre las guarderías',
            f'Va de {ent(menor.ninos_0a5_por_guarderia)} niñas y niños de 0 a 5 años por guardería '
            f'en {menor.alcaldia} a {ent(mayor.ninos_0a5_por_guarderia)} en {mayor.alcaldia}: '
            f'{veces(mayor.ninos_0a5_por_guarderia, menor.ninos_0a5_por_guarderia)} veces más.',
            fuente=FTE_CRUCE, nivel='Alcaldía', destacado=True, advertencia=AVISO_PRESION))

    mc = alc['carga_directa_x100_mujeres'].median()
    mg = alc['ninos_0a5_por_guarderia'].median()
    doble = alc[(alc['carga_directa_x100_mujeres'] > mc) & (alc['ninos_0a5_por_guarderia'] > mg)]
    doble = doble.sort_values('carga_directa_x100_mujeres', ascending=False)
    if len(doble):
        H.append(hallazgo(
            'alc_doble_presion', 'Doble presión: mucha carga y poca oferta',
            f'{len(doble)} alcaldías tienen a la vez una carga de cuidado y una presión sobre las '
            f'guarderías por encima de la mediana de las alcaldías: {lista(doble["alcaldia"])}.',
            fuente=FTE_CRUCE, nivel='Alcaldía', destacado=True, advertencia=AVISO_PRESION))

    m = alc.dropna(subset=['mayores_60_por_establecimiento'])
    if len(m):
        top = m.sort_values('mayores_60_por_establecimiento', ascending=False).iloc[0]
        H.append(hallazgo(
            'alc_mayores', 'El cuidado de las personas mayores',
            f'{top.alcaldia} tiene la mayor presión sobre el cuidado de personas mayores: '
            f'{ent(top.mayores_60_por_establecimiento)} personas de 60 años o más por cada '
            f'residencia, asilo o centro de día, con {pct(top.pct_60mas)} de su población en '
            f'ese grupo de edad.',
            fuente=FTE_CRUCE, nivel='Alcaldía', advertencia=AVISO_PRESION))
    return H
