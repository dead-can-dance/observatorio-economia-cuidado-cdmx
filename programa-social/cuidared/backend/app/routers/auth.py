from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Usuario
from app.schemas import LoginEntrada, Token, UsuarioCrear, UsuarioPublico
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["autenticación"])


@router.post("/registro", response_model=UsuarioPublico, status_code=status.HTTP_201_CREATED)
def registro(datos: UsuarioCrear, db: Session = Depends(get_db)):
    """Crea una cuenta. Exige aceptar el aviso de privacidad."""
    if not datos.acepto_aviso_privacidad:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Debes aceptar el aviso de privacidad para registrarte")
    correo = datos.email.lower()
    if db.scalar(select(Usuario).where(Usuario.email == correo)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe una cuenta con ese correo")
    usuario = Usuario(
        email=correo,
        password_hash=hash_password(datos.password),
        nombre=datos.nombre,
        perfil=datos.perfil,
        ageb=datos.ageb,
        acepto_aviso_privacidad=True,
        fecha_consentimiento=datetime.now(timezone.utc),
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.post("/login", response_model=Token)
def login(datos: LoginEntrada, db: Session = Depends(get_db)):
    """Entrega un token de acceso si el correo y la contraseña son correctos."""
    usuario = db.scalar(select(Usuario).where(Usuario.email == datos.email.lower()))
    if usuario is None or not verify_password(datos.password, usuario.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Correo o contraseña incorrectos")
    return Token(access_token=create_access_token(usuario.id))


@router.get("/yo", response_model=UsuarioPublico)
def yo(usuario: Usuario = Depends(get_current_user)):
    """Devuelve los datos de la persona autenticada."""
    return usuario
