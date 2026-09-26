"""One-time codes for password reset.

The code itself is never stored, only a bcrypt hash of it, and only the newest
unused code for a user counts. Requesting a new code invalidates the old one.
"""

import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.models.enums import OtpPurpose
from app.models.user import OtpToken, User

CODE_LENGTH = 6


def _generate_code() -> str:
    return f"{secrets.randbelow(10 ** CODE_LENGTH):0{CODE_LENGTH}d}"


def issue_otp(db: Session, user: User, purpose: str = OtpPurpose.PASSWORD_RESET) -> str:
    # Any code issued earlier is spent the moment a new one is requested.
    for token in db.scalars(
        select(OtpToken).where(
            OtpToken.user_id == user.id,
            OtpToken.purpose == purpose,
            OtpToken.used_at.is_(None),
        )
    ):
        token.used_at = datetime.now(UTC)

    code = _generate_code()
    db.add(
        OtpToken(
            user_id=user.id,
            code_hash=hash_password(code),
            purpose=purpose,
            expires_at=datetime.now(UTC) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
        )
    )
    db.commit()
    return code


def consume_otp(
    db: Session, user: User, code: str, purpose: str = OtpPurpose.PASSWORD_RESET
) -> bool:
    """Check the code and spend it. A code works exactly once."""
    token = db.scalar(
        select(OtpToken)
        .where(
            OtpToken.user_id == user.id,
            OtpToken.purpose == purpose,
            OtpToken.used_at.is_(None),
        )
        .order_by(OtpToken.id.desc())
    )
    if token is None:
        return False

    expires_at = token.expires_at
    if expires_at.tzinfo is None:
        # SQLite hands back naive datetimes; they are stored as UTC.
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at < datetime.now(UTC):
        return False

    if not verify_password(code, token.code_hash):
        return False

    token.used_at = datetime.now(UTC)
    db.commit()
    return True
