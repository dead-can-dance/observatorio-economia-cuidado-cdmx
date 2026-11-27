# Seguimiento, horas y pago simulado (Paso 4)

Endpoints nuevos (todos bajo `/vinculaciones/{id}`; solo participan las dos personas de la vinculación):

| Método y ruta | Quién | Qué hace |
|---|---|---|
| `GET /seguimiento` | ambas | Línea de tiempo: solicitud, respuesta, primer encuentro, horas y pago, check-in, evaluación |
| `POST /checkin` | ambas | "Todo va bien" o "Reportar un problema" (con nota) |
| `POST /evaluacion` | ambas | Valoración de 1 a 5, una sola vez por persona |
| `GET /horas` | ambas | Horas registradas, tarifa acordada, total y estado del pago |
| `POST /horas` | cuidadora | Registra horas (1 a 24 por día) |
| `POST /horas/confirmar` | quien contrata | Confirma las horas pendientes; el pago simulado queda "confirmado" |

Reglas (en `backend/app/seguimiento.py`, sin base de datos y con pruebas):
- Solo se registran horas, check-ins y evaluaciones cuando la vinculación está **aceptada**.
- `tarifa acordada` = punto medio del traslape entre presupuesto y tarifa.
- Estado del pago: `sin_horas`, `por_confirmar` o `pagado_simulado`.
- Tablas nuevas: `horas_trabajo`, `seguimientos`, `evaluaciones`.
- El criterio "Horario" de las coincidencias es informativo: no cambia el puntaje.
