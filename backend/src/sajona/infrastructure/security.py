"""Implementaciones de hashing Argon2id y tokens JWT/opacos."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

from sajona.domain.entities import UserIdentity
from sajona.domain.exceptions import UnauthorizedError


class Argon2PasswordHasher:
    """Hashing seguro de contraseñas mediante Argon2id."""

    def __init__(self) -> None:
        self._hasher = PasswordHash.recommended()

    def hash(self, raw_password: str) -> str:
        return self._hasher.hash(raw_password)

    def verify(self, raw_password: str, password_hash: str) -> bool:
        try:
            return self._hasher.verify(raw_password, password_hash)
        except Exception:
            return False


class JwtTokenProvider:
    """Emisión y verificación de JWT HS256 y tokens opacos con SHA-256."""

    def __init__(self, secret_key: str, algorithm: str = "HS256", ttl_minutes: int = 15) -> None:
        self._secret = secret_key
        self._algorithm = algorithm
        self._ttl_minutes = ttl_minutes

    def create_access_token(self, identity: UserIdentity) -> str:
        now = datetime.now(UTC)
        payload: dict[str, Any] = {
            "sub": str(identity.id),
            "username": identity.username,
            "roles": [r.value for r in identity.roles],
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=self._ttl_minutes)).timestamp()),
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def decode_access_token(self, token: str) -> dict[str, Any]:
        try:
            decoded: dict[str, Any] = jwt.decode(
                token, self._secret, algorithms=[self._algorithm]
            )
            return decoded
        except jwt.PyJWTError as exc:
            raise UnauthorizedError("Token de acceso inválido o expirado.") from exc

    def generate_opaque_token(self) -> tuple[str, str]:
        raw = secrets.token_urlsafe(36)
        return raw, self.hash_token(raw)

    def hash_token(self, raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
