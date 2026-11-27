import 'package:flutter/material.dart';

import 'modelos.dart';
import 'tema.dart';
import 'widgets.dart';

String _textoCriterio(Criterio c) {
  switch (c.estado) {
    case 'coincide':
      return c.nombre == 'Precio' ? 'En tu presupuesto' : 'Coincide';
    case 'parcial':
      return 'Parcial';
    case 'no_coincide':
      return 'No coincide';
    default:
      return 'Sin dato';
  }
}

/// Dibuja un "retrato" ilustrado (silueta y círculos) sobre el degradado. No usamos fotos reales.
class _PintorRetrato extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final suave = Paint()..color = Colors.white.withValues(alpha: 0.12);
    canvas.drawCircle(Offset(size.width * 0.85, size.height * 0.15), size.height * 0.32, suave);
    canvas.drawCircle(Offset(size.width * 0.05, size.height * 0.75), size.height * 0.25, suave);
    final silueta = Paint()..color = Colors.white.withValues(alpha: 0.30);
    canvas.drawCircle(Offset(size.width / 2, size.height * 0.40), size.height * 0.17, silueta);
    canvas.drawOval(
        Rect.fromCenter(center: Offset(size.width / 2, size.height * 0.98), width: size.width * 0.58, height: size.height * 0.62),
        silueta);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class TarjetaPerfil extends StatelessWidget {
  final Coincidencia c;
  const TarjetaPerfil({super.key, required this.c});

  String get _ubicacion {
    for (final k in c.criterios) {
      if (k.nombre == 'Zona') {
        if (k.estado == 'coincide') return 'Vive en tu zona';
        if (k.estado == 'parcial') return 'Vive en tu alcaldía';
      }
    }
    return 'Zona sin especificar';
  }

  @override
  Widget build(BuildContext context) => Container(
        clipBehavior: Clip.antiAlias,
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(28),
          boxShadow: [BoxShadow(color: Colores.verdeProfundo.withValues(alpha: 0.2), blurRadius: 30, offset: const Offset(0, 16))],
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          _retrato(),
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 18, 20, 12),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(crossAxisAlignment: CrossAxisAlignment.end, children: [
                Text(
                  c.tarifaMin == c.tarifaMax ? '\$${c.tarifaMin}' : '\$${c.tarifaMin}–\$${c.tarifaMax}',
                  style: const TextStyle(fontSize: 30, fontWeight: FontWeight.w800, color: Colores.tinta, height: 1),
                ),
                const SizedBox(width: 6),
                const Padding(padding: EdgeInsets.only(bottom: 3), child: Text('por hora', style: estiloPequeno)),
              ]),
              const SizedBox(height: 10),
              Wrap(spacing: 8, runSpacing: 8, children: [
                if (c.disponibilidad != null && c.disponibilidad!.isNotEmpty)
                  Etiqueta(c.disponibilidad!, icono: Icons.schedule_rounded),
                if (c.zonaPrioritaria)
                  const Etiqueta('Zona prioritaria', fondo: Colores.ambar, color: Colores.tinta, icono: Icons.star_rounded),
              ]),
              const SizedBox(height: 16),
              const Text('Por qué coincide', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w800)),
              const SizedBox(height: 4),
              for (final k in c.criterios) _FilaCriterio(k),
            ]),
          ),
        ]),
      );

  Widget _retrato() => SizedBox(
        height: 250,
        child: Stack(children: [
          Positioned.fill(child: DecoratedBox(decoration: BoxDecoration(gradient: degradadoPara(c.nombre)))),
          Positioned.fill(child: CustomPaint(painter: _PintorRetrato())),
          Align(
            alignment: Alignment.bottomCenter,
            child: Container(
              height: 120,
              decoration: BoxDecoration(
                gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [Colors.transparent, Colors.black.withValues(alpha: 0.55)]),
              ),
            ),
          ),
          Positioned(
            left: 16,
            top: 16,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
              decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.22), borderRadius: BorderRadius.circular(20)),
              child: Row(mainAxisSize: MainAxisSize.min, children: [
                Icon(iconoTipo(c.tipoCuidado), size: 16, color: Colors.white),
                const SizedBox(width: 6),
                Text(etiquetaTipo(c.tipoCuidado),
                    style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 13)),
              ]),
            ),
          ),
          Positioned(
            right: 14,
            top: 12,
            child: Tooltip(
              message: 'Compatibilidad',
              child: Container(
                width: 58,
                height: 58,
                decoration: BoxDecoration(color: Colors.black.withValues(alpha: 0.18), shape: BoxShape.circle),
                child: Stack(alignment: Alignment.center, children: [
                  SizedBox(
                    width: 46,
                    height: 46,
                    child: CircularProgressIndicator(
                        value: c.puntaje / 100, strokeWidth: 4.5, color: Colors.white, backgroundColor: Colors.white24),
                  ),
                  Text('${c.puntaje}%',
                      style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 13)),
                ]),
              ),
            ),
          ),
          Positioned(
            left: 20,
            right: 20,
            bottom: 16,
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(c.nombre, style: const TextStyle(fontSize: 28, fontWeight: FontWeight.w800, color: Colors.white)),
              const SizedBox(height: 2),
              Row(children: [
                const Icon(Icons.place_rounded, size: 16, color: Colors.white70),
                const SizedBox(width: 4),
                Text(_ubicacion, style: const TextStyle(color: Colors.white70, fontSize: 14)),
              ]),
            ]),
          ),
        ]),
      );
}

class _FilaCriterio extends StatelessWidget {
  final Criterio k;
  const _FilaCriterio(this.k);

  @override
  Widget build(BuildContext context) {
    IconData icono;
    Color colorIcono;
    switch (k.estado) {
      case 'coincide':
        icono = Icons.check_circle_rounded;
        colorIcono = Colores.verde;
      case 'parcial':
        icono = Icons.info_rounded;
        colorIcono = const Color(0xFFE0A100);
      case 'no_coincide':
        icono = Icons.cancel_rounded;
        colorIcono = Colores.coral;
      default:
        icono = Icons.help_rounded;
        colorIcono = Colores.apagado;
    }
    final bueno = k.estado == 'coincide';
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 7),
      child: Row(children: [
        Icon(icono, size: 20, color: colorIcono),
        const SizedBox(width: 10),
        Expanded(child: Text(k.nombre, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500))),
        Etiqueta(
          _textoCriterio(k),
          fondo: bueno ? Colores.menta : (k.estado == 'sin_dato' ? Colores.fondo : Colores.ambar),
          color: bueno ? Colores.verde : Colores.tinta,
        ),
      ]),
    );
  }
}

class _Sello extends StatelessWidget {
  final String texto;
  final Color color;
  const _Sello(this.texto, this.color);

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
        decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.9),
            border: Border.all(color: color, width: 4),
            borderRadius: BorderRadius.circular(12)),
        child: Text(texto, style: TextStyle(color: color, fontSize: 24, fontWeight: FontWeight.w900, letterSpacing: 1)),
      );
}

/// Tarjeta que se arrastra: derecha = me interesa, izquierda = pasar. Vuela fuera de la pantalla al decidir.
class TarjetaDeslizable extends StatefulWidget {
  final Widget hijo;
  final Future<void> Function(bool) alDecidir;
  const TarjetaDeslizable({super.key, required this.hijo, required this.alDecidir});

  @override
  State<TarjetaDeslizable> createState() => TarjetaDeslizableState();
}

class TarjetaDeslizableState extends State<TarjetaDeslizable> with SingleTickerProviderStateMixin {
  static const _umbral = 110.0;
  late final AnimationController _ctrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 260));
  double _dx = 0;
  double _desde = 0;
  double _dir = 1;
  bool _volando = false;

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  /// También se llama desde los botones redondos "Pasar" y "Me interesa".
  Future<void> deslizar(bool derecha) async {
    if (_volando) return;
    _volando = true;
    _dir = derecha ? 1 : -1;
    _desde = _dx;
    await _ctrl.forward(from: 0);
    if (!mounted) return;
    await widget.alDecidir(derecha);
    if (!mounted) return;
    setState(() {
      _dx = 0;
      _volando = false;
    });
    _ctrl.reset();
  }

  @override
  Widget build(BuildContext context) => AnimatedBuilder(
        animation: _ctrl,
        builder: (context, _) {
          final t = Curves.easeIn.transform(_ctrl.value);
          final dx = _volando ? _desde + (_dir * 520 - _desde) * t : _dx;
          final opacidad = _volando ? (1 - t).clamp(0.0, 1.0) : 1.0;
          final fuerza = (dx.abs() / _umbral).clamp(0.0, 1.0);
          return GestureDetector(
            onPanUpdate: (d) {
              if (!_volando) setState(() => _dx += d.delta.dx);
            },
            onPanEnd: (_) {
              if (_volando) return;
              if (_dx.abs() >= _umbral) {
                deslizar(_dx > 0);
              } else {
                setState(() => _dx = 0);
              }
            },
            child: Opacity(
              opacity: opacidad,
              child: Transform.translate(
                offset: Offset(dx, 0),
                child: Transform.rotate(
                  angle: dx / 1400,
                  child: Stack(children: [
                    widget.hijo,
                    if (dx.abs() > 16)
                      Positioned(
                        top: 70,
                        left: dx > 0 ? 20 : null,
                        right: dx < 0 ? 20 : null,
                        child: Opacity(
                          opacity: fuerza,
                          child: Transform.rotate(
                            angle: dx > 0 ? -0.22 : 0.22,
                            child: dx > 0 ? const _Sello('ME INTERESA', Colores.verde) : const _Sello('PASAR', Colores.coral),
                          ),
                        ),
                      ),
                  ]),
                ),
              ),
            ),
          );
        },
      );
}
