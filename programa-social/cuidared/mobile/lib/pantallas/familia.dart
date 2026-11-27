import 'package:flutter/material.dart';

import '../modelos.dart';
import '../sesion.dart';
import '../tarjetas.dart';
import '../tema.dart';
import '../widgets.dart';
import 'vinculaciones.dart';

class InicioFamilia extends StatefulWidget {
  final Sesion sesion;
  const InicioFamilia({super.key, required this.sesion});

  @override
  State<InicioFamilia> createState() => _InicioFamiliaState();
}

class _InicioFamiliaState extends State<InicioFamilia> {
  int _pestana = 0;

  void _alInicio() {
    if (mounted) setState(() => _pestana = 0);
  }

  @override
  void initState() {
    super.initState();
    senalInicio.addListener(_alInicio);
  }

  @override
  void dispose() {
    senalInicio.removeListener(_alInicio);
    super.dispose();
  }
  Solicitud? _solicitud;

  @override
  Widget build(BuildContext context) {
    final api = widget.sesion.api;
    final paginas = <Widget>[
      FormularioSolicitud(
        sesion: widget.sesion,
        alCrear: (s) => setState(() {
          _solicitud = s;
          _pestana = 1;
        }),
      ),
      _solicitud == null
          ? const Center(
              child: Padding(
                  padding: EdgeInsets.all(24),
                  child: Text('Primero cuéntanos qué necesitas para ver coincidencias.',
                      style: estiloPequeno, textAlign: TextAlign.center)))
          : PilaTarjetas(key: ValueKey(_solicitud!.id), sesion: widget.sesion, solicitud: _solicitud!),
      Column(children: [
        const Align(
            alignment: Alignment.centerLeft,
            child: Padding(padding: EdgeInsets.fromLTRB(20, 12, 20, 4), child: Text('Tus vinculaciones', style: estiloTitulo))),
        Expanded(child: ListaVinculaciones(key: const ValueKey('mias'), api: api, recibidas: false)),
      ]),
    ];
    return Scaffold(
      body: SafeArea(
        child: Column(children: [
          Encabezado(alSalir: widget.sesion.salir),
          Expanded(child: paginas[_pestana]),
        ]),
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _pestana,
        onDestinationSelected: (i) => setState(() => _pestana = i),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.edit_note_rounded), selectedIcon: Icon(Icons.edit_note_rounded, color: Colores.verde), label: 'Solicitar'),
          NavigationDestination(icon: Icon(Icons.style_rounded), selectedIcon: Icon(Icons.style_rounded, color: Colores.verde), label: 'Coincidencias'),
          NavigationDestination(icon: Icon(Icons.timeline_rounded), selectedIcon: Icon(Icons.timeline_rounded, color: Colores.verde), label: 'Seguimiento'),
        ],
      ),
    );
  }
}

/// Pantalla 2 del diseño: "Cuéntanos qué necesitas".
class FormularioSolicitud extends StatefulWidget {
  final Sesion sesion;
  final ValueChanged<Solicitud> alCrear;
  const FormularioSolicitud({super.key, required this.sesion, required this.alCrear});

  @override
  State<FormularioSolicitud> createState() => _FormularioSolicitudState();
}

class _FormularioSolicitudState extends State<FormularioSolicitud> {
  String _tipo = 'acompanamiento';
  Set<String> _franjas = {'Mañana'};
  late String? _zona = claveAlcaldia(widget.sesion.usuario?.ageb);
  RangeValues _rango = const RangeValues(90, 130);
  String? _error;
  bool _ocupado = false;

  Future<void> _crear() async {
    final min = _rango.start.round();
    final max = _rango.end.round();
    if (max < min) {
      setState(() => _error = 'El máximo no puede ser menor que el mínimo.');
      return;
    }
    setState(() {
      _error = null;
      _ocupado = true;
    });
    try {
      final horario = franjas.where(_franjas.contains).join(', ');
      final s = await widget.sesion.api
          .crearSolicitud(tipo: _tipo, min: min, max: max, horario: horario, ageb: _zona);
      widget.alCrear(s);
    } catch (e) {
      if (mounted) setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _ocupado = false);
    }
  }

  @override
  Widget build(BuildContext context) => ListView(padding: const EdgeInsets.fromLTRB(20, 12, 20, 28), children: [
        const TarjetaHero(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            BarraPaso(texto: 'Paso 1 de 3 · Necesito cuidado', avance: 1 / 3, claro: true),
            SizedBox(height: 18),
            Text('Cuéntanos qué necesitas',
                style: TextStyle(fontSize: 30, fontWeight: FontWeight.w800, color: Colors.white, height: 1.1)),
            SizedBox(height: 6),
            Text('Tú pagas por el cuidado: dinos cuánto puedes por hora.', style: TextStyle(fontSize: 14, color: Colors.white70)),
          ]),
        ),
        const EtiquetaCampo('Tipo de cuidado'),
        ChipsTipo(seleccionado: _tipo, alCambiar: (v) => setState(() => _tipo = v)),
        const EtiquetaCampo('Cuándo'),
        ChipsFranjas(seleccionadas: _franjas, alCambiar: (v) => setState(() => _franjas = v)),
        const EtiquetaCampo('Zona'),
        SeleccionZona(valor: _zona, alCambiar: (v) => setState(() => _zona = v)),
        const EtiquetaCampo('Presupuesto por hora'),
        CamposPrecio(inicial: _rango, alCambiar: (v) => _rango = v),
        const SizedBox(height: 10),
        const Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Icon(Icons.shield_rounded, size: 16, color: Colores.verde),
          SizedBox(width: 6),
          Expanded(
              child: Text('No pedimos diagnósticos ni documentos médicos. El pago lo hace quien contrata.',
                  style: estiloPequeno)),
        ]),
        const SizedBox(height: 20),
        MensajeError(_error),
        BotonPrincipal(
            texto: _ocupado ? 'Buscando…' : 'Ver coincidencias',
            icono: Icons.arrow_forward_rounded,
            alPresionar: _ocupado ? null : _crear),
      ]);
}

/// Pantalla 3 del diseño: coincidencias, con deslizamiento.
class PilaTarjetas extends StatefulWidget {
  final Sesion sesion;
  final Solicitud solicitud;
  const PilaTarjetas({super.key, required this.sesion, required this.solicitud});

  @override
  State<PilaTarjetas> createState() => _PilaTarjetasState();
}

class _PilaTarjetasState extends State<PilaTarjetas> {
  List<Coincidencia>? _pila;
  String? _error;
  bool _ocupado = false;
  final _clave = GlobalKey<TarjetaDeslizableState>();

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  Future<void> _cargar() async {
    setState(() {
      _error = null;
      _pila = null;
    });
    try {
      final r = await widget.sesion.api.coincidencias(widget.solicitud.id);
      if (mounted) setState(() => _pila = r);
    } catch (e) {
      if (mounted) setState(() => _error = e.toString());
    }
  }

  Future<void> _decidir(bool meInteresa) async {
    if (_ocupado || _pila == null || _pila!.isEmpty) return;
    final actual = _pila!.first;
    setState(() => _ocupado = true);
    try {
      await widget.sesion.api.decidir(widget.solicitud.id, actual.servicioId, meInteresa);
      if (!mounted) return;
      setState(() => _pila!.removeAt(0));
      if (meInteresa) {
        await showDialog<void>(context: context, builder: (_) => _DialogoInteres(nombre: actual.nombre));
      }
    } catch (e) {
      if (mounted) mostrarMensaje(context, e.toString());
    } finally {
      if (mounted) setState(() => _ocupado = false);
    }
  }

  String get _subtitulo {
    final s = widget.solicitud;
    final partes = [etiquetaTipo(s.tipoCuidado)];
    if (s.horario != null && s.horario!.isNotEmpty) partes.add(s.horario!.toLowerCase());
    partes.add('tu zona');
    return partes.join(' · ');
  }

  @override
  Widget build(BuildContext context) {
    if (_error != null) {
      return Center(
          child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                Text(_error!, textAlign: TextAlign.center),
                const SizedBox(height: 12),
                OutlinedButton(onPressed: _cargar, child: const Text('Reintentar')),
              ])));
    }
    if (_pila == null) return const Center(child: CircularProgressIndicator());
    if (_pila!.isEmpty) {
      return Center(
          child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                const Text('Ya viste todos los perfiles', style: estiloSeccion),
                const SizedBox(height: 6),
                const Text('Prueba con otro rango de precio, horario o tipo de cuidado.',
                    style: estiloPequeno, textAlign: TextAlign.center),
                const SizedBox(height: 12),
                OutlinedButton(onPressed: _cargar, child: const Text('Actualizar')),
              ])));
    }
    final n = _pila!.length;
    final actual = _pila!.first;
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 8),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(n == 1 ? '1 coincidencia' : '$n coincidencias', style: estiloTitulo),
        const SizedBox(height: 2),
        Text(_subtitulo, style: estiloPequeno),
        const SizedBox(height: 14),
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.only(bottom: 22),
            child: Stack(children: [
              if (n > 1)
                Positioned.fill(
                  child: Transform.translate(
                    offset: const Offset(0, 16),
                    child: Transform.scale(
                      scale: 0.93,
                      child: Container(
                        decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(28),
                            border: Border.all(color: Colores.borde)),
                      ),
                    ),
                  ),
                ),
              TarjetaDeslizable(
                key: _clave,
                alDecidir: _decidir,
                hijo: TarjetaPerfil(key: ValueKey(actual.servicioId), c: actual),
              ),
            ]),
          ),
        ),
        const SizedBox(height: 6),
        Row(mainAxisAlignment: MainAxisAlignment.center, children: [
          _BotonRedondo(
              icono: Icons.close_rounded,
              etiqueta: 'Pasar',
              tam: 62,
              colorIcono: Colores.coral,
              alPresionar: _ocupado ? null : () => _clave.currentState?.deslizar(false)),
          const SizedBox(width: 36),
          _BotonRedondo(
              icono: Icons.favorite_rounded,
              etiqueta: 'Me interesa',
              tam: 74,
              gradiente: degradadoMarca,
              colorIcono: Colors.white,
              alPresionar: _ocupado ? null : () => _clave.currentState?.deslizar(true)),
        ]),
        const SizedBox(height: 6),
        const Center(
          child: Text('Desliza o usa los botones. La otra persona también debe aceptar.',
              style: estiloPequeno, textAlign: TextAlign.center),
        ),
      ]),
    );
  }
}

class _BotonRedondo extends StatelessWidget {
  final IconData icono;
  final String etiqueta;
  final double tam;
  final Color colorIcono;
  final Gradient? gradiente;
  final VoidCallback? alPresionar;
  const _BotonRedondo(
      {required this.icono,
      required this.etiqueta,
      required this.tam,
      required this.colorIcono,
      required this.alPresionar,
      this.gradiente});

  @override
  Widget build(BuildContext context) => Column(mainAxisSize: MainAxisSize.min, children: [
        Opacity(
          opacity: alPresionar == null ? 0.5 : 1,
          child: Container(
            width: tam,
            height: tam,
            decoration: BoxDecoration(
              gradient: gradiente,
              color: gradiente == null ? Colors.white : null,
              shape: BoxShape.circle,
              boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: 0.16), blurRadius: 16, offset: const Offset(0, 8))],
            ),
            child: Material(
              color: Colors.transparent,
              shape: const CircleBorder(),
              child: InkWell(
                customBorder: const CircleBorder(),
                onTap: alPresionar,
                child: Icon(icono, size: tam * 0.46, color: colorIcono),
              ),
            ),
          ),
        ),
        const SizedBox(height: 4),
        Text(etiqueta, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: Colores.apagado)),
      ]);
}

class _DialogoInteres extends StatelessWidget {
  final String nombre;
  const _DialogoInteres({required this.nombre});

  @override
  Widget build(BuildContext context) => Dialog(
        backgroundColor: Colors.transparent,
        child: Container(
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(gradient: degradadoMarca, borderRadius: BorderRadius.circular(28)),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            Container(
              width: 76,
              height: 76,
              decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.2), shape: BoxShape.circle),
              child: const Icon(Icons.favorite_rounded, color: Colors.white, size: 40),
            ),
            const SizedBox(height: 16),
            const Text('¡Interés enviado!',
                style: TextStyle(fontSize: 26, fontWeight: FontWeight.w800, color: Colors.white)),
            const SizedBox(height: 8),
            Text('Le avisamos a $nombre. Cuando acepte, verás su contacto en la pestaña Seguimiento.',
                textAlign: TextAlign.center, style: const TextStyle(color: Colors.white70, fontSize: 15, height: 1.4)),
            const SizedBox(height: 20),
            FilledButton(
              style: FilledButton.styleFrom(backgroundColor: Colors.white, foregroundColor: Colores.verde),
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Seguir viendo perfiles'),
            ),
          ]),
        ),
      );
}
