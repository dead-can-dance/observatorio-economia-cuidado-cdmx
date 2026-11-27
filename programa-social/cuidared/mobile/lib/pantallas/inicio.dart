import 'package:flutter/material.dart';

import '../modelos.dart';
import '../sesion.dart';
import '../tema.dart';
import 'acceso.dart';

const _descripciones = {
  'necesita_cuidado': 'Para mí o para alguien a quien cuido',
  'puede_cuidar': 'Ofrezco mi tiempo y recibo un pago justo',
  'organizacion': 'Financio o coordino cuidado en una zona',
};

const _iconos = {
  'necesita_cuidado': Icons.favorite_rounded,
  'puede_cuidar': Icons.volunteer_activism_rounded,
  'organizacion': Icons.handshake_rounded,
};

/// Pantalla 1 del diseño: bienvenida y elección de perfil. Tocar una opción lleva al registro.
class PantallaInicio extends StatefulWidget {
  final Sesion sesion;
  const PantallaInicio({super.key, required this.sesion});

  @override
  State<PantallaInicio> createState() => _PantallaInicioState();
}

class _PantallaInicioState extends State<PantallaInicio> {
  bool _enAcceso = false;
  bool _registro = true;
  String _perfil = 'necesita_cuidado';

  void _ir({required bool registro, String? perfil}) => setState(() {
        _enAcceso = true;
        _registro = registro;
        if (perfil != null) _perfil = perfil;
      });

  @override
  Widget build(BuildContext context) {
    if (_enAcceso) {
      return PantallaAcceso(
        key: ValueKey('$_registro$_perfil'),
        sesion: widget.sesion,
        registroInicial: _registro,
        perfilInicial: _perfil,
        alVolver: () => setState(() => _enAcceso = false),
      );
    }
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(gradient: degradadoMarca),
        child: Stack(children: [
          Positioned(
              right: -80,
              top: -60,
              child: Container(
                  width: 260,
                  height: 260,
                  decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.08), shape: BoxShape.circle))),
          Positioned(
              left: -90,
              bottom: 120,
              child: Container(
                  width: 240,
                  height: 240,
                  decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.07), shape: BoxShape.circle))),
          SafeArea(
            child: ListView(padding: const EdgeInsets.fromLTRB(24, 20, 24, 28), children: [
              Row(children: [
                Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.2), shape: BoxShape.circle),
                  child: const Icon(Icons.diversity_1, color: Colors.white),
                ),
                const SizedBox(width: 10),
                const Text('CuidaRed', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w800, color: Colors.white)),
                const Spacer(),
                const Text('Prototipo', style: TextStyle(color: Colors.white70, fontSize: 12)),
              ]),
              const SizedBox(height: 36),
              const Text('Cuidar también es trabajo',
                  style: TextStyle(fontSize: 40, fontWeight: FontWeight.w800, height: 1.05, color: Colors.white)),
              const SizedBox(height: 16),
              const Text(
                'Reconocemos y pagamos el cuidado que hoy se hace sin remuneración, entre personas de la misma zona.',
                style: TextStyle(fontSize: 16, color: Colors.white70, height: 1.45),
              ),
              const SizedBox(height: 30),
              for (final e in perfiles.entries) ...[
                _OpcionPerfil(
                  icono: _iconos[e.key]!,
                  titulo: e.value,
                  detalle: _descripciones[e.key]!,
                  destacada: e.key == 'necesita_cuidado',
                  alTocar: () => _ir(registro: true, perfil: e.key),
                ),
                const SizedBox(height: 12),
              ],
              const SizedBox(height: 4),
              Center(
                child: TextButton(
                  style: TextButton.styleFrom(foregroundColor: Colors.white),
                  onPressed: () => _ir(registro: false),
                  child: const Text('Ya tengo cuenta · Iniciar sesión', style: TextStyle(fontWeight: FontWeight.w700)),
                ),
              ),
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.14),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: Colors.white.withValues(alpha: 0.25))),
                child: const Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Icon(Icons.lock_rounded, color: Colors.white, size: 18),
                  SizedBox(width: 10),
                  Expanded(
                    child: Text.rich(
                      TextSpan(children: [
                        TextSpan(text: 'Tus datos, bajo control. ', style: TextStyle(fontWeight: FontWeight.w800)),
                        TextSpan(
                            text: 'Compartimos solo lo necesario para encontrar coincidencias. '
                                'Nunca mostramos tu dirección exacta.'),
                      ]),
                      style: TextStyle(fontSize: 13, height: 1.4, color: Colors.white),
                    ),
                  ),
                ]),
              ),
            ]),
          ),
        ]),
      ),
    );
  }
}

class _OpcionPerfil extends StatelessWidget {
  final IconData icono;
  final String titulo;
  final String detalle;
  final bool destacada;
  final VoidCallback alTocar;
  const _OpcionPerfil(
      {required this.icono, required this.titulo, required this.detalle, required this.destacada, required this.alTocar});

  @override
  Widget build(BuildContext context) => Semantics(
        button: true,
        label: titulo,
        child: InkWell(
          borderRadius: BorderRadius.circular(22),
          onTap: alTocar,
          child: Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: destacada ? Colors.white : Colors.white.withValues(alpha: 0.14),
              borderRadius: BorderRadius.circular(22),
              border: Border.all(color: destacada ? Colors.transparent : Colors.white.withValues(alpha: 0.28)),
              boxShadow: destacada
                  ? [BoxShadow(color: Colors.black.withValues(alpha: 0.18), blurRadius: 20, offset: const Offset(0, 10))]
                  : null,
            ),
            child: Row(children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                    color: destacada ? Colores.menta : Colors.white.withValues(alpha: 0.2), shape: BoxShape.circle),
                child: Icon(icono, color: destacada ? Colores.verde : Colors.white),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(titulo,
                      style: TextStyle(
                          fontSize: 17, fontWeight: FontWeight.w800, color: destacada ? Colores.tinta : Colors.white)),
                  const SizedBox(height: 2),
                  Text(detalle, style: TextStyle(fontSize: 13, color: destacada ? Colores.apagado : Colors.white70)),
                ]),
              ),
              Icon(Icons.arrow_forward_rounded, color: destacada ? Colores.verde : Colors.white),
            ]),
          ),
        ),
      );
}
