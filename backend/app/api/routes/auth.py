"""Signup, login, and OTP-based password reset."""

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_reset_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models.enums import Role
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordIn,
    ForgotPasswordOut,
    LoginIn,
    MessageOut,
    ResetPasswordIn,
    SignupIn,
    TokenOut,
    UserOut,
    VerifyOtpIn,
    VerifyOtpOut,
)
from app.services.otp import consume_otp, issue_otp

router = APIRouter(prefix="/auth", tags=["auth"])


def _find_user(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupIn, db: Session = Depends(get_db)) -> User:
    if _find_user(db, payload.email) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )
    if payload.role not in Role.ALL:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unknown role")

    user = User(
        name=payload.name.strip(),
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)) -> dict:
    user = _find_user(db, payload.email)
    # Same message either way: never reveal which half was wrong.
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password"
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account is disabled")

    return {"access_token": create_access_token(user.id), "user": user}


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.post("/forgot-password", response_model=ForgotPasswordOut)
def forgot_password(payload: ForgotPasswordIn, db: Session = Depends(get_db)) -> dict:
    user = _find_user(db, payload.email)
    message = "If that email is registered, a 6-digit code has been sent to it."

    # Answer identically for unknown emails so the endpoint cannot be used to
    # discover who has an account.
    if user is None:
        return {"message": message, "otp": None}

    code = issue_otp(db, user)
    if settings.DEV_SHOW_OTP:
        print(f"[dev] password reset code for {user.email}: {code}")
        return {"message": message, "otp": code}
    return {"message": message, "otp": None}


@router.post("/verify-otp", response_model=VerifyOtpOut)
def verify_otp(payload: VerifyOtpIn, db: Session = Depends(get_db)) -> dict:
    user = _find_user(db, payload.email)
    if user is None or not consume_otp(db, user, payload.otp):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="That code is invalid or has expired"
        )
    return {"reset_token": create_reset_token(user.id)}


@router.post("/reset-password", response_model=MessageOut)
def reset_password(payload: ResetPasswordIn, db: Session = Depends(get_db)) -> dict:
    try:
        claims = decode_token(payload.reset_token, expected_type="reset")
        user = db.get(User, int(claims["sub"]))
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset link has expired. Request a new code.",
        ) from None

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password updated. You can sign in now."}
