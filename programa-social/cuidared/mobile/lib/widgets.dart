import 'package:flutter/material.dart';

import 'modelos.dart';
import 'tema.dart';

void mostrarMensaje(BuildContext context, String texto) {
  ScaffoldMessenger.of(context)
    ..hideCurrentSnackBar()
    ..showSnackBar(SnackBar(
      content: Text(texto),
      behavior: SnackBarBehavior.floating,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
    ));
}

IconData iconoTipo(String clave) {
  switch (clave) {
    case 'acompanamiento':
      return Icons.diversity_1;
    case 'apoyo_hogar':
      return Icons.home_rounded;
    case 'comidas':
      return Icons.restaurant_rounded;
    case 'traslados':
      return Icons.directions_car_rounded;
    case 'cuidado_nocturno':
      return Icons.nights_stay_rounded;
    default:
      return Icons.favorite;
  }
}

IconData iconoFranja(String franja) {
  switch (franja) {
    case 'Mañana':
      return Icons.wb_sunny_rounded;
    case 'Tarde':
      return Icons.wb_twilight_rounded;
    case 'Noche':
      return Icons.nights_stay_rounded;
    default:
      return Icons.weekend_rounded;
  }
}

/// Encabezado de las pantallas: marca a la izquierda, "Prototipo" y acciones a la derecha.
class Encabezado extends StatelessWidget {
  final VoidCallback? alSalir;
  final VoidCallback? alVolver;
  final bool claro;
  const Encabezado({super.key, this.alSalir, this.alVolver, this.claro = false});

  @override
  Widget build(BuildContext context) {
    final color = claro ? Colors.white : Colores.verde;
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 10, 8, 4),
      child: Row(children: [
        if (alVolver != null)
          IconButton(
              onPressed: alVolver,
              icon: Icon(Icons.arrow_back_rounded, color: color),
              tooltip: 'Volver',
              visualDensity: VisualDensity.compact),
        Container(
          width: 30,
          height: 30,
          decoration: BoxDecoration(
              gradient: claro ? null : degradadoMarca,
              color: claro ? Colors.white.withValues(alpha: 0.2) : null,
              shape: BoxShape.circle),
          child: const Icon(Icons.diversity_1, size: 17, color: Colors.white),
        ),
        const SizedBox(width: 8),
        Text('CuidaRed', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: color)),
        const Spacer(),
        Text('Prototipo', style: TextStyle(fontSize: 12, color: claro ? Colors.white70 : Colores.apagado)),
        if (alSalir != null)
          TextButton(
              onPressed: alSalir,
              style: TextButton.styleFrom(foregroundColor: color),
              child: const Text('Salir')),
      ]),
    );
  }
}

/// Tarjeta grande con degradado de marca para titulares y totales.
class TarjetaHero extends StatelessWidget {
  final Widget child;
  final Gradient gradiente;
  const TarjetaHero({super.key, required this.child, this.gradiente = degradadoMarca});

  @override
  Widget build(BuildContext context) => Container(
        width: double.infinity,
        clipBehavior: Clip.antiAlias,
        decoration: BoxDecoration(
          gradient: gradiente,
          borderRadius: BorderRadius.circular(28),
          boxShadow: [BoxShadow(color: Colores.verde.withValues(alpha: 0.3), blurRadius: 24, offset: const Offset(0, 12))],
        ),
        child: Stack(children: [
          Positioned(right: -30, top: -30, child: _Burbuja(120, 0.10)),
          Positioned(right: 40, bottom: -50, child: _Burbuja(100, 0.08)),
          Padding(padding: const EdgeInsets.all(20), child: child),
        ]),
      );
}

class _Burbuja extends StatelessWidget {
  final double tam;
  final double opacidad;
  const _Burbuja(this.tam, this.opacidad);

  @override
  Widget build(BuildContext context) => Container(
      width: tam, height: tam, decoration: BoxDecoration(color: Colors.white.withValues(alpha: opacidad), shape: BoxShape.circle));
}

/// Círculo con degradado y la inicial de la persona (no usamos fotos reales).
class Avatar extends StatelessWidget {
  final String nombre;
  final double radio;
  const Avatar(this.nombre, {super.key, this.radio = 24});

  @override
  Widget build(BuildContext context) {
    final inicial = nombre.trim().isEmpty ? '?' : nombre.trim()[0].toUpperCase();
    return Container(
      width: radio * 2,
      height: radio * 2,
      decoration: BoxDecoration(gradient: degradadoPara(nombre), shape: BoxShape.circle),
      alignment: Alignment.center,
      child: Text(inicial, style: TextStyle(fontSize: radio * 0.95, fontWeight: FontWeight.w800, color: Colors.white)),
    );
  }
}

/// Botón principal con degradado.
class BotonPrincipal extends StatelessWidget {
  final String texto;
  final VoidCallback? alPresionar;
  final IconData? icono;
  final Gradient gradiente;
  const BotonPrincipal(
      {super.key, required this.texto, required this.alPresionar, this.icono, this.gradiente = degradadoMarca});

  @override
  Widget build(BuildContext context) {
    final activo = alPresionar != null;
    return Opacity(
      opacity: activo ? 1 : 0.5,
      child: Container(
        height: 56,
        decoration: BoxDecoration(
          gradient: gradiente,
          borderRadius: BorderRadius.circular(28),
          boxShadow: activo
              ? [BoxShadow(color: Colores.verde.withValues(alpha: 0.35), blurRadius: 18, offset: const Offset(0, 8))]
              : null,
        ),
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            borderRadius: BorderRadius.circular(28),
            onTap: alPresionar,
            child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
              Text(texto, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: Colors.white)),
              if (icono != null) ...[const SizedBox(width: 8), Icon(icono, color: Colors.white, size: 20)],
            ]),
          ),
        ),
      ),
    );
  }
}

class Etiqueta extends StatelessWidget {
  final String texto;
  final Color fondo;
  final Color color;
  final IconData? icono;
  const Etiqueta(this.texto, {super.key, this.fondo = Colores.menta, this.color = Colores.verde, this.icono});

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
        decoration: BoxDecoration(color: fondo, borderRadius: BorderRadius.circular(20)),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          if (icono != null) ...[Icon(icono, size: 13, color: color), const SizedBox(width: 4)],
          Text(texto, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: color)),
        ]),
      );
}

class MensajeError extends StatelessWidget {
  final String? texto;
  const MensajeError(this.texto, {super.key});

  @override
  Widget build(BuildContext context) => texto == null
      ? const SizedBox.shrink()
      : Container(
          width: double.infinity,
          margin: const EdgeInsets.only(bottom: 12),
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(color: const Color(0xFFFDECEA), borderRadius: BorderRadius.circular(12)),
          child: Text(texto!, style: const TextStyle(color: Colores.error, fontSize: 14)),
        );
}

/// Barra de avance ("Paso 1 de 3 · Necesito cuidado").
class BarraPaso extends StatelessWidget {
  final String texto;
  final double avance;
  final bool claro;
  const BarraPaso({super.key, required this.texto, required this.avance, this.claro = false});

  @override
  Widget build(BuildContext context) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(texto, style: TextStyle(fontSize: 13, color: claro ? Colors.white70 : Colores.apagado)),
        const SizedBox(height: 8),
        ClipRRect(
          borderRadius: BorderRadius.circular(6),
          child: LinearProgressIndicator(
              value: avance,
              minHeight: 6,
              color: claro ? Colors.white : Colores.verde,
              backgroundColor: claro ? Colors.white24 : Colores.borde),
        ),
      ]);
}

/// Opción tipo "píldora": con degradado cuando está elegida.
class ChipOpcion extends StatelessWidget {
  final String texto;
  final bool seleccionado;
  final VoidCallback alTocar;
  final IconData? icono;
  const ChipOpcion({super.key, required this.texto, required this.seleccionado, required this.alTocar, this.icono});

  @override
  Widget build(BuildContext context) => Semantics(
        button: true,
        selected: seleccionado,
        child: InkWell(
          borderRadius: BorderRadius.circular(24),
          onTap: alTocar,
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 160),
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              gradient: seleccionado ? degradadoMarca : null,
              color: seleccionado ? null : Colors.white,
              borderRadius: BorderRadius.circular(24),
              border: Border.all(color: seleccionado ? Colors.transparent : Colores.borde),
              boxShadow: seleccionado
                  ? [BoxShadow(color: Colores.verde.withValues(alpha: 0.3), blurRadius: 10, offset: const Offset(0, 4))]
                  : null,
            ),
            child: Row(mainAxisSize: MainAxisSize.min, children: [
              if (icono != null) ...[
                Icon(icono, size: 17, color: seleccionado ? Colors.white : Colores.verde),
                const SizedBox(width: 6),
              ],
              Text(texto,
                  style: TextStyle(
                      fontSize: 14, fontWeight: FontWeight.w600, color: seleccionado ? Colors.white : Colores.tinta)),
            ]),
          ),
        ),
      );
}

class ChipsTipo extends StatelessWidget {
  final String seleccionado;
  final ValueChanged<String> alCambiar;
  const ChipsTipo({super.key, required this.seleccionado, required this.alCambiar});

  @override
  Widget build(BuildContext context) => Wrap(spacing: 8, runSpacing: 8, children: [
        for (final e in tiposCuidado.entries)
          ChipOpcion(
              texto: e.value,
              icono: iconoTipo(e.key),
              seleccionado: seleccionado == e.key,
              alTocar: () => alCambiar(e.key)),
      ]);
}

/// Franjas de horario (se pueden elegir varias).
class ChipsFranjas extends StatelessWidget {
  final Set<String> seleccionadas;
  final ValueChanged<Set<String>> alCambiar;
  const ChipsFranjas({super.key, required this.seleccionadas, required this.alCambiar});

  @override
  Widget build(BuildContext context) => Wrap(spacing: 8, runSpacing: 8, children: [
        for (final f in franjas)
          ChipOpcion(
            texto: f,
            icono: iconoFranja(f),
            seleccionado: seleccionadas.contains(f),
            alTocar: () {
              final nuevo = {...seleccionadas};
              nuevo.contains(f) ? nuevo.remove(f) : nuevo.add(f);
              alCambiar(nuevo);
            },
          ),
      ]);
}

class SeleccionZona extends StatelessWidget {
  final String? valor;
  final ValueChanged<String?> alCambiar;
  const SeleccionZona({super.key, required this.valor, required this.alCambiar});

  @override
  Widget build(BuildContext context) => DropdownButtonFormField<String>(
        initialValue: valor,
        isExpanded: true,
        decoration: const InputDecoration(
            hintText: 'Colonia o alcaldía', prefixIcon: Icon(Icons.place_rounded, color: Colores.verde)),
        items: [for (final e in alcaldias.entries) DropdownMenuItem(value: e.key, child: Text(e.value))],
        onChanged: alCambiar,
      );
}

/// Precio por hora: cifra grande, campos "Mínimo" y "Máximo" y una barra para ajustarlos.
class CamposPrecio extends StatefulWidget {
  final RangeValues inicial;
  final ValueChanged<RangeValues> alCambiar;
  const CamposPrecio({super.key, required this.inicial, required this.alCambiar});

  @override
  State<CamposPrecio> createState() => _CamposPrecioState();
}

class _CamposPrecioState extends State<CamposPrecio> {
  late RangeValues _v = widget.inicial;
  late final TextEditingController _min = TextEditingController(text: '${_v.start.round()}');
  late final TextEditingController _max = TextEditingController(text: '${_v.end.round()}');

  @override
  void dispose() {
    _min.dispose();
    _max.dispose();
    super.dispose();
  }

  void _desdeTexto() {
    final a = int.tryParse(_min.text);
    final b = int.tryParse(_max.text);
    if (a == null || b == null) return;
    _v = RangeValues(a.toDouble(), b.toDouble());
    widget.alCambiar(_v);
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final bajo = _v.start.clamp(0, 400).toDouble();
    final alto = _v.end.clamp(0, 400).toDouble();
    final valido = bajo <= alto;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: decoracionTarjeta(),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(crossAxisAlignment: CrossAxisAlignment.baseline, textBaseline: TextBaseline.alphabetic, children: [
          Text('\$${_v.start.round()} – \$${_v.end.round()}',
              style: const TextStyle(fontSize: 30, fontWeight: FontWeight.w800, color: Colores.verde)),
          const SizedBox(width: 8),
          const Text('por hora', style: estiloPequeno),
        ]),
        if (valido)
          SliderTheme(
            data: SliderTheme.of(context).copyWith(
              trackHeight: 6,
              activeTrackColor: Colores.verde,
              inactiveTrackColor: Colores.menta,
              thumbColor: Colores.verde,
              overlayColor: Colores.verde.withValues(alpha: 0.12),
            ),
            child: RangeSlider(
              values: RangeValues(bajo, alto),
              min: 0,
              max: 400,
              divisions: 40,
              onChanged: (r) {
                _v = r;
                _min.text = '${r.start.round()}';
                _max.text = '${r.end.round()}';
                widget.alCambiar(r);
                setState(() {});
              },
            ),
          ),
        Row(children: [
          Expanded(child: _campo('Mínimo', _min)),
          const Padding(padding: EdgeInsets.symmetric(horizontal: 10, vertical: 20), child: Text('–')),
          Expanded(child: _campo('Máximo', _max)),
        ]),
      ]),
    );
  }

  Widget _campo(String etiqueta, TextEditingController c) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(etiqueta, style: estiloPequeno),
        const SizedBox(height: 4),
        TextField(
          controller: c,
          keyboardType: TextInputType.number,
          onChanged: (_) => _desdeTexto(),
          decoration: const InputDecoration(prefixText: '\$ ', isDense: true),
        ),
      ]);
}

class EtiquetaCampo extends StatelessWidget {
  final String texto;
  const EtiquetaCampo(this.texto, {super.key});

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(top: 22, bottom: 10),
        child: Text(texto, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: Colores.tinta)),
      );
}

/// Aviso de "ir al inicio": las pantallas con pestañas lo escuchan y regresan a la primera pestaña.
final ValueNotifier<int> senalInicio = ValueNotifier<int>(0);

/// Regresa a la primera pestaña de la pantalla principal desde cualquier pantalla de detalle.
class BotonVolverInicio extends StatelessWidget {
  const BotonVolverInicio({super.key});

  @override
  Widget build(BuildContext context) => Center(
        child: TextButton.icon(
          onPressed: () {
            Navigator.of(context).popUntil((ruta) => ruta.isFirst);
            senalInicio.value++;
          },
          icon: const Icon(Icons.home_rounded, size: 20),
          label: const Text('Volver al inicio', style: TextStyle(fontWeight: FontWeight.w700)),
        ),
      );
}
