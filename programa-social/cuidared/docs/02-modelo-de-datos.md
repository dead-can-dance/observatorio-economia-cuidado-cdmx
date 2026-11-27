# Modelo de datos (Paso 2)

```mermaid
erDiagram
    USUARIOS ||--o{ SERVICIOS : ofrece
    USUARIOS ||--o{ SOLICITUDES : publica
    SOLICITUDES ||--o{ DECISIONES : recibe
    SERVICIOS ||--o{ DECISIONES : recibe
    SOLICITUDES ||--o{ VINCULACIONES : origina
    SERVICIOS ||--o{ VINCULACIONES : origina

    USUARIOS {
        int id PK
        string email UK
        string password_hash
        string nombre
        enum perfil "necesita_cuidado | puede_cuidar | organizacion"
        string ageb "zona estadística, no dirección"
        bool acepto_aviso_privacidad
        datetime fecha_consentimiento
        datetime creado_en
    }
    SERVICIOS {
        int id PK
        int cuidadora_id FK
        enum tipo_cuidado
        int tarifa_min "MXN por hora"
        int tarifa_max "MXN por hora"
        string disponibilidad
    }
    SOLICITUDES {
        int id PK
        int solicitante_id FK
        enum tipo_cuidado
        string horario
        string ageb
        int presupuesto_min "MXN por hora"
        int presupuesto_max "MXN por hora"
        enum estado "abierta | cerrada | cancelada"
    }
    DECISIONES {
        int id PK
        int solicitud_id FK
        int servicio_id FK
        enum decision "me_interesa | pasar"
    }
    VINCULACIONES {
        int id PK
        int solicitud_id FK
        int servicio_id FK
        enum estado "pendiente | aceptada | rechazada"
        datetime respondida_en
    }
```

Las tablas de horas, pagos simulados, evaluaciones e incidentes se agregan en el Paso 4. Los endpoints de servicios, solicitudes y vinculaciones están en `03-matching.md`.

## Decisiones de diseño y privacidad

- **Zona por AGEB, no por dirección:** minimiza los datos personales y permite marcar zonas prioritarias.
- **Sin datos de salud ni diagnósticos:** solo el tipo de cuidado que se necesita u ofrece.
- **Consentimiento registrado:** se guarda si la persona aceptó el aviso de privacidad y la fecha.
- **Contraseñas:** nunca se guardan; se almacena un hash con scrypt y sal aleatoria.
- **Rangos de precio:** una restricción de base de datos impide que el máximo sea menor que el mínimo.
- **Género:** no se guarda ni se usa como criterio de elegibilidad.

## Endpoints disponibles

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/auth/registro` | Crea una cuenta (exige aceptar el aviso de privacidad). |
| POST | `/auth/login` | Devuelve un token de acceso. |
| GET | `/auth/yo` | Datos de la persona autenticada (requiere token). |
