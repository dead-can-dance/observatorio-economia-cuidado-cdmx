import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Paleta de CuidaRed. Para cambiar la identidad visual basta con editar estos valores.
class Colores {
  static const verde = Color(0xFF0F6F6A);
  static const verdeProfundo = Color(0xFF0A3F3D);
  static const turquesa = Color(0xFF2CC3AE);
  static const coral = Color(0xFFFF7A59);
  static const fondo = Color(0xFFF2F7F6);
  static const tinta = Color(0xFF10302E);
  static const apagado = Color(0xFF506967);
  static const borde = Color(0xFFD9E5E3);
  static const menta = Color(0xFFDDF3EE);
  static const ambar = Color(0xFFFFE3A3);
  static const error = Color(0xFFB3261E);
}

const degradadoMarca = LinearGradient(
  begin: Alignment.topLeft,
  end: Alignment.bottomRight,
  colors: [Colores.verdeProfundo, Colores.verde, Colores.turquesa],
);

const degradadoCoral = LinearGradient(
  begin: Alignment.topLeft,
  end: Alignment.bottomRight,
  colors: [Color(0xFFFF7A59), Color(0xFFFFB347)],
);

const _paletasRetrato = <List<Color>>[
  [Color(0xFF0F6F6A), Color(0xFF2CC3AE)],
  [Color(0xFFFF7A59), Color(0xFFFFB347)],
  [Color(0xFF5B5BD6), Color(0xFF9B8CF5)],
  [Color(0xFFE0507F), Color(0xFFFF9EC4)],
  [Color(0xFF1B7FB8), Color(0xFF6CCBEA)],
];

/// Un degradado distinto para cada persona (siempre el mismo para el mismo nombre).
LinearGradient degradadoPara(String nombre) {
  final i = nombre.codeUnits.fold<int>(0, (a, b) => a + b) % _paletasRetrato.length;
  return LinearGradient(begin: Alignment.topLeft, end: Alignment.bottomRight, colors: _paletasRetrato[i]);
}

const estiloTitulo = TextStyle(fontSize: 28, fontWeight: FontWeight.w800, color: Colores.tinta, height: 1.15);
const estiloSeccion = TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: Colores.tinta);
const estiloPequeno = TextStyle(fontSize: 13, color: Colores.apagado, height: 1.4);

BoxDecoration decoracionTarjeta({bool sombra = false}) => BoxDecoration(
      color: Colors.white,
      borderRadius: BorderRadius.circular(24),
      border: sombra ? null : Border.all(color: Colores.borde),
      boxShadow: [
        BoxShadow(
          color: Colores.verdeProfundo.withValues(alpha: sombra ? 0.16 : 0.05),
          blurRadius: sombra ? 28 : 12,
          offset: Offset(0, sombra ? 14 : 4),
        ),
      ],
    );

ThemeData crearTema() {
  final esquema = ColorScheme.fromSeed(seedColor: Colores.verde, primary: Colores.verde);
  OutlineInputBorder borde(Color c, [double ancho = 1]) =>
      OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: BorderSide(color: c, width: ancho));
  return ThemeData(
    useMaterial3: true,
    colorScheme: esquema,
    fontFamily: GoogleFonts.dmSans().fontFamily,
    scaffoldBackgroundColor: Colores.fondo,
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: Colors.white,
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      border: borde(Colores.borde),
      enabledBorder: borde(Colores.borde),
      focusedBorder: borde(Colores.verde, 2),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        minimumSize: const Size.fromHeight(54),
        backgroundColor: Colores.verde,
        shape: const StadiumBorder(),
        textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        minimumSize: const Size.fromHeight(54),
        foregroundColor: Colores.verde,
        side: const BorderSide(color: Colores.verde, width: 1.5),
        shape: const StadiumBorder(),
        textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
      ),
    ),
    navigationBarTheme: NavigationBarThemeData(
      height: 70,
      backgroundColor: Colors.white,
      indicatorColor: Colores.menta,
      indicatorShape: const StadiumBorder(),
      labelTextStyle: WidgetStateProperty.all(const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
    ),
  );
}
