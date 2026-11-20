const Map<String, String> tiposCuidado = {
  'acompanamiento': 'Acompañamiento',
  'apoyo_hogar': 'Apoyo en el hogar',
  'comidas': 'Preparación de comidas',
  'traslados': 'Traslados',
  'cuidado_nocturno': 'Cuidado nocturno',
};

const Map<String, String> perfiles = {
  'necesita_cuidado': 'Necesito cuidado',
  'puede_cuidar': 'Puedo cuidar',
  'organizacion': 'Soy aliado u organización',
};

const List<String> franjas = ['Mañana', 'Tarde', 'Noche', 'Fines de semana'];

/// Alcaldías de la CDMX con su clave INEGI (entidad 09 + 3 dígitos). La zona se guarda con esta clave.
const Map<String, String> alcaldias = {
  '09002': 'Azcapotzalco',
  '09003': 'Coyoacán',
  '09004': 'Cuajimalpa de Morelos',
  '09005': 'Gustavo A. Madero',
  '09006': 'Iztacalco',
  '09007': 'Iztapalapa',
  '09008': 'La Magdalena Contreras',
  '09009': 'Milpa Alta',
  '09010': 'Álvaro Obregón',
  '09011': 'Tláhuac',
  '09012': 'Tlalpan',
  '09013': 'Xochimilco',
  '09014': 'Benito Juárez',
  '09015': 'Cuauhtémoc',
  '09016': 'Miguel Hidalgo',
  '09017': 'Venustiano Carranza',
};

/// Clave de alcaldía (5 primeros caracteres de la AGEB) si es una conocida.
String? claveAlcaldia(String? ageb) {
  if (ageb == null || ageb.length < 5) return null;
  final c = ageb.substring(0, 5);
  return alcaldias.containsKey(c) ? c : null;
}

String etiquetaTipo(String clave) => tiposCuidado[clave] ?? clave;

String formatoRango(int min, int max) =>
    min == max ? '\$$min por hora' : '\$$min–\$$max por hora';

class Usuario {
  final int id;
  final String email;
  final String nombre;
  final String perfil;
  final String? ageb;
  Usuario({required this.id, required this.email, required this.nombre, required this.perfil, this.ageb});
  bool get esCuidadora => perfil != 'necesita_cuidado';
  factory Usuario.fromJson(Map<String, dynamic> j) => Usuario(
        id: j['id'] as int,
        email: j['email'] as String,
        nombre: j['nombre'] as String,
        perfil: j['perfil'] as String,
        ageb: j['ageb'] as String?,
      );
}

class Servicio {
  final int id;
  final String tipoCuidado;
  final int tarifaMin;
  final int tarifaMax;
  final String? disponibilidad;
  Servicio({required this.id, required this.tipoCuidado, required this.tarifaMin, required this.tarifaMax, this.disponibilidad});
  factory Servicio.fromJson(Map<String, dynamic> j) => Servicio(
        id: j['id'] as int,
        tipoCuidado: j['tipo_cuidado'] as String,
        tarifaMin: j['tarifa_min'] as int,
        tarifaMax: j['tarifa_max'] as int,
        disponibilidad: j['disponibilidad'] as String?,
      );
}

class Solicitud {
  final int id;
  final String tipoCuidado;
  final String? horario;
  final String? ageb;
  final int presupuestoMin;
  final int presupuestoMax;
  Solicitud({required this.id, required this.tipoCuidado, this.horario, this.ageb, required this.presupuestoMin, required this.presupuestoMax});
  factory Solicitud.fromJson(Map<String, dynamic> j) => Solicitud(
        id: j['id'] as int,
        tipoCuidado: j['tipo_cuidado'] as String,
        horario: j['horario'] as String?,
        ageb: j['ageb'] as String?,
        presupuestoMin: j['presupuesto_min'] as int,
        presupuestoMax: j['presupuesto_max'] as int,
      );
}

class Criterio {
  final String nombre;
  final String estado;
  Criterio({required this.nombre, required this.estado});
  factory Criterio.fromJson(Map<String, dynamic> j) =>
      Criterio(nombre: j['nombre'] as String, estado: j['estado'] as String);
}

class Coincidencia {
  final int servicioId;
  final String nombre;
  final String tipoCuidado;
  final int tarifaMin;
  final int tarifaMax;
  final String? disponibilidad;
  final int puntaje;
  final bool zonaPrioritaria;
  final List<Criterio> criterios;
  Coincidencia({
    required this.servicioId,
    required this.nombre,
    required this.tipoCuidado,
    required this.tarifaMin,
    required this.tarifaMax,
    this.disponibilidad,
    required this.puntaje,
    required this.zonaPrioritaria,
    required this.criterios,
  });
  factory Coincidencia.fromJson(Map<String, dynamic> j) => Coincidencia(
        servicioId: j['servicio_id'] as int,
        nombre: j['nombre'] as String,
        tipoCuidado: j['tipo_cuidado'] as String,
        tarifaMin: j['tarifa_min'] as int,
        tarifaMax: j['tarifa_max'] as int,
        disponibilidad: j['disponibilidad'] as String?,
        puntaje: j['puntaje'] as int,
        zonaPrioritaria: j['zona_prioritaria'] as bool,
        criterios: (j['criterios'] as List).map((e) => Criterio.fromJson(e as Map<String, dynamic>)).toList(),
      );
}

class Vinculacion {
  final int id;
  final String estado;
  final String tipoCuidado;
  final String? horario;
  final int presupuestoMin;
  final int presupuestoMax;
  final int tarifaMin;
  final int tarifaMax;
  final String otraPersona;
  final String? contacto;
  Vinculacion({
    required this.id,
    required this.estado,
    required this.tipoCuidado,
    this.horario,
    required this.presupuestoMin,
    required this.presupuestoMax,
    required this.tarifaMin,
    required this.tarifaMax,
    required this.otraPersona,
    this.contacto,
  });
  factory Vinculacion.fromJson(Map<String, dynamic> j) => Vinculacion(
        id: j['id'] as int,
        estado: j['estado'] as String,
        tipoCuidado: j['tipo_cuidado'] as String,
        horario: j['horario'] as String?,
        presupuestoMin: j['presupuesto_min'] as int,
        presupuestoMax: j['presupuesto_max'] as int,
        tarifaMin: j['tarifa_min'] as int,
        tarifaMax: j['tarifa_max'] as int,
        otraPersona: j['otra_persona'] as String,
        contacto: j['contacto'] as String?,
      );
}

class PasoSeguimiento {
  final String clave;
  final String titulo;
  final String detalle;
  final String estado; // hecho | actual | pendiente
  PasoSeguimiento({required this.clave, required this.titulo, required this.detalle, required this.estado});
  factory PasoSeguimiento.fromJson(Map<String, dynamic> j) => PasoSeguimiento(
        clave: j['clave'] as String,
        titulo: j['titulo'] as String,
        detalle: j['detalle'] as String,
        estado: j['estado'] as String,
      );
}

class Seguimiento {
  final String otraPersona;
  final String estadoVinculacion;
  final List<PasoSeguimiento> pasos;
  final String avisoSeguridad;
  Seguimiento({required this.otraPersona, required this.estadoVinculacion, required this.pasos, required this.avisoSeguridad});
  factory Seguimiento.fromJson(Map<String, dynamic> j) => Seguimiento(
        otraPersona: j['otra_persona'] as String,
        estadoVinculacion: j['estado_vinculacion'] as String,
        pasos: (j['pasos'] as List).map((e) => PasoSeguimiento.fromJson(e as Map<String, dynamic>)).toList(),
        avisoSeguridad: j['aviso_seguridad'] as String,
      );
}

class HoraRegistro {
  final int id;
  final DateTime fecha;
  final int horas;
  final bool confirmada;
  HoraRegistro({required this.id, required this.fecha, required this.horas, required this.confirmada});
  factory HoraRegistro.fromJson(Map<String, dynamic> j) => HoraRegistro(
        id: j['id'] as int,
        fecha: DateTime.parse(j['fecha'] as String),
        horas: j['horas'] as int,
        confirmada: j['confirmada'] as bool,
      );
}

class HorasInfo {
  final List<HoraRegistro> registros;
  final int totalHoras;
  final int tarifaAcordada;
  final int totalAPagar;
  final String quienPaga;
  final String estadoPago; // sin_horas | por_confirmar | pagado_simulado
  HorasInfo({
    required this.registros,
    required this.totalHoras,
    required this.tarifaAcordada,
    required this.totalAPagar,
    required this.quienPaga,
    required this.estadoPago,
  });
  factory HorasInfo.fromJson(Map<String, dynamic> j) => HorasInfo(
        registros: (j['registros'] as List).map((e) => HoraRegistro.fromJson(e as Map<String, dynamic>)).toList(),
        totalHoras: j['total_horas'] as int,
        tarifaAcordada: j['tarifa_acordada'] as int,
        totalAPagar: j['total_a_pagar'] as int,
        quienPaga: j['quien_paga'] as String,
        estadoPago: j['estado_pago'] as String,
      );
}
