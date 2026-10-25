"""Contenido metodológico del observatorio: fuentes, advertencias y glosario.

Resume docs/diccionario_datos.md y el README. Si cambian esos documentos, este módulo
debe seguirlos: el tablero no debe decir nada que la documentación del equipo no diga.
"""

PREGUNTA_RECTORA = ('¿Dónde y cuánto trabajo de cuidado recae sobre las mujeres de la '
                    'Ciudad de México, y qué tanto lo alivia la oferta de cuidados que '
                    'tienen cerca?')

FUENTES = [
    {
        'clave': 'ENUT 2024',
        'nombre': 'Encuesta Nacional sobre Uso del Tiempo 2024',
        'institucion': 'INEGI',
        'niveles': ['Nacional', 'CDMX'],
        'que_mide': 'Horas a la semana que las personas de 12 años y más dedican al trabajo '
                    'para el mercado, al trabajo doméstico y al cuidado no remunerado.',
        'notas': [
            'Es representativa por entidad federativa. En la CDMX la muestra es de 2,107 '
            'personas de 12 años y más (1,144 mujeres).',
            'Las horas de cuidado excluyen los cuidados pasivos (solo tiempo activo).',
            'Salvo en la doble jornada y en «¿qué mujeres cuidan más?», las horas se '
            'promedian entre quienes realizan la actividad, el método con el que se '
            'reproducen las cifras publicadas por el INEGI.',
        ],
    },
    {
        'clave': 'ENASIC 2022',
        'nombre': 'Encuesta Nacional para el Sistema de Cuidados 2022',
        'institucion': 'INEGI',
        'niveles': ['Nacional'],
        'que_mide': 'Perfil de las personas cuidadoras y su relación con los servicios '
                    'de cuidado: si los buscan, por qué no, qué preferirían.',
        'notas': [
            'Sus microdatos públicos no traen ninguna variable geográfica: todas sus cifras '
            'son nacionales y no se pueden atribuir a la CDMX ni poner en un mapa.',
            'Base: mujeres cuidadoras de 15 años y más, ponderadas con FAC_CUI (4,173 '
            'registros, 23.8 millones de mujeres). Es edición única: no hay serie de tiempo.',
        ],
    },
    {
        'clave': 'Censo 2020',
        'nombre': 'Censo de Población y Vivienda 2020',
        'institucion': 'INEGI',
        'niveles': ['Alcaldía', 'AGEB'],
        'que_mide': 'Población que necesita cuidado directo (0 a 5 años y discapacidad para '
                    'el autocuidado), mujeres en edad de cuidar, hogares con jefatura '
                    'femenina y participación laboral.',
        'notas': [
            'Las celdas reservadas por confidencialidad entran como dato faltante, nunca '
            'como cero.',
            'Las AGEB urbanas no cubren la zona rural: en Milpa Alta queda fuera el 16 % de '
            'la población. Los totales por alcaldía sí son completos.',
        ],
    },
    {
        'clave': 'DENUE 05/2026',
        'nombre': 'Directorio Estadístico Nacional de Unidades Económicas, mayo de 2026',
        'institucion': 'INEGI',
        'niveles': ['Alcaldía', 'AGEB'],
        'que_mide': 'Establecimientos de cuidado de la CDMX con su ubicación: guarderías, '
                    'residencias y asilos, centros de día, comedores comunitarios y otros.',
        'notas': [
            'Es un directorio: dice que un establecimiento existe, no a cuántas personas '
            'puede atender.',
            'De los 1,463 establecimientos de cuidado, 838 cuentan como respaldo (guarderías, '
            'residencias y asilos de personas mayores y centros de día): son los que '
            'sustituyen horas de cuidado en el hogar.',
        ],
    },
]

ADVERTENCIAS = [
    {
        'titulo': 'El DENUE cuenta establecimientos, no lugares disponibles',
        'texto': 'El DENUE registra que un establecimiento existe, no su capacidad. Por eso '
                 'las razones de niñas y niños por guardería o de personas mayores por '
                 'establecimiento miden presión sobre la oferta, no cobertura. Y de los 1,463 '
                 'establecimientos, solo 838 cuentan como respaldo.',
        'no': '«La cobertura de guarderías en Iztapalapa es de X %».',
        'si': '«En Iztapalapa hay N guarderías registradas en el DENUE» o «hay N niñas y '
              'niños de 0 a 5 por cada guardería registrada».',
    },
    {
        'titulo': 'La ENASIC es nacional: no se puede atribuir a la CDMX',
        'texto': 'Los microdatos públicos de la ENASIC 2022 no traen entidad, municipio ni '
                 'tamaño de localidad. Sus cifras describen a las cuidadoras del país.',
        'no': '«61.2 % de las cuidadoras de la CDMX prefiere el cuidado en casa».',
        'si': '«61.2 % de las mujeres cuidadoras del país prefiere el cuidado en casa '
              '(INEGI, ENASIC 2022, nacional)».',
    },
    {
        'titulo': 'Las zonas sin respaldo usan ubicaciones aproximadas',
        'texto': 'Mientras no se integre el Marco Geoestadístico del INEGI, el punto de cada '
                 'AGEB es la mediana de los establecimientos del DENUE que caen dentro, no el '
                 'centroide de su polígono. El hallazgo de las 88 AGEB y 125,256 mujeres es '
                 'exploratorio y puede cambiar al recalcularse.',
        'no': 'Presentar las 88 AGEB como un conteo definitivo.',
        'si': '«De forma exploratoria, 88 AGEB de alta carga no tienen respaldo a 1 km».',
    },
    {
        'titulo': 'Algunas cifras de la ENUT para la CDMX salen de menos de 100 casos',
        'texto': 'Al partir la muestra de la CDMX por sexo y actividad, se adelgaza. Las '
                 'cifras con menos de 100 casos (o grupos con menos de 60) se marcan en el '
                 'tablero y se leen solo como indicio. La bandera es un semáforo por tamaño '
                 'de muestra, no el coeficiente de variación formal.',
        'no': 'Citar como dato las horas de las mujeres desocupadas (4 casos).',
        'si': 'Mostrarlas marcadas como «muestra chica» o no mostrarlas.',
    },
    {
        'titulo': 'La unidad de análisis es la mujer cuidadora',
        'texto': 'Los datos de hombres existen solo para dimensionar la brecha. No encabezan '
                 'ninguna gráfica, título ni conclusión; aparecen en gris y con la etiqueta '
                 '«referencia».',
        'no': 'Una gráfica o un titular sobre los hombres.',
        'si': '«Las mujeres que cuidan dedican 12.2 h, 1.51 veces lo de los hombres '
              '(referencia)».',
    },
]

GLOSARIO = [
    {'termino': 'Trabajo de cuidado no remunerado',
     'definicion': 'Atención directa a integrantes del hogar (niñas y niños, personas '
                   'mayores, personas enfermas o con discapacidad) sin pago a cambio.'},
    {'termino': 'Trabajo no pagado',
     'definicion': 'Suma del trabajo doméstico y del cuidado no remunerado del propio hogar.'},
    {'termino': 'Doble jornada',
     'definicion': 'Trabajo para el mercado más trabajo no pagado de las personas ocupadas.'},
    {'termino': 'Carga de cuidado directo',
     'definicion': 'Niñas y niños de 0 a 5 años más personas con discapacidad para vestirse, '
                   'bañarse o comer, por cada 100 mujeres de 15 a 59 años. No incluye a toda '
                   'la población de 60+, porque la mayoría es autónoma.'},
    {'termino': 'AGEB',
     'definicion': 'Área Geoestadística Básica del INEGI: la unidad territorial más fina del '
                   'análisis, del tamaño de unas cuantas colonias o manzanas.'},
    {'termino': 'AGEB de alta carga',
     'definicion': 'AGEB en el cuartil superior de carga de cuidado de la ciudad (24.1 o más '
                   'personas por cada 100 mujeres). Son 580.'},
    {'termino': 'Respaldo de cuidado',
     'definicion': 'Guarderías, residencias y asilos para personas mayores y centros de día: '
                   'los servicios que sustituyen horas de cuidado en el hogar.'},
    {'termino': 'Zona sin respaldo',
     'definicion': 'AGEB de alta carga sin ningún servicio de respaldo a menos de 1 km '
                   '(unos 12 a 15 minutos a pie). Hallazgo exploratorio.'},
    {'termino': 'Presión sobre la oferta',
     'definicion': 'Población potencialmente demandante por cada establecimiento. No es '
                   'cobertura: el DENUE no publica lugares disponibles.'},
    {'termino': 'Referencia (hombres)',
     'definicion': 'Las cifras de hombres se muestran solo para medir la brecha con las '
                   'mujeres.'},
]

EMBUDO_AGEB = [
    {'etapa': 'AGEB urbanas de la CDMX (Censo 2020)', 'agebs': 2433},
    {'etapa': 'Con al menos 100 mujeres de 15 a 59 y carga calculable', 'agebs': 2326},
    {'etapa': 'Con punto de ubicación (aproximado) para medir distancias', 'agebs': 2320},
]


def contenido():
    return {
        'pregunta_rectora': PREGUNTA_RECTORA,
        'fuentes': FUENTES,
        'advertencias': ADVERTENCIAS,
        'glosario': GLOSARIO,
        'embudo_agebs': EMBUDO_AGEB,
        'documentos': ['README.md', 'docs/diccionario_datos.md'],
    }
