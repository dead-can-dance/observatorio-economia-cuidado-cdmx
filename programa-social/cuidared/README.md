# CuidaRed (nombre provisional)

Plataforma móvil que conecta a personas que necesitan cuidado con personas cuidadoras de su misma zona
y que remunera el cuidado que hoy se hace sin pago. Proyecto integrador de 7.º semestre,
Licenciatura en Ciencias de Datos para Negocios (UNRC): Observatorio de datos + programa de innovación social.

- **App móvil:** Flutter (Android e iOS), en `mobile/`.
- **Backend:** Python + FastAPI + PostgreSQL, en `backend/`.
- **Documentación:** en `docs/`.

## Cómo probarlo

```bash
cp .env.example .env        # en Windows: copy .env.example .env
docker compose up --build
```
- Comprobación: http://localhost:8000/health
- Documentación interactiva de la API: http://localhost:8000/docs

Instrucciones detalladas: [docs/01-instalacion-windows.md](docs/01-instalacion-windows.md).
Alcance y reglas: [docs/00-alcance-mvp.md](docs/00-alcance-mvp.md).
Modelo de datos y endpoints: [docs/02-modelo-de-datos.md](docs/02-modelo-de-datos.md).
Matching, precio y deslizamiento: [docs/03-matching.md](docs/03-matching.md).

## Estado

| Paso | Contenido | Estado |
|---|---|---|
| 1 | Alcance y repositorio | Hecho |
| 2 | Backend base: datos y autenticación | Hecho |
| 3 | Backend de matching y deslizamiento | Hecho |
| 4 | Backend de seguimiento, horas y pago simulado | En pruebas |
| 5 | App Flutter base | En pruebas |
| 6 | App Flutter, flujos principales | En pruebas |
| 7 | Pruebas y privacidad | Pendiente |
| 8 | Documentación final | Pendiente |

## Equipo
[Nombres del equipo]

## Licencia
[Por definir]
