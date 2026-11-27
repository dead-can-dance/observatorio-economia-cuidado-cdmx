/// Dirección de la API. Se cambia al compilar:
///   flutter run -d chrome --dart-define=API_URL=https://mi-api.onrender.com
class ApiConfig {
  static const String baseUrl =
      String.fromEnvironment('API_URL', defaultValue: 'http://localhost:8000');
}
