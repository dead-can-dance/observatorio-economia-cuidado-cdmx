# App Flutter (Pasos 5 y 6)

La app sigue el diseño de referencia de 5 pantallas (`docs/evidencias/CuidaRed_prototipo_pantallas.png`).

| # | Pantalla del diseño | Dónde está en el código |
|---|---|---|
| 1 | Inicio: "Cuidar también es trabajo" y elección de perfil | `lib/pantallas/inicio.dart` |
| 2 | Solicitud y presupuesto (tipo, cuándo, zona, precio por hora) | `FormularioSolicitud` en `lib/pantallas/familia.dart` |
| 3 | Coincidencias con deslizamiento y "Por qué coincide" | `PilaTarjetas` y `lib/tarjetas.dart` |
| 4 | Seguimiento (línea de tiempo, aviso de seguridad, check-in) | `lib/pantallas/seguimiento.dart` |
| 5 | Horas y pago (pago simulado) | `PantallaHoras` en `lib/pantallas/seguimiento.dart` |

## Perfiles
- **Necesito cuidado**: solicita, desliza perfiles, confirma horas. Es quien paga.
- **Puedo cuidar** y **aliado u organización**: publican servicios con su tarifa por hora, aceptan solicitudes y registran horas.

## Qué es real y qué es de ejemplo
- Real (guardado en la API): cuentas, servicios, solicitudes, decisiones, vinculaciones, horas, check-ins y evaluaciones.
- El pago es **simulado**: se calcula `horas × tarifa acordada` y se marca como "confirmado", sin mover dinero.
- La tarifa acordada es el punto medio entre el rango de la persona cuidadora y el presupuesto de quien contrata.
- No se muestran insignias de "identidad verificada" ni "referencias", ni distancia en km, porque el prototipo no tiene un proceso de verificación ni ubicación exacta (por privacidad solo se guarda la alcaldía). Quedan como trabajo futuro.
- El criterio "Accesibilidad" del diseño tampoco existe aún en los datos.

## Zona
Se elige la alcaldía y se guarda su clave INEGI (por ejemplo `09007` = Iztapalapa). El matching compara esas claves.

## Diseño responsivo
En teléfono ocupa toda la pantalla; en computadora se muestra como una columna centrada de 480 px.

## Plataformas
Android y web se prueban directamente. iOS comparte el mismo código; compilarlo requiere una Mac.

## Conexión con el backend
La dirección se define al compilar con `--dart-define=API_URL=...`. El backend permite el origen web mediante CORS (`CORS_ORIGINS`).
