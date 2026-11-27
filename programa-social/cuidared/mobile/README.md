# CuidaRed — app Flutter

App para Android, iOS y web (computadora y teléfono). Se conecta a la API de `backend/`.

## Primera vez
```
flutter pub add http shared_preferences google_fonts intl
flutter pub add flutter_localizations --sdk=flutter
flutter pub get
```

## Probar en el navegador
1. Con el backend corriendo (`docker compose up --build` en la raíz del repo):
2. En esta carpeta: `flutter run -d chrome`
3. Otra API: `flutter run -d chrome --dart-define=API_URL=https://tu-api.onrender.com`

## Versión web publicable
`flutter build web --release --dart-define=API_URL=https://tu-api.onrender.com` (queda en `build/web/`).

## Pruebas
`flutter analyze` y `flutter test`

## Estructura
- `lib/api.dart`: llamadas a la API y token
- `lib/modelos.dart`: modelos de datos
- `lib/pantallas/`: inicio, acceso, familia, cuidadora, vinculaciones, seguimiento y horas
- `lib/tarjetas.dart`: tarjeta de perfil y gesto de deslizar
