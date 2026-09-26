"""Password hashing and JWT access tokens."""

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        # Malformed hash in the database: treat as a failed login, never a 500.
        return False


def create_token(subject: str | int, expires_in: timedelta, **claims: Any) -> str:
    payload: dict[str, Any] = {
        "sub": str(subject),
        "exp": datetime.now(UTC) + expires_in,
        "iat": datetime.now(UTC),
        **claims,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(user_id: int) -> str:
    return create_token(
        user_id,
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        type="access",
    )


def create_reset_token(user_id: int) -> str:
    """Short-lived proof that the user entered the right OTP."""
    return create_token(user_id, timedelta(minutes=settings.OTP_EXPIRE_MINUTES), type="reset")


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    """Raise jwt.InvalidTokenError if the token is expired, forged or of the wrong kind."""
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError("Unexpected token type")
    return payload
