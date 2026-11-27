import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import 'config.dart';
import 'modelos.dart';

class ApiError implements Exception {
  final String mensaje;
  ApiError(this.mensaje);
  @override
  String toString() => mensaje;
}

class ApiCliente {
  String? _token;
  static const _clave = 'token';

  bool get hayToken => _token != null;

  Future<void> cargarToken() async {
    final p = await SharedPreferences.getInstance();
    _token = p.getString(_clave);
  }

  Future<void> _guardarToken(String? t) async {
    _token = t;
    final p = await SharedPreferences.getInstance();
    if (t == null) {
      await p.remove(_clave);
    } else {
      await p.setString(_clave, t);
    }
  }

  Map<String, String> get _cabeceras => {
        'Content-Type': 'application/json',
        if (_token != null) 'Authorization': 'Bearer $_token',
      };

  Future<dynamic> _enviar(String metodo, String ruta, {Object? cuerpo}) async {
    final uri = Uri.parse('${ApiConfig.baseUrl}$ruta');
    http.Response r;
    try {
      final c = cuerpo == null ? null : jsonEncode(cuerpo);
      switch (metodo) {
        case 'POST':
          r = await http.post(uri, headers: _cabeceras, body: c);
        default:
          r = await http.get(uri, headers: _cabeceras);
      }
    } catch (_) {
      throw ApiError('No se pudo conectar con el servidor. Revisa tu internet e inténtalo de nuevo.');
    }
    dynamic datos;
    if (r.body.isNotEmpty) {
      try {
        datos = jsonDecode(utf8.decode(r.bodyBytes));
      } catch (_) {
        datos = null;
      }
    }
    if (r.statusCode >= 200 && r.statusCode < 300) return datos;
    throw ApiError(_mensajeError(r.statusCode, datos));
  }

  String _mensajeError(int codigo, dynamic datos) {
    if (codigo == 401) return 'Correo o contraseña incorrectos, o tu sesión expiró.';
    if (codigo == 403) return 'Esta acción no está disponible para tu perfil.';
    if (codigo == 409) return 'Ese correo ya está registrado.';
    if (datos is Map && datos['detail'] is String) return datos['detail'] as String;
    if (codigo == 422) return 'Revisa los datos: hay un campo con formato inválido.';
    return 'Ocurrió un error inesperado ($codigo).';
  }

  Future<void> registro({
    required String email,
    required String password,
    required String nombre,
    required String perfil,
    String? ageb,
  }) async {
    await _enviar('POST', '/auth/registro', cuerpo: {
      'email': email,
      'password': password,
      'nombre': nombre,
      'perfil': perfil,
      if (ageb != null && ageb.isNotEmpty) 'ageb': ageb,
      'acepto_aviso_privacidad': true,
    });
  }

  Future<void> login(String email, String password) async {
    final d = await _enviar('POST', '/auth/login', cuerpo: {'email': email, 'password': password});
    await _guardarToken((d as Map)['access_token'] as String);
  }

  Future<Usuario> yo() async => Usuario.fromJson(await _enviar('GET', '/auth/yo') as Map<String, dynamic>);

  Future<void> cerrarSesion() => _guardarToken(null);

  Future<void> crearServicio({required String tipo, required int min, required int max, String? disponibilidad}) =>
      _enviar('POST', '/servicios', cuerpo: {
        'tipo_cuidado': tipo,
        'tarifa_min': min,
        'tarifa_max': max,
        if (disponibilidad != null && disponibilidad.isNotEmpty) 'disponibilidad': disponibilidad,
      });

  Future<List<Servicio>> misServicios() async =>
      ((await _enviar('GET', '/servicios/mios')) as List).map((e) => Servicio.fromJson(e as Map<String, dynamic>)).toList();

  Future<List<Vinculacion>> recibidas() async =>
      ((await _enviar('GET', '/vinculaciones/recibidas')) as List).map((e) => Vinculacion.fromJson(e as Map<String, dynamic>)).toList();

  Future<List<Vinculacion>> mias() async =>
      ((await _enviar('GET', '/vinculaciones/mias')) as List).map((e) => Vinculacion.fromJson(e as Map<String, dynamic>)).toList();

  Future<void> responder(int id, bool aceptar) =>
      _enviar('POST', '/vinculaciones/$id/responder', cuerpo: {'aceptar': aceptar});

  Future<Solicitud> crearSolicitud({
    required String tipo,
    required int min,
    required int max,
    String? horario,
    String? ageb,
  }) async =>
      Solicitud.fromJson(await _enviar('POST', '/solicitudes', cuerpo: {
        'tipo_cuidado': tipo,
        'presupuesto_min': min,
        'presupuesto_max': max,
        if (horario != null && horario.isNotEmpty) 'horario': horario,
        if (ageb != null && ageb.isNotEmpty) 'ageb': ageb,
      }) as Map<String, dynamic>);

  Future<List<Solicitud>> misSolicitudes() async =>
      ((await _enviar('GET', '/solicitudes/mias')) as List).map((e) => Solicitud.fromJson(e as Map<String, dynamic>)).toList();

  Future<List<Coincidencia>> coincidencias(int solicitudId) async =>
      ((await _enviar('GET', '/solicitudes/$solicitudId/coincidencias')) as List)
          .map((e) => Coincidencia.fromJson(e as Map<String, dynamic>))
          .toList();

  Future<void> decidir(int solicitudId, int servicioId, bool meInteresa) =>
      _enviar('POST', '/solicitudes/$solicitudId/decisiones', cuerpo: {
        'servicio_id': servicioId,
        'decision': meInteresa ? 'me_interesa' : 'pasar',
      });

  Future<Seguimiento> seguimiento(int id) async =>
      Seguimiento.fromJson(await _enviar('GET', '/vinculaciones/$id/seguimiento') as Map<String, dynamic>);

  Future<void> checkin(int id, bool todoBien, {String? nota}) => _enviar('POST', '/vinculaciones/$id/checkin',
      cuerpo: {'todo_bien': todoBien, if (nota != null && nota.isNotEmpty) 'nota': nota});

  Future<void> evaluar(int id, int puntuacion, {String? comentario}) =>
      _enviar('POST', '/vinculaciones/$id/evaluacion',
          cuerpo: {'puntuacion': puntuacion, if (comentario != null && comentario.isNotEmpty) 'comentario': comentario});

  Future<HorasInfo> horas(int id) async =>
      HorasInfo.fromJson(await _enviar('GET', '/vinculaciones/$id/horas') as Map<String, dynamic>);

  Future<HorasInfo> registrarHoras(int id, DateTime fecha, int horas) async {
    final f = '${fecha.year.toString().padLeft(4, '0')}-${fecha.month.toString().padLeft(2, '0')}-${fecha.day.toString().padLeft(2, '0')}';
    return HorasInfo.fromJson(
        await _enviar('POST', '/vinculaciones/$id/horas', cuerpo: {'fecha': f, 'horas': horas}) as Map<String, dynamic>);
  }

  Future<HorasInfo> confirmarHoras(int id) async =>
      HorasInfo.fromJson(await _enviar('POST', '/vinculaciones/$id/horas/confirmar') as Map<String, dynamic>);
}
