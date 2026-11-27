import 'package:cuidared_app/modelos.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('formatoRango muestra el rango por hora', () {
    expect(formatoRango(80, 150), r'$80–$150 por hora');
    expect(formatoRango(100, 100), r'$100 por hora');
  });

  test('Usuario.fromJson identifica a la cuidadora', () {
    final u = Usuario.fromJson({'id': 1, 'email': 'a@b.mx', 'nombre': 'Ana', 'perfil': 'puede_cuidar'});
    expect(u.esCuidadora, isTrue);
    final f = Usuario.fromJson({'id': 2, 'email': 'b@b.mx', 'nombre': 'Bea', 'perfil': 'necesita_cuidado'});
    expect(f.esCuidadora, isFalse);
  });

  test('claveAlcaldia reconoce las primeras 5 posiciones de la AGEB', () {
    expect(claveAlcaldia('0900700012345'), '09007');
    expect(claveAlcaldia('99999'), isNull);
    expect(claveAlcaldia(null), isNull);
  });

  test('HorasInfo.fromJson lee el pago simulado', () {
    final h = HorasInfo.fromJson({
      'registros': [
        {'id': 1, 'fecha': '2026-11-02', 'horas': 2, 'confirmada': false}
      ],
      'total_horas': 2,
      'tarifa_acordada': 110,
      'total_a_pagar': 220,
      'quien_paga': 'Quien contrata',
      'estado_pago': 'por_confirmar',
    });
    expect(h.totalAPagar, 220);
    expect(h.registros.single.fecha.day, 2);
  });

  test('Coincidencia.fromJson lee los criterios', () {
    final c = Coincidencia.fromJson({
      'servicio_id': 3,
      'nombre': 'María',
      'tipo_cuidado': 'comidas',
      'tarifa_min': 90,
      'tarifa_max': 120,
      'disponibilidad': null,
      'puntaje': 85,
      'zona_prioritaria': false,
      'criterios': [
        {'nombre': 'Zona', 'estado': 'ok'}
      ],
    });
    expect(c.criterios.single.nombre, 'Zona');
    expect(etiquetaTipo(c.tipoCuidado), 'Preparación de comidas');
  });
}
