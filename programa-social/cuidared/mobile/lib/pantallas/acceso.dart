import 'package:flutter/material.dart';

import '../modelos.dart';
import '../sesion.dart';
import '../tema.dart';
import '../widgets.dart';

class PantallaAcceso extends StatefulWidget {
  final Sesion sesion;
  final bool registroInicial;
  final String perfilInicial;
  final VoidCallback alVolver;
  const PantallaAcceso({
    super.key,
    required this.sesion,
    required this.registroInicial,
    required this.perfilInicial,
    required this.alVolver,
  });

  @override
  State<PantallaAcceso> createState() => _PantallaAccesoState();
}

class _PantallaAccesoState extends State<PantallaAcceso> {
  final _email = TextEditingController();
  final _password = TextEditingController();
  final _nombre = TextEditingController();
  late bool _registro = widget.registroInicial;
  late final String _perfil = widget.perfilInicial;
  String? _zona;
  bool _acepto = false;
  bool _ocupado = false;
  String? _error;

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    _nombre.dispose();
    super.dispose();
  }

  Future<void> _avisoPrivacidad() => showDialog<void>(
        context: context,
        builder: (_) => AlertDialog(
          title: const Text('Aviso de privacidad (borrador)'),
          content: const Text(
              'Este es un prototipo académico. Guardamos tu correo, nombre y zona para vincularte con otras personas. '
              'Tu correo solo se comparte cuando ambas partes aceptan. Usa únicamente datos de ejemplo.'),
          actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cerrar'))],
        ),
      );

  Future<void> _enviar() async {
    setState(() {
      _error = null;
      _ocupado = true;
    });
    try {
      if (_registro) {
        if (_nombre.text.trim().isEmpty) throw 'Escribe tu nombre.';
        if (!_acepto) throw 'Debes aceptar el aviso de privacidad.';
        await widget.sesion.registrar(
          email: _email.text.trim(),
          password: _password.text,
          nombre: _nombre.text.trim(),
          perfil: _perfil,
          ageb: _zona,
        );
      } else {
        await widget.sesion.entrar(_email.text.trim(), _password.text);
      }
    } catch (e) {
      if (mounted) setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _ocupado = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        body: Column(children: [
          Container(
            width: double.infinity,
            decoration: const BoxDecoration(
              gradient: degradadoMarca,
              borderRadius: BorderRadius.vertical(bottom: Radius.circular(32)),
            ),
            child: SafeArea(
              bottom: false,
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Encabezado(alVolver: widget.alVolver, claro: true),
                Padding(
                  padding: const EdgeInsets.fromLTRB(24, 12, 24, 28),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text(_registro ? 'Crea tu cuenta' : 'Bienvenida de vuelta',
                        style: const TextStyle(fontSize: 32, fontWeight: FontWeight.w800, color: Colors.white)),
                    const SizedBox(height: 4),
                    Text(_registro ? 'Perfil: ${perfiles[_perfil]}' : 'Entra para ver tus coincidencias',
                        style: const TextStyle(fontSize: 15, color: Colors.white70)),
                  ]),
                ),
              ]),
            ),
          ),
          Expanded(
            child: ListView(padding: const EdgeInsets.fromLTRB(24, 22, 24, 24), children: [
              if (_registro) ...[
                TextField(
                    controller: _nombre,
                    decoration: const InputDecoration(labelText: 'Nombre', prefixIcon: Icon(Icons.person_rounded))),
                const SizedBox(height: 12),
              ],
              TextField(
                  controller: _email,
                  keyboardType: TextInputType.emailAddress,
                  decoration: const InputDecoration(labelText: 'Correo electrónico', prefixIcon: Icon(Icons.mail_rounded))),
              const SizedBox(height: 12),
              TextField(
                  controller: _password,
                  obscureText: true,
                  decoration: InputDecoration(
                      labelText: 'Contraseña',
                      prefixIcon: const Icon(Icons.lock_rounded),
                      helperText: _registro ? 'Mínimo 8 caracteres' : null)),
              if (_registro) ...[
                const EtiquetaCampo('Zona'),
                SeleccionZona(valor: _zona, alCambiar: (v) => setState(() => _zona = v)),
                const SizedBox(height: 8),
                CheckboxListTile(
                  value: _acepto,
                  onChanged: (v) => setState(() => _acepto = v ?? false),
                  contentPadding: EdgeInsets.zero,
                  controlAffinity: ListTileControlAffinity.leading,
                  title: const Text('Acepto el aviso de privacidad', style: TextStyle(fontSize: 14)),
                  subtitle: GestureDetector(
                      onTap: _avisoPrivacidad,
                      child: const Text('Leer aviso', style: TextStyle(color: Colores.verde, fontWeight: FontWeight.w700))),
                ),
              ],
              const SizedBox(height: 14),
              MensajeError(_error),
              BotonPrincipal(
                texto: _ocupado ? 'Un momento…' : (_registro ? 'Crear cuenta' : 'Entrar'),
                icono: Icons.arrow_forward_rounded,
                alPresionar: _ocupado ? null : _enviar,
              ),
              const SizedBox(height: 8),
              Center(
                child: TextButton(
                  onPressed: () => setState(() {
                    _registro = !_registro;
                    _error = null;
                  }),
                  child: Text(_registro ? 'Ya tengo cuenta' : 'Crear una cuenta'),
                ),
              ),
            ]),
          ),
        ]),
      );
}
