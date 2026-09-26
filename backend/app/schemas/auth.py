"""Request and response bodies for the auth endpoints."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import Role


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: str


class SignupIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str = Role.MANAGER


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ForgotPasswordIn(BaseModel):
    email: EmailStr


class ForgotPasswordOut(BaseModel):
    message: str
    # Dev only: the code is returned instead of emailed so the flow is demoable.
    otp: str | None = None


class VerifyOtpIn(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=4, max_length=10)


class VerifyOtpOut(BaseModel):
    reset_token: str


class ResetPasswordIn(BaseModel):
    reset_token: str
    new_password: str = Field(min_length=8, max_length=128)


class MessageOut(BaseModel):
    message: str
