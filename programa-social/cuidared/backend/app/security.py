import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt

from app.config import settings

ALGORITMO = "HS256"
_N, _R, _P = 2**14, 8, 1


def hash_password(password: str) -> str:
    """Devuelve la contraseña protegida con scrypt y una sal aleatoria."""
    sal = os.urandom(16)
    derivada = hashlib.scrypt(password.encode(), salt=sal, n=_N, r=_R, p=_P)
    return "scrypt${}${}".format(base64.b64encode(sal).decode(), base64.b64encode(derivada).decode())


def verify_password(password: str, guardada: str) -> bool:
    """Comprueba una contraseña contra su versión protegida."""
    try:
        esquema, sal_b64, hash_b64 = guardada.split("$")
        if esquema != "scrypt":
            return False
        sal = base64.b64decode(sal_b64)
        esperada = base64.b64decode(hash_b64)
    except ValueError:
        return False
    derivada = hashlib.scrypt(password.encode(), salt=sal, n=_N, r=_R, p=_P)
    return hmac.compare_digest(derivada, esperada)


def create_access_token(usuario_id: int) -> str:
    vence = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode({"sub": str(usuario_id), "exp": vence}, settings.secret_key, algorithm=ALGORITMO)


def decode_access_token(token: str) -> int | None:
    """Devuelve el id de usuario del token, o None si no es válido o ya venció."""
    try:
        datos = jwt.decode(token, settings.secret_key, algorithms=[ALGORITMO])
        return int(datos["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None
