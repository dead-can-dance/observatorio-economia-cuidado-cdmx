import 'package:flutter/material.dart';

import '../modelos.dart';
import '../sesion.dart';
import '../tema.dart';
import '../widgets.dart';
import 'vinculaciones.dart';

class InicioCuidadora extends StatefulWidget {
  final Sesion sesion;
  const InicioCuidadora({super.key, required this.sesion});

  @override
  State<InicioCuidadora> createState() => _InicioCuidadoraState();
}

class _InicioCuidadoraState extends State<InicioCuidadora> {
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

  @override
  Widget build(BuildContext context) {
    final api = widget.sesion.api;
    final paginas = [
      MisServicios(sesion: widget.sesion),
      Column(children: [
        const Align(
            alignment: Alignment.centerLeft,
            child: Padding(padding: EdgeInsets.fromLTRB(20, 12, 20, 0), child: Text('Solicitudes y seguimiento', style: estiloTitulo))),
        Expanded(child: ListaVinculaciones(key: const ValueKey('rec'), api: api, recibidas: true)),
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
          NavigationDestination(icon: Icon(Icons.work_rounded), selectedIcon: Icon(Icons.work_rounded, color: Colores.verde), label: 'Mis servicios'),
          NavigationDestination(icon: Icon(Icons.favorite_rounded), selectedIcon: Icon(Icons.favorite_rounded, color: Colores.verde), label: 'Solicitudes'),
        ],
      ),
    );
  }
}

class MisServicios extends StatefulWidget {
  final Sesion sesion;
  const MisServicios({super.key, required this.sesion});

  @override
  State<MisServicios> createState() => _MisServiciosState();
}

class _MisServiciosState extends State<MisServicios> {
  late Future<List<Servicio>> _futuro;
  String _tipo = 'acompanamiento';
  Set<String> _franjas = {'Mañana'};
  RangeValues _rango = const RangeValues(90, 130);
  String? _error;
  bool _ocupado = false;

  @override
  void initState() {
    super.initState();
    _futuro = widget.sesion.api.misServicios();
  }

  Future<void> _publicar() async {
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
      await widget.sesion.api.crearServicio(
          tipo: _tipo, min: min, max: max, disponibilidad: franjas.where(_franjas.contains).join(', '));
      if (!mounted) return;
      setState(() {
        _futuro = widget.sesion.api.misServicios();
      });
      mostrarMensaje(context, 'Servicio publicado.');
    } catch (e) {
      if (mounted) setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _ocupado = false);
    }
  }

  @override
  Widget build(BuildContext context) => ListView(padding: const EdgeInsets.fromLTRB(20, 12, 20, 24), children: [
        TarjetaHero(
          child: Row(children: [
            Avatar(widget.sesion.usuario?.nombre ?? '', radio: 30),
            const SizedBox(width: 14),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('Hola, ${widget.sesion.usuario?.nombre ?? ''}',
                    style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w800, color: Colors.white)),
                const SizedBox(height: 4),
                const Text('Tu trabajo de cuidado se reconoce y se paga. Publica lo que ofreces.',
                    style: TextStyle(fontSize: 14, color: Colors.white70, height: 1.35)),
              ]),
            ),
          ]),
        ),
        const EtiquetaCampo('Tipo de cuidado'),
        ChipsTipo(seleccionado: _tipo, alCambiar: (v) => setState(() => _tipo = v)),
        const EtiquetaCampo('Cuándo estás disponible'),
        ChipsFranjas(seleccionadas: _franjas, alCambiar: (v) => setState(() => _franjas = v)),
        const EtiquetaCampo('Tarifa por hora'),
        CamposPrecio(inicial: _rango, alCambiar: (v) => _rango = v),
        const SizedBox(height: 14),
        MensajeError(_error),
        BotonPrincipal(texto: 'Publicar servicio', icono: Icons.check_rounded, alPresionar: _ocupado ? null : _publicar),
        const SizedBox(height: 24),
        const Text('Mis servicios publicados', style: estiloSeccion),
        const SizedBox(height: 8),
        FutureBuilder<List<Servicio>>(
          future: _futuro,
          builder: (context, snap) {
            if (snap.connectionState != ConnectionState.done) {
              return const Padding(padding: EdgeInsets.all(16), child: Center(child: CircularProgressIndicator()));
            }
            if (snap.hasError) return Text(snap.error.toString());
            final lista = snap.data!;
            if (lista.isEmpty) return const Text('Todavía no publicas ningún servicio.', style: estiloPequeno);
            return Column(children: [
              for (final s in lista)
                Container(
                  margin: const EdgeInsets.only(bottom: 10),
                  decoration: decoracionTarjeta(),
                  padding: const EdgeInsets.all(14),
                  width: double.infinity,
                  child: Row(children: [
                    Container(
                      width: 44,
                      height: 44,
                      decoration: const BoxDecoration(color: Colores.menta, shape: BoxShape.circle),
                      child: Icon(iconoTipo(s.tipoCuidado), color: Colores.verde),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Text(etiquetaTipo(s.tipoCuidado), style: const TextStyle(fontWeight: FontWeight.w700)),
                        Text(formatoRango(s.tarifaMin, s.tarifaMax),
                            style: const TextStyle(color: Colores.verde, fontWeight: FontWeight.w800)),
                        if (s.disponibilidad != null && s.disponibilidad!.isNotEmpty)
                          Text(s.disponibilidad!, style: estiloPequeno),
                      ]),
                    ),
                  ]),
                ),
            ]);
          },
        ),
      ]);
}
