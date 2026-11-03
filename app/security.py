from datetime import datetime, timedelta, timezone
from hashlib import sha256
from uuid import uuid4

import jwt
from pwdlib import PasswordHash

from app.config import settings
from app.exceptions import UnauthorizedError

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str: return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool: return password_hash.verify(password, hashed)


def hash_jti(jti: str) -> str: return sha256(jti.encode()).hexdigest()


def create_token(user_id: int, role: str, token_type: str, expires_delta: timedelta) -> tuple[str, str, datetime]:
    now = datetime.now(timezone.utc); expires_at = now + expires_delta; jti = str(uuid4())
    payload = {"sub": str(user_id), "role": role, "type": token_type, "jti": jti, "iat": now, "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm), jti, expires_at


def decode_token(token: str, expected_type: str) -> dict:
    try: payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc: raise UnauthorizedError("El token es inválido o venció") from exc
    if payload.get("type") != expected_type or not payload.get("sub") or not payload.get("jti"):
        raise UnauthorizedError("El tipo de token no es válido")
    return payload
