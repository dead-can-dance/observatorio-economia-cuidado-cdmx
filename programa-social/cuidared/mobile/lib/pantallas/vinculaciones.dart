import 'package:flutter/material.dart';

import '../api.dart';
import '../modelos.dart';
import '../tema.dart';
import '../widgets.dart';
import 'seguimiento.dart';

/// Lista de vinculaciones. Si [recibidas] es true (cuidadora), puede aceptar o rechazar.
class ListaVinculaciones extends StatefulWidget {
  final ApiCliente api;
  final bool recibidas;
  const ListaVinculaciones({super.key, required this.api, required this.recibidas});

  @override
  State<ListaVinculaciones> createState() => _ListaVinculacionesState();
}

class _ListaVinculacionesState extends State<ListaVinculaciones> {
  late Future<List<Vinculacion>> _futuro;

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  void _cargar() {
    _futuro = widget.recibidas ? widget.api.recibidas() : widget.api.mias();
  }

  Future<void> _responder(Vinculacion v, bool aceptar) async {
    try {
      await widget.api.responder(v.id, aceptar);
      if (!mounted) return;
      setState(_cargar);
      mostrarMensaje(context, aceptar ? 'Aceptaste la vinculación.' : 'Rechazaste la vinculación.');
    } catch (e) {
      if (mounted) mostrarMensaje(context, e.toString());
    }
  }

  @override
  Widget build(BuildContext context) => FutureBuilder<List<Vinculacion>>(
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
                      OutlinedButton(onPressed: () => setState(_cargar), child: const Text('Reintentar')),
                    ])));
          }
          final lista = snap.data!;
          if (lista.isEmpty) {
            return const Center(
                child: Padding(
                    padding: EdgeInsets.all(24),
                    child: Text('Aún no tienes vinculaciones. Cuando alguien acepte, aparecerá aquí.', style: estiloPequeno, textAlign: TextAlign.center)));
          }
          return RefreshIndicator(
            onRefresh: () async => setState(_cargar),
            child: ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: lista.length,
              separatorBuilder: (_, _) => const SizedBox(height: 12),
              itemBuilder: (_, i) => _Fila(
                v: lista[i],
                puedeResponder: widget.recibidas,
                alResponder: _responder,
                alAbrir: () => Navigator.of(context).push(MaterialPageRoute<void>(
                    builder: (_) => PantallaSeguimiento(api: widget.api, vinculacion: lista[i], esCuidadora: widget.recibidas))),
              ),
            ),
          );
        },
      );
}

class _Fila extends StatelessWidget {
  final Vinculacion v;
  final bool puedeResponder;
  final Future<void> Function(Vinculacion, bool) alResponder;
  final VoidCallback alAbrir;
  const _Fila({required this.v, required this.puedeResponder, required this.alResponder, required this.alAbrir});

  @override
  Widget build(BuildContext context) {
    final aceptada = v.estado == 'aceptada';
    final pendiente = v.estado == 'pendiente';
    return Container(
      decoration: decoracionTarjeta(),
      padding: const EdgeInsets.all(16),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Avatar(v.otraPersona, radio: 22),
          const SizedBox(width: 12),
          Expanded(child: Text(v.otraPersona, style: estiloSeccion)),
          Etiqueta(v.estado,
              fondo: aceptada ? Colores.verde : (v.estado == 'rechazada' ? const Color(0xFFFDECEA) : Colores.ambar),
              color: aceptada ? Colors.white : (v.estado == 'rechazada' ? Colores.error : Colores.tinta)),
        ]),
        const SizedBox(height: 10),
        Row(children: [
          Icon(iconoTipo(v.tipoCuidado), size: 18, color: Colores.verde),
          const SizedBox(width: 6),
          Text(etiquetaTipo(v.tipoCuidado), style: const TextStyle(fontWeight: FontWeight.w700)),
        ]),
        Text('Tarifa: ${formatoRango(v.tarifaMin, v.tarifaMax)}', style: estiloPequeno),
        Text('Presupuesto: ${formatoRango(v.presupuestoMin, v.presupuestoMax)}', style: estiloPequeno),
        if (v.horario != null) Text('Horario: ${v.horario}', style: estiloPequeno),
        if (aceptada && v.contacto != null) ...[
          const SizedBox(height: 10),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(color: Colores.menta, borderRadius: BorderRadius.circular(12)),
            child: SelectableText('Contacto: ${v.contacto}'),
          ),
        ],
        if (aceptada) ...[
          const SizedBox(height: 12),
          OutlinedButton(onPressed: alAbrir, child: const Text('Ver seguimiento')),
        ],
        if (puedeResponder && pendiente) ...[
          const SizedBox(height: 12),
          Row(children: [
            Expanded(child: OutlinedButton(onPressed: () => alResponder(v, false), child: const Text('Rechazar'))),
            const SizedBox(width: 10),
            Expanded(child: FilledButton(onPressed: () => alResponder(v, true), child: const Text('Aceptar'))),
          ]),
        ],
      ]),
    );
  }
}
