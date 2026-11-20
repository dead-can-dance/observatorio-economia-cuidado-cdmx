# Alcance del MVP

Plataforma que conecta a personas que necesitan cuidado con personas cuidadoras de su misma zona,
y que **remunera el cuidado que hoy se hace sin pago**. El pago lo hace la persona que contrata el servicio.

## Historias de usuario

| Id | Historia |
|---|---|
| HU-01 | Como persona usuaria me registro y elijo mi perfil: "Necesito cuidado" o "Puedo cuidar". |
| HU-02 | Como persona cuidadora defino mis servicios, mi **rango de tarifa por hora**, mi disponibilidad y mi zona. |
| HU-03 | Como persona que contrata creo una solicitud con tipo de cuidado, horario, zona y **presupuesto por hora (mínimo y máximo)**. |
| HU-04 | Como persona que contrata veo una pila de tarjetas y **deslizo**: derecha "Me interesa", izquierda "Pasar". Cada tarjeta muestra compatibilidad y rango de precio. |
| HU-05 | Como persona cuidadora recibo solicitudes y las acepto o rechazo. El contacto se abre solo con aceptación de ambas partes. |
| HU-06 | Registramos las horas trabajadas y ambas partes las confirman. |
| HU-07 | La persona que contrata realiza el pago (simulado en el prototipo). |
| HU-08 | Ambas partes se evalúan y pueden reportar incidentes. |
| HU-09 | Al registrarme acepto un aviso de privacidad y doy mi consentimiento para los tratamientos no esenciales. |

## Reglas del sistema

- **Precio:** una tarjeta solo se muestra si el rango de la persona cuidadora se traslapa con el presupuesto de quien contrata.
- **Zona:** se maneja por AGEB (zona estadística), nunca por dirección exacta. Las AGEB sin servicios cercanos se marcan como prioritarias.
- **Datos mínimos:** no se piden diagnósticos ni documentos médicos.
- **Género:** no es criterio de elegibilidad. Se usa solo como indicador agregado de seguimiento.

## Fuera de alcance (por ahora)

Pagos reales, chat en tiempo real, verificación oficial de identidad (se simula) y notificaciones push.
