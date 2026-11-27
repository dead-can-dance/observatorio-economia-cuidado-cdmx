import 'package:flutter/foundation.dart';

import 'api.dart';
import 'modelos.dart';

class Sesion extends ChangeNotifier {
  final ApiCliente api = ApiCliente();
  Usuario? usuario;
  bool cargando = true;

  /// Al abrir la app: si hay token guardado, intenta recuperar la sesión.
  Future<void> iniciar() async {
    await api.cargarToken();
    if (api.hayToken) {
      try {
        usuario = await api.yo();
      } catch (_) {
        await api.cerrarSesion();
      }
    }
    cargando = false;
    notifyListeners();
  }

  Future<void> entrar(String email, String password) async {
    await api.login(email, password);
    usuario = await api.yo();
    notifyListeners();
  }

  Future<void> registrar({
    required String email,
    required String password,
    required String nombre,
    required String perfil,
    String? ageb,
  }) async {
    await api.registro(email: email, password: password, nombre: nombre, perfil: perfil, ageb: ageb);
    await entrar(email, password);
  }

  Future<void> salir() async {
    await api.cerrarSesion();
    usuario = null;
    notifyListeners();
  }
}
