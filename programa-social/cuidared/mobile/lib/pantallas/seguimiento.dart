import 'package:flutter/material.dart';

import '../api.dart';
import '../modelos.dart';
import '../tema.dart';
import '../widgets.dart';

const _dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];

String _fechaCorta(DateTime f) =>
    '${_dias[f.weekday - 1]} ${f.day.toString().padLeft(2, '0')}/${f.month.toString().padLeft(2, '0')}';

/// Pantalla 4 del diseño: línea de tiempo de la vinculación.
class PantallaSeguimiento extends StatefulWidget {
  final ApiCliente api;
  final Vinculacion vinculacion;
  final bool esCuidadora;
  const PantallaSeguimiento({super.key, required this.api, required this.vinculacion, required this.esCuidadora});

  @override
  State<PantallaSeguimiento> createState() => _PantallaSeguimientoState();
}

class _PantallaSeguimientoState extends State<PantallaSeguimiento> {
  late Future<Seguimiento> _futuro;

  @override
  void initState() {
    super.initState();
    _futuro = widget.api.seguimiento(widget.vinculacion.id);
  }

  void _recargar() => setState(() {
        _futuro = widget.api.seguimiento(widget.vinculacion.id);
      });

  Future<void> _checkin(bool todoBien) async {
    String? nota;
    if (!todoBien) {
      final c = TextEditingController();
      final ok = await showDialog<bool>(
        context: context,
        builder: (_) => AlertDialog(
          title: const Text('Reportar un problema'),
          content: TextField(
              controller: c,
              maxLength: 500,
              maxLines: 3,
              decoration: const InputDecoration(hintText: 'Cuéntanos qué pasó')),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancelar')),
            FilledButton(
                style: FilledButton.styleFrom(minimumSize: const Size(100, 44)),
                onPressed: () => Navigator.pop(context, true),
                child: const Text('Enviar')),
          ],
        ),
      );
      nota = c.text.trim();
      c.dispose();
      if (ok != true) return;
    }
    try {
      await widget.api.checkin(widget.vinculacion.id, todoBien, nota: nota);
      if (!mounted) return;
      mostrarMensaje(context, todoBien ? '¡Gracias! Registramos tu check-in.' : 'Recibimos tu reporte.');
      _recargar();
    } catch (e) {
      if (mounted) mostrarMensaje(context, e.toString());
    }
  }

  Future<void> _evaluar() async {
    var puntos = 5;
    final c = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => StatefulBuilder(
        builder: (context, setLocal) => AlertDialog(
          title: const Text('Evalúa tu experiencia'),
          content: Column(mainAxisSize: MainAxisSize.min, children: [
            Row(mainAxisAlignment: MainAxisAlignment.center, children: [
              for (var i = 1; i <= 5; i++)
                IconButton(
                  tooltip: '$i de 5',
                  onPressed: () => setLocal(() => puntos = i),
                  icon: Icon(i <= puntos ? Icons.star : Icons.star_border, color: Colores.verde, size: 32),
                ),
            ]),
            TextField(
                controller: c,
                maxLength: 500,
                maxLines: 3,
                decoration: const InputDecoration(hintText: 'Comentario (opcional)')),
          ]),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancelar')),
            FilledButton(
                style: FilledButton.styleFrom(minimumSize: const Size(100, 44)),
                onPressed: () => Navigator.pop(context, true),
                child: const Text('Enviar')),
          ],
        ),
      ),
    );
    final comentario = c.text.trim();
    c.dispose();
    if (ok != true) return;
    try {
      await widget.api.evaluar(widget.vinculacion.id, puntos, comentario: comentario);
      if (!mounted) return;
      mostrarMensaje(context, 'Gracias por tu evaluación.');
      _recargar();
    } catch (e) {
      if (mounted) mostrarMensaje(context, e.toString());
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        body: SafeArea(
          child: Column(children: [
            Encabezado(alVolver: () => Navigator.of(context).pop()),
            Expanded(
              child: FutureBuilder<Seguimiento>(
                future: _futuro,
                builder: (context, snap) {
                  if (snap.connectionState != ConnectionState.done) {
                    return const Center(child: CircularProgressIndicator());
                  }
                  if (snap.hasError) {
                    return Center(
                        child: Padding(
                            padding: const EdgeInsets.all(24),
                            child: Column(mainAxisSize: MainAxisSize.min, children: [
                              Text(snap.error.toString(), textAlign: TextAlign.center),
                              const SizedBox(height: 12),
                              OutlinedButton(onPressed: _recargar, child: const Text('Reintentar')),
                            ])));
                  }
                  return _Contenido(
                    datos: snap.data!,
                    alHoras: () => Navigator.of(context)
                        .push(MaterialPageRoute<void>(
                            builder: (_) => PantallaHoras(
                                api: widget.api, vinculacion: widget.vinculacion, esCuidadora: widget.esCuidadora)))
                        .then((_) => _recargar()),
                    alEvaluar: _evaluar,
                    alCheckin: _checkin,
                  );
                },
              ),
            ),
          ]),
        ),
      );
}

class _Contenido extends StatelessWidget {
  final Seguimiento datos;
  final VoidCallback alHoras;
  final VoidCallback alEvaluar;
  final Future<void> Function(bool) alCheckin;
  const _Contenido({required this.datos, required this.alHoras, required this.alEvaluar, required this.alCheckin});

  @override
  Widget build(BuildContext context) {
    final aceptada = datos.estadoVinculacion == 'aceptada';
    final i = datos.avisoSeguridad.indexOf(':');
    final negrita = i > 0 ? datos.avisoSeguridad.substring(0, i + 1) : '';
    final resto = i > 0 ? datos.avisoSeguridad.substring(i + 1) : datos.avisoSeguridad;
    return Column(children: [
      Expanded(
        child: ListView(padding: const EdgeInsets.fromLTRB(20, 8, 20, 12), children: [
          TarjetaHero(
            child: Row(children: [
              Avatar(datos.otraPersona, radio: 30),
              const SizedBox(width: 14),
              Expanded(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  const Text('Tu vinculación con', style: TextStyle(color: Colors.white70, fontSize: 13)),
                  Text(datos.otraPersona,
                      style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w800, color: Colors.white)),
                ]),
              ),
            ]),
          ),
          const SizedBox(height: 22),
          for (var i = 0; i < datos.pasos.length; i++) _Paso(datos.pasos[i], ultimo: i == datos.pasos.length - 1),
          const SizedBox(height: 4),
          if (datos.pasos.every((p) => p.estado == 'hecho')) ...[
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(gradient: degradadoMarca, borderRadius: BorderRadius.circular(18)),
              child: const Row(children: [
                Icon(Icons.celebration_rounded, color: Colors.white, size: 28),
                SizedBox(width: 12),
                Expanded(
                  child: Text('¡Proceso completo! Gracias por cuidar y reconocer el cuidado.',
                      style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, height: 1.35)),
                ),
              ]),
            ),
            const SizedBox(height: 14),
          ],
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(color: Colores.ambar, borderRadius: BorderRadius.circular(14)),
            child: Text.rich(
                TextSpan(children: [
                  TextSpan(text: negrita, style: const TextStyle(fontWeight: FontWeight.w700)),
                  TextSpan(text: resto),
                ]),
                style: const TextStyle(fontSize: 13, height: 1.45, color: Colores.tinta)),
          ),
          if (aceptada) ...[
            const SizedBox(height: 14),
            _Acceso(icono: Icons.schedule, texto: 'Horas y pago', alTocar: alHoras),
            const SizedBox(height: 10),
            _Acceso(icono: Icons.star_outline, texto: 'Evaluar esta experiencia', alTocar: alEvaluar),
          ],
        ]),
      ),
      if (aceptada)
        Padding(
          padding: const EdgeInsets.fromLTRB(20, 4, 20, 16),
          child: Row(children: [
            Expanded(child: OutlinedButton(onPressed: () => alCheckin(false), child: const Text('Reportar un problema'))),
            const SizedBox(width: 10),
            Expanded(child: BotonPrincipal(texto: 'Todo va bien', icono: Icons.thumb_up_rounded, alPresionar: () => alCheckin(true))),
          ]),
        ),
      const Padding(padding: EdgeInsets.only(bottom: 10), child: BotonVolverInicio()),
    ]);
  }
}

class _Paso extends StatelessWidget {
  final PasoSeguimiento p;
  final bool ultimo;
  const _Paso(this.p, {this.ultimo = false});

  @override
  Widget build(BuildContext context) {
    Widget marca;
    switch (p.estado) {
      case 'hecho':
        marca = Container(
          width: 28,
          height: 28,
          decoration: const BoxDecoration(gradient: degradadoMarca, shape: BoxShape.circle),
          child: const Icon(Icons.check_rounded, size: 17, color: Colors.white),
        );
      case 'actual':
        marca = Container(
          width: 28,
          height: 28,
          decoration: BoxDecoration(
              gradient: degradadoCoral,
              shape: BoxShape.circle,
              boxShadow: [BoxShadow(color: Colores.coral.withValues(alpha: 0.45), blurRadius: 12, spreadRadius: 2)]),
          child: const Icon(Icons.more_horiz_rounded, size: 18, color: Colors.white),
        );
      default:
        marca = Container(
          width: 28,
          height: 28,
          decoration: BoxDecoration(shape: BoxShape.circle, border: Border.all(color: const Color(0xFF9FB8B5), width: 2)),
        );
    }
    final actual = p.estado == 'actual';
    return IntrinsicHeight(
      child: Row(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        SizedBox(
          width: 28,
          child: Column(children: [
            marca,
            if (!ultimo)
              Expanded(
                child: Container(
                    width: 2,
                    margin: const EdgeInsets.symmetric(vertical: 4),
                    color: p.estado == 'hecho' ? Colores.verde : Colores.borde),
              ),
          ]),
        ),
        const SizedBox(width: 14),
        Expanded(
          child: Padding(
            padding: const EdgeInsets.only(bottom: 18),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(p.titulo,
                  style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w800,
                      color: p.estado == 'pendiente' ? Colores.apagado : Colores.tinta)),
              Text(actual ? '${p.detalle} · ahora' : p.detalle, style: estiloPequeno),
            ]),
          ),
        ),
      ]),
    );
  }
}

class _Acceso extends StatelessWidget {
  final IconData icono;
  final String texto;
  final VoidCallback alTocar;
  const _Acceso({required this.icono, required this.texto, required this.alTocar});

  @override
  Widget build(BuildContext context) => InkWell(
        borderRadius: BorderRadius.circular(14),
        onTap: alTocar,
        child: Container(
          padding: const EdgeInsets.all(14),
          decoration: decoracionTarjeta(),
          child: Row(children: [
            Container(
              width: 40,
              height: 40,
              decoration: const BoxDecoration(color: Colores.menta, shape: BoxShape.circle),
              child: Icon(icono, color: Colores.verde),
            ),
            const SizedBox(width: 12),
            Expanded(child: Text(texto, style: const TextStyle(fontWeight: FontWeight.w700))),
            const Icon(Icons.chevron_right, color: Colores.apagado),
          ]),
        ),
      );
}

/// Pantalla 5 del diseño: horas registradas y pago (simulado).
class PantallaHoras extends StatefulWidget {
  final ApiCliente api;
  final Vinculacion vinculacion;
  final bool esCuidadora;
  const PantallaHoras({super.key, required this.api, required this.vinculacion, required this.esCuidadora});

  @override
  State<PantallaHoras> createState() => _PantallaHorasState();
}

class _PantallaHorasState extends State<PantallaHoras> {
  late Future<HorasInfo> _futuro;

  @override
  void initState() {
    super.initState();
    _futuro = widget.api.horas(widget.vinculacion.id);
  }

  void _recargar() => setState(() {
        _futuro = widget.api.horas(widget.vinculacion.id);
      });

  Future<void> _agregar() async {
    var fecha = DateTime.now();
    var horas = 2;
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => StatefulBuilder(
        builder: (context, setLocal) => AlertDialog(
          title: const Text('Agregar horas'),
          content: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('Día', style: estiloPequeno),
            OutlinedButton(
              style: OutlinedButton.styleFrom(minimumSize: const Size.fromHeight(44)),
              onPressed: () async {
                final d = await showDatePicker(
                  context: context,
                  initialDate: fecha,
                  firstDate: DateTime.now().subtract(const Duration(days: 60)),
                  lastDate: DateTime.now().add(const Duration(days: 180)),
                );
                if (d != null) setLocal(() => fecha = d);
              },
              child: Text(_fechaCorta(fecha)),
            ),
            const SizedBox(height: 12),
            const Text('Horas trabajadas', style: estiloPequeno),
            DropdownButtonFormField<int>(
              initialValue: horas,
              items: [for (var h = 1; h <= 12; h++) DropdownMenuItem(value: h, child: Text('$h h'))],
              onChanged: (v) => setLocal(() => horas = v ?? horas),
            ),
          ]),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancelar')),
            FilledButton(
                style: FilledButton.styleFrom(minimumSize: const Size(100, 44)),
                onPressed: () => Navigator.pop(context, true),
                child: const Text('Guardar')),
          ],
        ),
      ),
    );
    if (ok != true) return;
    try {
      await widget.api.registrarHoras(widget.vinculacion.id, fecha, horas);
      if (mounted) _recargar();
    } catch (e) {
      if (mounted) mostrarMensaje(context, e.toString());
    }
  }

  Future<void> _confirmar() async {
    try {
      await widget.api.confirmarHoras(widget.vinculacion.id);
      if (!mounted) return;
      mostrarMensaje(context, 'Horas confirmadas. Pago simulado registrado.');
      _recargar();
    } catch (e) {
      if (mounted) mostrarMensaje(context, e.toString());
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        body: SafeArea(
          child: Column(children: [
            Encabezado(alVolver: () => Navigator.of(context).pop()),
            Expanded(
              child: FutureBuilder<HorasInfo>(
                future: _futuro,
                builder: (context, snap) {
                  if (snap.connectionState != ConnectionState.done) {
                    return const Center(child: CircularProgressIndicator());
                  }
                  if (snap.hasError) {
                    return Center(
                        child: Padding(
                            padding: const EdgeInsets.all(24),
                            child: Column(mainAxisSize: MainAxisSize.min, children: [
                              Text(snap.error.toString(), textAlign: TextAlign.center),
                              const SizedBox(height: 12),
                              OutlinedButton(onPressed: _recargar, child: const Text('Reintentar')),
                            ])));
                  }
                  return _tabla(snap.data!);
                },
              ),
            ),
          ]),
        ),
      );

  Widget _botonCuidadora(HorasInfo h) => Column(mainAxisSize: MainAxisSize.min, children: [
        BotonPrincipal(texto: 'Agregar horas', icono: Icons.add_rounded, alPresionar: _agregar),
        const SizedBox(height: 8),
        Text(
            'Puedes registrar horas de hoy o de días próximos. ${widget.vinculacion.otraPersona} las confirma '
            'cuando se realicen, y eso libera el pago (simulado).',
            textAlign: TextAlign.center,
            style: estiloPequeno),
      ]);

  Widget _botonContratante(HorasInfo h) {
    final hoy = DateTime.now();
    final puedeConfirmar = h.registros.any((r) => !r.confirmada && !r.fecha.isAfter(hoy));
    final soloProgramadas = h.estadoPago == 'por_confirmar' && !puedeConfirmar;
    return Column(mainAxisSize: MainAxisSize.min, children: [
      BotonPrincipal(
          texto: 'Confirmar semana',
          icono: Icons.check_rounded,
          alPresionar: puedeConfirmar ? _confirmar : null),
      const SizedBox(height: 8),
      Text(
          h.estadoPago == 'sin_horas'
              ? 'Aún no hay horas registradas. ${widget.vinculacion.otraPersona} las agregará.'
              : soloProgramadas
                  ? 'Las horas programadas se podrán confirmar a partir del día del servicio.'
                  : h.estadoPago == 'pagado_simulado'
                      ? 'Todo confirmado. Pago simulado registrado.'
                      : 'Confirma las horas que ya se realizaron.',
          textAlign: TextAlign.center,
          style: estiloPequeno),
    ]);
  }

  Widget _tabla(HorasInfo h) {
    final pagado = h.estadoPago == 'pagado_simulado';
    return Column(children: [
      Expanded(
        child: ListView(padding: const EdgeInsets.fromLTRB(20, 8, 20, 12), children: [
          TarjetaHero(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('Horas y pago con ${widget.vinculacion.otraPersona}',
                  style: const TextStyle(color: Colors.white70, fontSize: 14)),
              const SizedBox(height: 8),
              Text('\$${h.totalAPagar}',
                  style: const TextStyle(fontSize: 46, fontWeight: FontWeight.w800, color: Colors.white, height: 1)),
              const SizedBox(height: 6),
              Text('${h.totalHoras} h × \$${h.tarifaAcordada} por hora',
                  style: const TextStyle(color: Colors.white70, fontSize: 14)),
              const SizedBox(height: 12),
              Etiqueta(pagado ? 'Pago simulado confirmado' : 'Pago simulado · por confirmar',
                  fondo: Colors.white.withValues(alpha: 0.22), color: Colors.white, icono: Icons.verified_rounded),
            ]),
          ),
          const SizedBox(height: 18),
          Container(
            decoration: decoracionTarjeta(),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
            child: Column(children: [
              if (h.registros.isEmpty)
                const Padding(
                    padding: EdgeInsets.symmetric(vertical: 16),
                    child: Text('Todavía no hay horas registradas.', style: estiloPequeno)),
              for (final r in h.registros)
                _Fila(
                    r.fecha.isAfter(DateTime.now())
                        ? '${_fechaCorta(r.fecha)} · programado'
                        : (r.confirmada ? '${_fechaCorta(r.fecha)} · confirmado' : _fechaCorta(r.fecha)),
                    '${r.horas} h'),
              _Fila('Total de horas', '${h.totalHoras} h', fuerte: true),
              _Fila('Tarifa acordada por hora', '\$${h.tarifaAcordada}'),
              _Fila('Total a pagar', '\$${h.totalAPagar}', fuerte: true, ultima: true),
            ]),
          ),
          const SizedBox(height: 14),
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(color: Colores.menta, borderRadius: BorderRadius.circular(14)),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                const Expanded(child: Text('Quién paga', style: TextStyle(fontWeight: FontWeight.w700))),
                Etiqueta(pagado ? 'Confirmado' : 'Por confirmar',
                    fondo: pagado ? Colores.verde : Colores.ambar, color: pagado ? Colors.white : Colores.tinta),
              ]),
              const SizedBox(height: 4),
              Text(h.quienPaga, style: const TextStyle(fontSize: 14)),
            ]),
          ),
          const SizedBox(height: 12),
          Text(
              pagado
                  ? 'Las dos partes confirmaron. Pago simulado: en este prototipo no se mueve dinero real.'
                  : 'Las dos partes confirman las horas antes de que se libere el pago. '
                      'Pago simulado: en este prototipo no se mueve dinero real.',
              style: estiloPequeno),
        ]),
      ),
      Padding(
        padding: const EdgeInsets.fromLTRB(20, 4, 20, 16),
        child: widget.esCuidadora ? _botonCuidadora(h) : _botonContratante(h),
      ),
      const Padding(padding: EdgeInsets.only(bottom: 10), child: BotonVolverInicio()),
    ]);
  }
}

class _Fila extends StatelessWidget {
  final String izquierda;
  final String derecha;
  final bool fuerte;
  final bool ultima;
  const _Fila(this.izquierda, this.derecha, {this.fuerte = false, this.ultima = false});

  @override
  Widget build(BuildContext context) {
    final estilo = TextStyle(fontSize: 14, fontWeight: fuerte ? FontWeight.w700 : FontWeight.w400);
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 11),
      decoration: BoxDecoration(border: ultima ? null : const Border(bottom: BorderSide(color: Colores.borde))),
      child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
        Text(izquierda, style: estilo),
        Text(derecha, style: estilo),
      ]),
    );
  }
}
