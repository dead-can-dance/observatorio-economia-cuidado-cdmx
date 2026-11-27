from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Perfil, Usuario
from app.security import decode_access_token

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credenciales: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    """Exige un token válido y entrega a la persona usuaria autenticada."""
    if credenciales is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No autenticado")
    usuario_id = decode_access_token(credenciales.credentials)
    usuario = db.get(Usuario, usuario_id) if usuario_id is not None else None
    if usuario is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido o vencido")
    return usuario


def requiere_perfil(*perfiles: Perfil):
    """Permite el paso solo a ciertos perfiles (por ejemplo, solo a quien puede cuidar)."""

    def _dependencia(usuario: Usuario = Depends(get_current_user)) -> Usuario:
        if usuario.perfil not in perfiles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Tu perfil no permite esta acción")
        return usuario

    return _dependencia
