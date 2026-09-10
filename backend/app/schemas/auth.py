import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class SignupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    # 72 bytes is bcrypt's hard limit; anything longer is silently truncated
    # by the algorithm, so it is rejected here instead.
    password: str = Field(min_length=8, max_length=72)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class EmailRequest(BaseModel):
    email: EmailStr


class UserRecord(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    email: str
    role: UserRole
    verified: bool
    created_at: datetime


class SignupResponse(BaseModel):
    user: UserRecord
    # False when the account still has to confirm its email before it can
    # log in. The frontend uses this to decide between dropping straight
    # into the app and showing "check your inbox".
    authenticated: bool
    message: str


class MessageResponse(BaseModel):
    message: str
