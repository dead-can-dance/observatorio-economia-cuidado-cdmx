import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import 'pantallas/cuidadora.dart';
import 'pantallas/familia.dart';
import 'pantallas/inicio.dart';
import 'sesion.dart';
import 'tema.dart';

void main() {
  runApp(const CuidaRedApp());
}

class CuidaRedApp extends StatefulWidget {
  const CuidaRedApp({super.key});

  @override
  State<CuidaRedApp> createState() => _CuidaRedAppState();
}

class _CuidaRedAppState extends State<CuidaRedApp> {
  final Sesion _sesion = Sesion();

  @override
  void initState() {
    super.initState();
    _sesion.iniciar();
  }

  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'CuidaRed',
        debugShowCheckedModeBanner: false,
        theme: crearTema(),
        locale: const Locale('es', 'MX'),
        supportedLocales: const [Locale('es', 'MX'), Locale('es')],
        localizationsDelegates: const [
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        // En pantallas anchas (computadora) la app se muestra como una columna centrada de 480 px.
        builder: (context, child) => ColoredBox(
          color: Colores.fondo,
          child: Center(
            child: ConstrainedBox(constraints: const BoxConstraints(maxWidth: 480), child: child),
          ),
        ),
        home: ListenableBuilder(
          listenable: _sesion,
          builder: (context, _) {
            if (_sesion.cargando) {
              return const Scaffold(body: Center(child: CircularProgressIndicator()));
            }
            final u = _sesion.usuario;
            if (u == null) return PantallaInicio(sesion: _sesion);
            return u.esCuidadora ? InicioCuidadora(sesion: _sesion) : InicioFamilia(sesion: _sesion);
          },
        ),
      );
}
