from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401  (registra las tablas en Base)
from app.config import settings
from app.database import Base, engine
from app.routers import auth, seguimiento, servicios, solicitudes, vinculaciones


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.5.0",
    description="API de la plataforma de vinculación de cuidados (prototipo académico).",
    lifespan=lifespan,
)

# La app web (Flutter) vive en otro dominio, así que el navegador exige CORS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_lista,
    allow_credentials=False,  # usamos token Bearer, no cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(servicios.router)
app.include_router(solicitudes.router)
app.include_router(vinculaciones.router)
app.include_router(seguimiento.router)


@app.get("/health", tags=["sistema"])
def health() -> dict[str, str]:
    """Comprueba que el servicio está arriba."""
    return {"status": "ok", "app": settings.app_name}
